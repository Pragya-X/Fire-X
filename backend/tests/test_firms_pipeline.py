import pandas as pd
from app.ml.data.preprocessing import normalize_firms
from app.ml.data.preprocessing import preprocess


def rows():
    return pd.DataFrame([dict(latitude='22',longitude='70',acq_date='2026-01-01',acq_time='0035',bright_ti4='330',frp='5',daynight='night',confidence='n',satellite='N',instrument='VIIRS')])


def test_viirs_time_and_native_confidence():
    clean, reject, report = normalize_firms(rows())
    assert clean.iloc[0].acquisition_time.hour == 0
    assert clean.iloc[0].acquisition_time.minute == 35
    assert clean.iloc[0].brightness == 330
    assert clean.iloc[0].confidence == 'n'
    assert clean.iloc[0].daynight == 'N'
    assert not len(reject)


def test_invalid_and_duplicate_accounted():
    df = pd.concat([rows()]*4, ignore_index=True)
    df.loc[2,'latitude'] = '91'
    df.loc[3,'acq_time'] = '2461'
    clean, reject, report = normalize_firms(df)
    assert len(clean) == 1 and len(reject) == 3
    assert report['input_rows'] == report['accepted_rows'] + report['rejected_rows']


def test_missing_optional_not_fabricated():
    df = rows().drop(columns=['frp','bright_ti4','daynight'])
    clean, _, _ = normalize_firms(df)
    assert pd.isna(clean.iloc[0].frp) and pd.isna(clean.iloc[0].brightness)


def test_preprocessing_roundtrip(tmp_path):
    path = tmp_path/'input.csv'; rows().to_csv(path,index=False)
    output = tmp_path/'clean.parquet'
    report = preprocess(path, output, tmp_path/'raw', 'synthetic-test')
    assert report['accepted_rows'] == 1
    assert pd.read_parquet(output).iloc[0].data_source == 'synthetic-test'
    assert output.with_suffix('.rejected.csv').exists()


def test_missing_schema_and_invalid_thermal():
    _, rejected, report = normalize_firms(pd.DataFrame([{'latitude':0}]))
    assert report['missing_columns'] and len(rejected) == 1
    df = rows(); df.loc[0,'frp'] = '-1'
    assert len(normalize_firms(df)[1]) == 1


def test_provider_reports_rejected_and_unique_identity():
    from app.providers.firms import FirmsProvider
    df=pd.concat([rows(),rows()],ignore_index=True)
    records,report=FirmsProvider.parse_with_report(df.to_csv(index=False))
    assert len(records)==1 and report['rejected_rows']==1
    assert records[0]['acq_time'].endswith('00:35:00+00:00')
    assert records[0]['confidence_native']=='n'
    assert records[0]['external_id'] != 'VIIRS'


def test_provider_failure_hides_key(monkeypatch):
    import httpx
    import pytest
    from app.config import settings
    from app.providers.firms import FirmsProvider, ProviderUnavailable
    monkeypatch.setattr(settings,'FIRMS_API_KEY','test-secret')
    def fail(*args,**kwargs): raise httpx.ConnectError('https://server/test-secret')
    monkeypatch.setattr(httpx,'get',fail)
    with pytest.raises(ProviderUnavailable) as error:
        FirmsProvider().fetch()
    assert 'test-secret' not in str(error.value)


def test_mixed_sensor_brightness_columns():
    df=rows(); df['brightness']=None
    clean,_,_=normalize_firms(df)
    assert clean.iloc[0].brightness==330
