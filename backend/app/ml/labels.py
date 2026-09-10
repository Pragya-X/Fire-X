"""Reviewed event annotations. Labels never derive from a model or context rule."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Literal
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

CLASSES = ('Industrial Fire', 'Persistent Industrial Source', 'Wildfire',
           'Agricultural Burning', 'Gas Flare', 'Mining', 'Other', 'Unknown')

class Annotation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    event_id: str = Field(min_length=1, max_length=100)
    label: Literal['Industrial Fire', 'Persistent Industrial Source', 'Wildfire',
                   'Agricultural Burning', 'Gas Flare', 'Mining', 'Other', 'Unknown']
    review_status: Literal['draft', 'submitted', 'approved', 'rejected'] = 'draft'
    annotator: str = Field(min_length=1, max_length=255)
    reviewer: str | None = Field(default=None, max_length=255)
    confidence: float | None = Field(default=None, ge=0, le=1)
    quality: Literal['A', 'B', 'C'] = 'C'
    evidence: list[str] = Field(default_factory=list, max_length=50)
    source: str = Field(default='', max_length=2000)
    notes: str = Field(default='', max_length=10000)
    reviewed_at: datetime | None = None

    @model_validator(mode='after')
    def reviewed_evidence(self):
        if self.reviewed_at is not None:
            if self.reviewed_at.tzinfo is None or self.reviewed_at > datetime.now(timezone.utc):
                raise ValueError('Review time must be timezone-aware and cannot be in the future')
        if self.review_status == 'approved':
            if not self.reviewer or self.reviewer.casefold() == self.annotator.casefold():
                raise ValueError('Approval requires a different reviewer')
            if not self.source or not self.evidence or any(not value.strip() for value in self.evidence):
                raise ValueError('Approval requires traceable source and evidence references')
            if self.confidence is None or self.reviewed_at is None:
                raise ValueError('Approval requires confidence and review timestamp')
        return self

    @property
    def training_eligible(self) -> bool:
        return (self.review_status == 'approved' and self.label != 'Unknown'
                and self.quality in ('A', 'B') and self.confidence is not None and self.confidence >= .8)


def validate_annotations(records: list[dict], event_ids: set[str]) -> tuple[list[Annotation], dict]:
    annotations, errors, seen = [], [], set()
    for index, record in enumerate(records):
        try:
            item = Annotation.model_validate(record)
            if item.event_id not in event_ids:
                raise ValueError('Unknown event ID')
            if item.event_id in seen:
                raise ValueError('Duplicate event annotation; supply only the latest revision')
            seen.add(item.event_id)
            annotations.append(item)
        except ValueError as exc:
            errors.append({'row': index, 'error': str(exc)})
    eligible = [a for a in annotations if a.training_eligible]
    return annotations, {'valid': not errors, 'errors': errors, 'annotation_count': len(annotations),
        'eligible_count': len(eligible), 'unlabeled_count': len(event_ids - seen),
        'class_distribution': dict(pd.Series([a.label for a in eligible], dtype='string').value_counts().items()),
        'quality_distribution': dict(pd.Series([a.quality for a in annotations], dtype='string').value_counts().items()),
        'policy': 'Independent approval, evidence, A/B quality, confidence >=0.8; Unknown is excluded.'}
