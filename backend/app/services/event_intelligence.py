"""Event decisions, confidence and explanations with explicit model approval.

Heuristic scores are not probabilities. Facility proximity cannot establish
cause. Pickled artifacts require trusted local paths and hash-bound approval."""
from __future__ import annotations
import math
import numpy as np
import json
import pickle
from pathlib import Path
from datetime import datetime, timezone
from app.config import settings
from app.ml.reference_bundle import sha256
from app.ml.training import check_gate


def number(value):
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except (ValueError,TypeError): return None


def statistical_anomaly(event: dict) -> dict:
    n = number(event.get('detections_90d')) or 0
    current, mean, std = (number(event.get(k)) for k in ('mean_frp','historical_mean_frp','historical_std_frp'))
    result = {'method':'historical_z_score','score':None,'deviation_mw':None,
              'historical_mean_mw':mean,'historical_std_mw':std,'sample_count':int(n),
              'status':'unavailable','reason':'At least five historical detections and nonzero variance required'}
    if current is not None and mean is not None: result['deviation_mw']=current-mean
    if n>=5 and current is not None and mean is not None and std is not None and std>0:
        z = (current-mean)/std
        result.update(score=z,status='elevated' if z>=3 else 'within_baseline',reason='Signed FRP deviation in historical standard deviations; 3 is an unvalidated heuristic threshold')
    return result


def persistence(event: dict) -> dict:
    days = number(event.get('active_days_90d'))
    mean, std = number(event.get('historical_mean_frp')), number(event.get('historical_std_frp'))
    cv = std/mean if mean is not None and mean>0 and std is not None else None
    if days is None or days<5:
        return {'status':'insufficient_history','observed_recurrence':days/90 if days is not None else None,
                'coefficient_of_variation':cv,'reason':'At least five active historical days required'}
    status = 'persistent_candidate' if days>=30 and cv is not None and cv<=.5 else 'recurrent_activity'
    return {'status':status,'observed_recurrence':days/90,'coefficient_of_variation':cv,
            'reason':'Observed recurrence and FRP stability; thresholds require validation. No inference of gas flare or mining without independent evidence.'}


def hybrid_decision(event: dict, classifier: dict | None = None) -> dict:
    anomaly, recurring = statistical_anomaly(event), persistence(event)
    reasons = []
    context = []
    for field,label in (('inside_industrial_polygon','industrial polygon'),('inside_forest','forest'),('inside_agriculture','agriculture')):
        if event.get(field) is True: context.append(label)
    if event.get('nearest_facility_type'): context.append(f"nearest reference: {event['nearest_facility_type']}")
    decision, confidence, mode = 'Unknown', None, 'evidence_rules'
    if classifier and classifier.get('mode')=='trained' and classifier.get('probabilities'):
        probabilities=classifier['probabilities']
        values=[number(v) for v in probabilities.values()]
        if any(v is None or v<0 or v>1 for v in values) or abs(sum(values)-1)>1e-5:
            raise ValueError('Invalid classifier probabilities')
        decision=max(probabilities,key=probabilities.get)
        confidence=probabilities[decision]
        mode='trained_with_context'
        reasons.append('Decision from reviewed event model; confidence is an uncalibrated model probability')
    else:
        reasons.append('No approved event classifier; source class cannot be established from thermal/context evidence alone')
    if recurring['status']=='persistent_candidate': reasons.append('Stable repeated heat supports a persistent-source candidate')
    if anomaly['status']=='elevated': reasons.append('Elevated FRP warrants analyst review; does not establish an industrial fire')
    if context: reasons.append('Observed context: '+', '.join(context))
    priority = 'review' if anomaly['status']=='elevated' else 'unassessed'
    return {'decision':decision,'confidence':confidence,'confidence_type':'uncalibrated_model_probability' if confidence is not None else 'unavailable',
            'mode':mode,'reasons':reasons,'anomaly':anomaly,'persistence':recurring,'risk':{'priority':priority,'score':None},
            'explanation':{'type':'evidence_rules','context':context,'shap':{'available':False,'reason':'No approved event model loaded'}}}


