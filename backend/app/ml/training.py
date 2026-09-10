"""Prepare reviewed data and run gated experiments. Never promotes legacy models.

CLI: python -m app.ml.training prepare --events ... --labels ... --readiness ...
     --reviews ... --output ... [--strategy temporal --train-end ... --validation-end ...]
     python -m app.ml.training train --dataset ... --output ...
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import pandas as pd
from app.ml.datasets import COLUMNS, STRING_FIELDS, TIME_FIELDS, validate_event_dataset
from app.ml.labels import CLASSES, validate_annotations
from app.ml.reference_bundle import sha256, load_reference_bundle
from app.ml.splits import SplitConfig, make_splits

# Coordinates, IDs, timestamps, source, labels, persistence rule outputs excluded.
FEATURES = [c for c in COLUMNS if c not in STRING_FIELDS | TIME_FIELDS |
            {'centroid_latitude','centroid_longitude','persistence_score'}]
REVIEW_DOMAINS = ('representativeness','references','temporal_history','clustering')


def write_json(path: Path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False))


def assess_inputs(events_path: Path, readiness_path: Path, reviews_path: Path | None) -> list[str]:
    reasons = []
    digest = sha256(events_path)
    report = json.loads(readiness_path.read_text()) if readiness_path.exists() else {}
    if report.get('source_event_sha256') != digest: reasons.append('MISSING_OR_STALE_DATA_READINESS_REPORT')
    if not report.get('readiness',{}).get('DATA_PIPELINE_READY',{}).get('ready'):
        reasons.append('DATA_PIPELINE_NOT_READY')
    manifest_path = events_path.with_suffix('.manifest.json')
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if manifest.get('event_dataset_sha256') != digest: reasons.append('EVENT_MANIFEST_HASH_MISMATCH')
    for key, path in (('membership_sha256',events_path.with_suffix('.membership.parquet')),
                      ('input_sha256',Path(manifest.get('input_path','/nonexistent')))):
        if not path.is_file() or sha256(path) != manifest.get(key): reasons.append(f'STALE_{key.upper()}')
    bundle = manifest.get('reference_bundle_path')
    if not bundle:
        reasons.append('NO_REFERENCE_BUNDLE')
    else:
        try:
            _, provenance = load_reference_bundle(Path(bundle))
            if provenance['reference_sha256'] != manifest.get('reference_sha256'):
                reasons.append('REFERENCE_HASH_MISMATCH')
            roles = {layer['role'] for layer in provenance['layers']}
            if not {'industrial','landcover','administrative'}.issubset(roles): reasons.append('INCOMPLETE_REFERENCE_ROLES')
        except (ValueError, OSError): reasons.append('INVALID_REFERENCE_BUNDLE')
    reviews = json.loads(reviews_path.read_text()) if reviews_path and reviews_path.exists() else {}
    if not isinstance(reviews,dict):
        raise ValueError('Dataset reviews must be an object keyed by review domain')
    for domain in REVIEW_DOMAINS:
        item = reviews.get(domain,{})
        if not isinstance(item,dict):
            reasons.append(f'{domain.upper()}_NOT_REVIEWED')
            continue
        try:
            at = datetime.fromisoformat(str(item.get('reviewed_at') or '').replace('Z','+00:00'))
            valid = (item.get('approved') is True and str(item.get('reviewer') or '').strip()
                and item.get('event_sha256') == digest and at.tzinfo is not None
                and at <= datetime.now(timezone.utc) and item.get('evidence'))
            # Evidence is a local reviewed document, versioned by hash; never trust a bare checkbox.
            for evidence in item.get('evidence',[]):
                path = (reviews_path.parent / evidence['path']).resolve()
                valid = valid and path.is_file() and sha256(path)==evidence['sha256']
            if not valid: reasons.append(f'{domain.upper()}_NOT_REVIEWED')
        except (ValueError,TypeError,KeyError,OSError): reasons.append(f'{domain.upper()}_NOT_REVIEWED')
    return reasons


def prepare(events_path: Path, labels_path: Path, readiness_path: Path, output: Path,
            reviews_path: Path | None = None, config: SplitConfig = SplitConfig()) -> dict:
    output.mkdir(parents=True,exist_ok=True)
    events = pd.read_parquet(events_path)
    validate_event_dataset(events)
    records = json.loads(labels_path.read_text()) if labels_path.exists() else []
    annotations, quality = validate_annotations(records,set(events.event_id))
    reasons = assess_inputs(events_path,readiness_path,reviews_path)
    event_manifest_path=events_path.with_suffix('.manifest.json')
    event_manifest=json.loads(event_manifest_path.read_text()) if event_manifest_path.exists() else {}
    minimum_radius=2*float(event_manifest.get('history_radius_km',1))
    if config.radius_km < minimum_radius:
        reasons.append('GROUP_RADIUS_SMALLER_THAN_SHARED_HISTORY_FOOTPRINT')
    if not quality['valid']: reasons.append('INVALID_ANNOTATIONS')
    if not quality['eligible_count']: reasons.append('NO_ELIGIBLE_REVIEWED_LABELS')
    rows = [{'event_id':a.event_id,'label':a.label,'label_quality':a.quality} for a in annotations if a.training_eligible]
    labels = pd.DataFrame(rows,columns=['event_id','label','label_quality'])
    dataset = events.merge(labels,on='event_id',validate='one_to_one')
    # Administrative data is reviewed against the India area, rather than using
    # this broad envelope as a substitute for an authoritative national boundary.
    if not len(dataset) or not (dataset.centroid_latitude.between(6,38)&dataset.centroid_longitude.between(67,98)).all():
        reasons.append('EMPTY_OR_NON_INDIA_TRAINING_DATA')
    required = set(CLASSES)-{'Unknown'}
    distribution = dataset.label.value_counts().to_dict()
    if any(distribution.get(label,0)<30 for label in required): reasons.append('MINIMUM_CLASS_SUPPORT_NOT_MET')
    try:
        assignments, split_audit = make_splits(dataset,config)
        if not split_audit['valid']: reasons.extend(split_audit['reasons'])
        dataset = dataset.merge(assignments,on='event_id',validate='one_to_one')
        for split in ('train','validation','test'):
            counts = dataset[dataset.split==split].label.value_counts()
            if any(counts.get(label,0)<5 for label in required): reasons.append(f'LOW_CLASS_SUPPORT_{split.upper()}')
    except ValueError as exc:
        split_audit = {'valid':False,'reasons':[str(exc)]}
        dataset['split'] = 'excluded'
        dataset['group_id'] = pd.Series(index=dataset.index,dtype='string')
        reasons.append('SPLIT_VALIDATION_FAILED')
    # Feature selection uses training observations only, never validation/test.
    train = dataset[dataset.split=='train']
    features = [c for c in FEATURES if len(train) and train[c].notna().any()]
    if not features: reasons.append('NO_TRAINABLE_FEATURES')
    path = output/'training_dataset.parquet'
    dataset.to_parquet(path,index=False)
    inputs = {'events':{'path':str(events_path.resolve()),'sha256':sha256(events_path)},
              'labels':{'path':str(labels_path.resolve()),'sha256':sha256(labels_path) if labels_path.exists() else None},
              'readiness':{'path':str(readiness_path.resolve()),'sha256':sha256(readiness_path) if readiness_path.exists() else None}}
    if reviews_path:
        inputs['reviews']={'path':str(reviews_path.resolve()),'sha256':sha256(reviews_path) if reviews_path.exists() else None}
    metadata = {'version':'event-training-v1','training_ready':not reasons,'blockers':sorted(set(reasons)),
        'dataset_sha256':sha256(path),'dataset_version':sha256(path)[:16], 'inputs':inputs,
        'features':features,'excluded_features':sorted(set(COLUMNS)-set(features)),
        'feature_importance_candidates':{'type':'unranked_candidates_not_measured_importance','features':FEATURES},
        'class_distribution':distribution,'label_quality':quality,'split_audit':split_audit,
        'missing_values':{c:int(dataset[c].isna().sum()) for c in FEATURES},
        'support_policy':'Engineering floor: 30 independently reviewed events per class and 5/class/split. Not evidence of adequacy or generalization.',
        'training_data_type':'real_reviewed_events','created_at':datetime.now(timezone.utc).isoformat()}
    write_json(output/'training_manifest.json',metadata)
    write_json(output/'feature_manifest.json',{'features':features,'excluded':metadata['excluded_features']})
    write_json(output/'label_quality_report.json',quality)
    write_json(output/'split_report.json',split_audit)
    return metadata


def check_gate(path: Path) -> tuple[pd.DataFrame,dict]:
    manifest = json.loads((path.parent/'training_manifest.json').read_text())
    if manifest.get('training_ready') is not True or manifest.get('blockers'):
        raise ValueError('TRAINING BLOCKED: readiness is false or unresolved blockers remain')
    if sha256(path) != manifest.get('dataset_sha256'): raise ValueError('TRAINING BLOCKED: dataset hash mismatch')
    for item in manifest['inputs'].values():
        source = Path(item['path'])
        if not source.is_file() or sha256(source) != item['sha256']: raise ValueError('TRAINING BLOCKED: stale source inputs')
    inputs = manifest['inputs']
    if 'reviews' not in inputs: raise ValueError('TRAINING BLOCKED: no reviewed evidence')
    reasons = assess_inputs(Path(inputs['events']['path']),Path(inputs['readiness']['path']),Path(inputs['reviews']['path']))
    if reasons: raise ValueError(f'TRAINING BLOCKED: {reasons}')
    frame = pd.read_parquet(path)
    # Reconstruct labels and assignments from source inputs; edited manifests or
    # reassigned folds cannot make a blocked dataset trainable.
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        rebuilt = prepare(Path(inputs['events']['path']),Path(inputs['labels']['path']),
            Path(inputs['readiness']['path']),Path(directory),Path(inputs['reviews']['path']),
            SplitConfig(**manifest['split_audit']['config']))
        expected = pd.read_parquet(Path(directory)/'training_dataset.parquet')
        if not rebuilt['training_ready'] or not frame.equals(expected) or rebuilt['features']!=manifest['features']:
            raise ValueError('TRAINING BLOCKED: reconstructed dataset/readiness mismatch')
    return frame, manifest


def train(path: Path, output: Path) -> dict:
    # Before importing/fitting ANY estimator, validate all input provenance and gates.
    frame, manifest = check_gate(path)
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.inspection import permutation_importance
    from app.ml.evaluation import evaluate
    import sklearn
    import joblib
    output.mkdir(parents=True,exist_ok=True)
    models = {'logistic_regression':LogisticRegression(max_iter=3000, class_weight='balanced',random_state=42),
              'hist_gradient_boosting':HistGradientBoostingClassifier(max_iter=300,random_state=42)}
    unavailable = {}
    for name, module, cls, kwargs in (
        ('lightgbm','lightgbm','LGBMClassifier',{'n_estimators':200,'random_state':42,'verbosity':-1}),
        ('xgboost','xgboost','XGBClassifier',{'n_estimators':200,'random_state':42}),
        ('catboost','catboost','CatBoostClassifier',{'iterations':200,'random_seed':42,'verbose':False,'allow_writing_files':False})):
        try:
            import importlib
            models[name] = getattr(importlib.import_module(module),cls)(**kwargs)
        except ImportError: unavailable[name] = 'Optional dependency not installed'
    features = manifest['features']
    parts = {s:frame[frame.split==s] for s in ('train','validation','test')}
    encoder = LabelEncoder().fit(parts['train'].label)
    classes = encoder.classes_.tolist()
    fitted, comparison = {}, {}
    def x(rows): return rows[features].astype(float).to_numpy()
    for name, estimator in models.items():
        pipeline = Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),
                             ('scaler',StandardScaler()),('model',estimator)])
        pipeline.fit(x(parts['train']),encoder.transform(parts['train'].label))
        validation = evaluate(parts['validation'].label,pipeline.predict_proba(x(parts['validation'])),classes)
        comparison[name] = {'validation':validation}
        fitted[name] = pipeline
    winner = max(comparison,key=lambda n:comparison[n]['validation']['classification_report']['macro avg']['f1-score'])
    # Select exclusively on validation macro F1. Test set is evaluated only after selection.
    pipeline = fitted[winner]
    test = evaluate(parts['test'].label,pipeline.predict_proba(x(parts['test'])),classes)
    importance = permutation_importance(pipeline,x(parts['validation']),encoder.transform(parts['validation'].label),
        scoring='f1_macro',n_repeats=5,random_state=42)
    report = {'dataset_version':manifest['dataset_version'],'winner':winner,'selection':'validation macro F1',
        'comparison':comparison,'unavailable_models':unavailable,'test':test,
        'validation_permutation_importance':{f:{'mean':float(m),'std':float(s)} for f,m,s in zip(features,importance.importances_mean,importance.importances_std)},
        'training_data_type':'real_reviewed_events','deployment_approved':False,
        'versions':{'python':platform.python_version(),'sklearn':sklearn.__version__},
        'limitations':['No external benchmark or confidence intervals yet','Calibration measured, not optimized','No operational deployment approval']}
    artifact = {'pipeline':pipeline,'features':features,'classes':classes,'metadata':manifest,'report':report,
                'background':x(parts['train'])[:50]}
    joblib.dump(artifact,output/'event_classifier.joblib')
    report['artifact_sha256']=sha256(output/'event_classifier.joblib')
    write_json(output/'evaluation.json',report)
    lines = ['# Event model experiment',f"Dataset: {manifest['dataset_version']}",f'Selected model: {winner}',
             'Selection used validation macro F1. Held-out test evaluated after selection. No automatic production promotion.',
             '| Metric | Held-out test |','|---|---|',f"| Accuracy | {test['accuracy']:.4f} |",
             f"| Macro F1 | {test['classification_report']['macro avg']['f1-score']:.4f} |",
             f"| Weighted F1 | {test['classification_report']['weighted avg']['f1-score']:.4f} |",
             'Full precision/recall/F1, ROC/PR, confusion matrix and reliability bins: evaluation.json.',
             f'Unavailable dependencies: {unavailable}',*report['limitations']]
    (output/'model_report.md').write_text('\n\n'.join(lines)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare')
    for name in ('events','labels','readiness','output'): p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--reviews',type=Path)
    p.add_argument('--strategy',choices=['group','geographic','temporal','facility'],default='geographic')
    p.add_argument('--train-end'); p.add_argument('--validation-end')
    t=sub.add_parser('train'); t.add_argument('--dataset',type=Path,required=True); t.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.command=='prepare':
            result=prepare(args.events,args.labels,args.readiness,args.output,args.reviews,
                SplitConfig(strategy=args.strategy,train_end=args.train_end,validation_end=args.validation_end))
            print(json.dumps({'training_ready':result['training_ready'],'blockers':result['blockers']},indent=2))
            return 0 if result['training_ready'] else 2
        train(args.dataset,args.output)
        return 0
    except (ValueError,OSError,KeyError) as exc:
        print(f'TRAINING BLOCKED: {exc}')
        return 2

if __name__=='__main__': raise SystemExit(main())
