"""Gated offline normal-operation anomaly experiment; no automatic deployment."""
import argparse
import json
from pathlib import Path
import joblib
from app.ml.training import check_gate,write_json
from app.ml.reference_bundle import sha256
from app.services.event_intelligence import HistoricalAnomalyModel


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('dataset','normal-reviews','output'): parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--kind',choices=['isolation_forest','one_class_svm'],default='isolation_forest')
    args=parser.parse_args()
    try:
        frame,manifest=check_gate(args.dataset)
        reviews=json.loads(args.normal_reviews.read_text())
        model=HistoricalAnomalyModel(args.kind).fit_reviewed(args.dataset,reviews)
        args.output.mkdir(parents=True,exist_ok=True)
        artifact=args.output/f'{args.kind}.joblib';joblib.dump(model,artifact)
        held_out=frame[frame.split=='test']
        write_json(args.output/f'{args.kind}_report.json',{
            'dataset_sha256':manifest['dataset_sha256'],'normal_reviews_sha256':sha256(args.normal_reviews),
            'artifact_sha256':sha256(artifact),'event_ids':held_out.event_id.tolist(),'scores':model.score(held_out),
            'evaluation':None,'reason':'No independently reviewed anomaly outcomes supplied; raw scores are not accuracy or probabilities',
            'deployment_approved':False})
    except (ValueError,OSError) as exc:
        print(f'ANOMALY TRAINING BLOCKED: {exc}');return 2
    return 0

if __name__=='__main__':raise SystemExit(main())
