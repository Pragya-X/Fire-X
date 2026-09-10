"""Metrics derived exclusively from held-out predictions; no placeholder scores."""
from __future__ import annotations
import numpy as np
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
    precision_recall_curve, roc_curve, roc_auc_score, average_precision_score, log_loss)


def evaluate(y_true, probabilities, classes) -> dict:
    classes = list(classes)
    probabilities = np.asarray(probabilities, dtype=float)
    y = np.asarray(y_true)
    if probabilities.shape != (len(y),len(classes)) or not len(y):
        raise ValueError('Invalid evaluation dimensions')
    if not np.isfinite(probabilities).all() or (probabilities<0).any() or not np.allclose(probabilities.sum(axis=1),1):
        raise ValueError('Invalid probability distribution')
    if not set(y).issubset(classes): raise ValueError('Unknown evaluation classes')
    pred = np.asarray(classes)[probabilities.argmax(axis=1)]
    report = {'n':len(y), 'classes':classes, 'accuracy':float(accuracy_score(y,pred)),
        'classification_report':classification_report(y,pred,labels=classes,output_dict=True,zero_division=0),
        'confusion_matrix':confusion_matrix(y,pred,labels=classes).tolist(),
        'log_loss':float(log_loss([classes.index(label) for label in y],probabilities,labels=list(range(len(classes))))), 'per_class':{}}
    for i,label in enumerate(classes):
        truth = (y==label).astype(int)
        if len(np.unique(truth))<2:
            report['per_class'][label] = {'available':False,'reason':'Both positive and negative samples required'}
            continue
        p = probabilities[:,i]
        fpr,tpr,_ = roc_curve(truth,p)
        precision,recall,_ = precision_recall_curve(truth,p)
        bins = []
        membership = np.minimum((p*10).astype(int), 9)
        for index in range(10):
            low = index / 10
            mask = membership == index
            if mask.any(): bins.append({'lower':float(low),'count':int(mask.sum()),
                'mean_probability':float(p[mask].mean()),'observed_frequency':float(truth[mask].mean())})
        report['per_class'][label] = {'available':True,'roc_auc':float(roc_auc_score(truth,p)),
            'average_precision':float(average_precision_score(truth,p)),
            'brier_score':float(np.mean((p-truth)**2)),
            'roc':{'fpr':fpr.tolist(),'tpr':tpr.tolist()},
            'pr':{'precision':precision.tolist(),'recall':recall.tolist()},'reliability':bins}
    report['calibration_note'] = 'Uncalibrated model probabilities; reliability assessed on held-out data. Empty bins omitted.'
    return report
