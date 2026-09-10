"""Authenticated real-observation workspace and append-only reviewed annotations."""
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.auth import get_current_user, require_role
from app.database import get_db
from app.event_models import ThermalEvent, EventPrediction, EventAnnotation, ThermalObservation, ReferenceFacility
from app.models import User
from app.ml.labels import Annotation, CLASSES
from app.services.event_intelligence import model_status,predict_event

router=APIRouter(prefix='/api/v1/thermal-events',tags=['Reviewed thermal events'],dependencies=[Depends(get_current_user)])


def event_or_404(event_id,db):
    event=db.get(ThermalEvent,event_id)
    if event is None: raise HTTPException(404,'Event not found')
    return event


def serialize(event,db,prediction=None,*,lookup=True):
    if lookup: prediction=db.scalar(select(EventPrediction).where(EventPrediction.event_id==event.event_id).order_by(EventPrediction.id.desc()).limit(1))
    return {'event_id':event.event_id,'latitude':event.latitude,'longitude':event.longitude,
        'start_time':event.start_time.replace(tzinfo=event.start_time.tzinfo or timezone.utc).isoformat(),'end_time':event.end_time.replace(tzinfo=event.end_time.tzinfo or timezone.utc).isoformat(),
        'facility_id':event.facility_id,'features':event.features,'provenance':event.provenance,
        'intelligence':prediction.intelligence if prediction else None}


def serialize_many(items,db):
    if not items: return []
    latest=select(func.max(EventPrediction.id)).where(EventPrediction.event_id.in_([e.event_id for e in items])).group_by(EventPrediction.event_id)
    predictions={p.event_id:p for p in db.scalars(select(EventPrediction).where(EventPrediction.id.in_(latest))).all()}
    return [serialize(e,db,predictions.get(e.event_id),lookup=False) for e in items]


@router.get('/status')
def status(db:Session=Depends(get_db)):
    return {'event_count':db.scalar(select(func.count()).select_from(ThermalEvent)),
        **model_status(),'classes':CLASSES}



@router.get('')
def list_events(facility_id:str|None=None, date_from:datetime|None=None, date_to:datetime|None=None,
                limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),db:Session=Depends(get_db)):
    if any(t is not None and t.tzinfo is None for t in (date_from,date_to)):
        raise HTTPException(422,'Date filters require timezone-aware timestamps')
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422,'date_from must not follow date_to')
    statement=select(ThermalEvent)
    if facility_id: statement=statement.where(ThermalEvent.facility_id==facility_id)
    if date_from: statement=statement.where(ThermalEvent.start_time>=date_from)
    if date_to: statement=statement.where(ThermalEvent.start_time<=date_to)
    total=db.scalar(select(func.count()).select_from(statement.subquery()))
    items=db.scalars(statement.order_by(ThermalEvent.start_time,ThermalEvent.event_id).offset(offset).limit(limit)).all()
    return {'items':serialize_many(items,db),'total':total,'limit':limit,'offset':offset}


@router.get('/annotations/export')
def export_annotations(db:Session=Depends(get_db)):
    latest=select(EventAnnotation.event_id,func.max(EventAnnotation.revision).label('revision')).group_by(EventAnnotation.event_id).subquery()
    items=db.scalars(select(EventAnnotation).join(latest,(EventAnnotation.event_id==latest.c.event_id)&(EventAnnotation.revision==latest.c.revision))).all()
    return [item.payload for item in items]


@router.get('/facilities/{facility_id}')
def facility_history(facility_id:str,db:Session=Depends(get_db)):
    facility=db.get(ReferenceFacility,facility_id)
    events=db.scalars(select(ThermalEvent).where(ThermalEvent.facility_id==facility_id).order_by(ThermalEvent.start_time).limit(1000)).all()
    if not facility and not events: raise HTTPException(404,'Facility not found')
    return {'facility':{'id':facility.facility_id,'name':facility.name,'type':facility.facility_type,'provenance':facility.provenance} if facility else None,
        'events':serialize_many(events,db),'limit':1000,
        'association_note':'Nearest reference association; does not establish event causation or ownership'}


@router.get('/{event_id}')
def detail(event_id:str,db:Session=Depends(get_db)):
    event=event_or_404(event_id,db)
    observations=db.scalars(select(ThermalObservation).where(ThermalObservation.event_id==event_id).order_by(ThermalObservation.acquisition_time).limit(1000)).all()
    annotations=db.scalars(select(EventAnnotation).where(EventAnnotation.event_id==event_id).order_by(EventAnnotation.revision)).all()
    return {**serialize(event,db),'observations':[o.measurements for o in observations],'observation_limit':1000,
            'annotations':[{'revision':a.revision,'actor_id':a.actor_id,'annotation':a.payload} for a in annotations]}


@router.get('/{event_id}/explanation')
def explanation(event_id:str,shap:bool=False,db:Session=Depends(get_db),user:User=Depends(require_role('analyst'))):
    return predict_event(event_or_404(event_id,db).features,shap_enabled=shap)


class AnnotationRequest(BaseModel):
    expected_revision:int=Field(ge=0)
    action:Literal['save','submit','approve','reject']='save'
    label:str
    confidence:float|None=Field(default=None,ge=0,le=1)
    quality:Literal['A','B','C']='C'
    evidence:list[str]=Field(default_factory=list,max_length=50)
    source:str=Field(default='',max_length=2000)
    notes:str=Field(default='',max_length=10000)


@router.post('/{event_id}/annotations')
def annotate(event_id:str,request:AnnotationRequest,db:Session=Depends(get_db),user:User=Depends(require_role('analyst'))):
    event_or_404(event_id,db)
    latest=db.scalar(select(EventAnnotation).where(EventAnnotation.event_id==event_id).order_by(EventAnnotation.revision.desc()).limit(1))
    revision=latest.revision if latest else 0
    if revision!=request.expected_revision: raise HTTPException(409,'Annotation changed; reload before editing')
    payload=request.model_dump(exclude={'expected_revision','action'})
    payload.update(event_id=event_id,annotator=str(user.id),review_status='submitted' if request.action=='submit' else 'draft')
    if request.action in ('approve','reject'):
        if not latest or latest.payload['review_status']!='submitted': raise HTTPException(409,'Only a submitted annotation can be reviewed')
        if str(user.id)==latest.payload['annotator']: raise HTTPException(403,'A different analyst must review this annotation')
        # Reviewer approves exactly the submitted content, never silently edits its label/evidence.
        payload={**latest.payload,'review_status':'approved' if request.action=='approve' else 'rejected',
                 'reviewer':str(user.id),'reviewed_at':datetime.now(timezone.utc).isoformat()}
    try: validated=Annotation.model_validate(payload)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    row=EventAnnotation(event_id=event_id,revision=revision+1,actor_id=user.id,payload=validated.model_dump(mode='json'))
    db.add(row)
    try: db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Concurrent annotation; reload before editing')
    return {'revision':row.revision,'annotation':row.payload,'training_eligible':validated.training_eligible}


@router.post('/{event_id}/analyze')
def analyze(event_id:str,db:Session=Depends(get_db),user:User=Depends(require_role('analyst'))):
    event=event_or_404(event_id,db)
    intelligence=predict_event(event.features)
    db.add(EventPrediction(event_id=event_id,model_version=intelligence['model_version'],
        decision=intelligence['decision'],confidence=intelligence['confidence'],intelligence=intelligence))
    db.commit()
    return intelligence
