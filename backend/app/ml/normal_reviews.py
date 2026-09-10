"""Normal-operation evidence is distinct from the event source class."""
from datetime import datetime,timezone


def validate_normal_reviews(document:dict,dataset_sha256:str) -> list[str]:
    if not isinstance(document,dict) or document.get('dataset_sha256')!=dataset_sha256:
        raise ValueError('Normal-operation review must match the training dataset hash')
    ids=[]
    for row in document.get('reviews',[]):
        try:
            when=datetime.fromisoformat(str(row.get('reviewed_at') or '').replace('Z','+00:00'))
            if (row.get('normal_operation') is not True or not row.get('reviewer','').strip()
                or row.get('reviewer')==row.get('annotator') or not row.get('annotator','').strip()
                or not row.get('source','').strip() or not row.get('evidence') or not row.get('event_id')
                or when.tzinfo is None or when>datetime.now(timezone.utc)):
                raise ValueError('Incomplete independent normal-operation evidence')
            ids.append(row['event_id'])
        except (KeyError,TypeError) as exc: raise ValueError('Invalid normal-operation review') from exc
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate normal-operation review')
    return ids