class HistoricalAnomalyModel:
    """Optional experiments on reviewed normal TRAIN rows; no project auto-fit.

    Scores are raw decision-function deviations, not calibrated probabilities.
    This module requires the same real-data gate as classifier experiments.
    """
    def __init__(self, kind='isolation_forest'):
        if kind not in ('isolation_forest','one_class_svm'): raise ValueError('Unknown anomaly model')
        self.kind=kind
        self.pipeline=None

    def fit_reviewed(self, dataset_path, normal_reviews):
        from app.ml.training import check_gate
        from sklearn.pipeline import make_pipeline
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler
        from sklearn.ensemble import IsolationForest
        from sklearn.svm import OneClassSVM
        frame, manifest=check_gate(dataset_path)
        train=frame[frame.split=='train']
        from app.ml.normal_reviews import validate_normal_reviews
        normal_event_ids=validate_normal_reviews(normal_reviews,manifest['dataset_sha256'])
        if len(set(normal_event_ids))<30 or not set(normal_event_ids).issubset(set(train.event_id)):
            raise ValueError('At least 30 reviewed normal event IDs from training partition required')
        self.features=manifest['features']
        model=IsolationForest(random_state=42,contamination='auto') if self.kind=='isolation_forest' else OneClassSVM(nu=.05)
        self.pipeline=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),model)
        self.pipeline.fit(train[train.event_id.isin(normal_event_ids)][self.features].astype(float).to_numpy())
        return self

    def score(self, events):
        if self.pipeline is None: raise ValueError('Anomaly model is not fitted')
        return {'method':self.kind,'scores':(-self.pipeline.decision_function(events[self.features].astype(float).to_numpy())).tolist(),
                'score_type':'raw_anomaly_deviation_not_probability'}


def explain_artifact(artifact: dict, event: dict, *, shap_enabled=False) -> dict:
    """Only call with trusted local experiment artifacts. SHAP is opt-in/expensive."""
    features=artifact['features']
    row=np.array([[number(event.get(f)) if number(event.get(f)) is not None else np.nan for f in features]])
    pipeline=artifact['pipeline']
    probabilities=pipeline.predict_proba(row)[0]
    explanation={'probabilities':dict(zip(artifact['classes'],map(float,probabilities))),
        'feature_importance':artifact['report'].get('validation_permutation_importance',{}),
        'importance_type':'validation_permutation_macro_f1','shap':{'available':False,'reason':'Not requested'}}
    if shap_enabled:
        try:
            import shap
            background=np.asarray(artifact['background'],dtype=float)
            # Explain the entire pipeline so raw features remain aligned, including missingness.
            explainer=shap.Explainer(pipeline.predict_proba,background,algorithm='permutation',seed=42)
            values=explainer(row,max_evals=2*len(features)+1)
            explanation['shap']={'available':True,'features':features,'values':values.values[0].tolist(),
                'base_values':values.base_values[0].tolist(),'classes':artifact['classes'],'output':'probability'}
        except ImportError:
            explanation['shap']={'available':False,'reason':'Optional SHAP dependency not installed'}
    return explanation


def load_approved_model():
    configured=settings.EVENT_MODEL_PATH.strip()
    if not configured: return None,'No approved event model configured'
    path=Path(configured).resolve()
    if not path.is_relative_to(Path(settings.MODEL_DIR).resolve()): return None,'Event artifact must reside inside MODEL_DIR'
    try:
        approval=json.loads(path.with_suffix('.approval.json').read_text())
        reviewed=datetime.fromisoformat(str(approval.get('reviewed_at') or '').replace('Z','+00:00'))
        if (approval.get('deployment_approved') is not True or not approval.get('reviewer','').strip()
            or not approval.get('evidence','').strip() or reviewed.tzinfo is None or reviewed>datetime.now(timezone.utc)
            or sha256(path)!=approval.get('artifact_sha256')):
            return None,'Deployment approval missing, invalid or stale'
        _,manifest=check_gate(Path(approval['training_dataset_path']))
        import joblib
        artifact=joblib.load(path)
        if (artifact['metadata']['dataset_sha256']!=manifest['dataset_sha256']
            or artifact['features']!=manifest['features'] or artifact['report']['training_data_type']!='real_reviewed_events'):
            return None,'Event artifact does not match the reviewed training dataset'
        return artifact,None
    except (OSError,ValueError,KeyError,TypeError,AttributeError,EOFError,pickle.UnpicklingError):
        return None,'Approved event artifact or reviewed source inputs unavailable/invalid'


def model_status():
    model,reason=load_approved_model()
    return {'model_mode':'trained' if model else 'evidence_rules','trained_event_model_available':bool(model),
            'training_ready':bool(model),'model_version':model['metadata']['dataset_version'] if model else 'event-evidence-rules-v1',
            'reason':reason or 'Operator-approved reviewed event classifier; probabilities remain uncalibrated',
            'shap_available':bool(model) and __import__('importlib.util',fromlist=['find_spec']).find_spec('shap') is not None}


def predict_event(event:dict,*,shap_enabled=False):
    model,reason=load_approved_model()
    if model is None:
        result=hybrid_decision(event)
        result['model_version']='event-evidence-rules-v1'
        result['explanation']['shap']['reason']=reason
        return result
    explanation=explain_artifact(model,event,shap_enabled=shap_enabled)
    result=hybrid_decision(event,{'mode':'trained','probabilities':explanation['probabilities']})
    result['explanation']=explanation
    result['model_version']=model['metadata']['dataset_version']
    return result
