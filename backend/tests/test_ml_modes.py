import joblib
import numpy as np
from sklearn.dummy import DummyClassifier
from app.config import settings
from app.ml.predict import classification_health, classify_vector
from test_classification import _vec


def test_rules_ignores_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'MODEL_DIR', str(tmp_path))
    monkeypatch.setattr(settings, 'ML_MODE', 'rules')
    (tmp_path / 'model.pkl').write_bytes(b'bad')
    assert classification_health()['model_mode'] == 'RULES'


def test_demo_is_never_real(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'MODEL_DIR', str(tmp_path))
    monkeypatch.setattr(settings, 'ML_MODE', 'demo')
    model = DummyClassifier().fit(np.zeros((2,14)), ['Wildfire', 'Wildfire'])
    joblib.dump(model, tmp_path / 'model.pkl')
    result = classify_vector(_vec())
    assert result['model_mode'] == 'DEMO_MODEL'
    assert result['training_data_type'] == 'synthetic'


def test_missing_or_wrong_real_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'MODEL_DIR', str(tmp_path))
    monkeypatch.setattr(settings, 'ML_MODE', 'trained')
    assert classification_health()['model_mode'] == 'RULES'
    assert classification_health()['fallback_reason']
    (tmp_path / 'model_metadata.json').write_text('{"training_data_type":"synthetic"}')
    assert classify_vector(_vec())['model_mode'] == 'RULES'


def test_configured_demo_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'MODEL_DIR', str(tmp_path))
    monkeypatch.setattr(settings, 'ML_MODE', 'trained')
    monkeypatch.setattr(settings, 'ML_FALLBACK_MODE', 'demo')
    model = DummyClassifier().fit(np.zeros((2,14)), ['Wildfire', 'Wildfire'])
    joblib.dump(model, tmp_path / 'model.pkl')
    health = classification_health()
    assert health['model_mode'] == 'DEMO_MODEL' and health['requested_mode'] == 'trained'
    assert health['fallback_reason'] and health['training_data_type']=='synthetic'


def test_feature_count_and_corrupt_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'MODEL_DIR', str(tmp_path))
    monkeypatch.setattr(settings, 'ML_MODE', 'demo')
    joblib.dump(DummyClassifier().fit(np.zeros((2,3)), ['Wildfire']*2),tmp_path/'model.pkl')
    assert classification_health()['model_mode']=='RULES'
    (tmp_path/'model.pkl').write_bytes(b'corrupt')
    assert classification_health()['model_mode']=='RULES'
