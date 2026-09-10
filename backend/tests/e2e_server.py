"""Disposable HTTP server for browser integration; never uses the developer DB."""
import os
from pathlib import Path
import tempfile


def main():
    with tempfile.TemporaryDirectory(prefix='firex-e2e-') as root:
        folder=Path(root)
        os.environ.update(DATABASE_URL='sqlite:///'+str(folder/'test.db'),DATA_DIR=str(folder/'data'),
            MODEL_DIR=str(folder/'models'),UPLOAD_DIR=str(folder/'uploads'),ENV='test',DEBUG='false',DEMO_MODE='false',
            SMTP_HOST='',SMTP_USER='',SMTP_PASSWORD='',SATELLITE_API_KEY='',ML_MODE='rules',
            JWT_SECRET='isolated-e2e-only-01234567890123456789')
        from app.database import init_db,SessionLocal
        from app.auth import hash_password
        from app.models import User
        from app.ml.data.preprocessing import preprocess
        from app.ml.build_dataset import build_files
        from app.ml.import_events import import_events
        init_db()
        source=Path(__file__).resolve().parents[2]/'data'/'samples'/'firms_nasa_tutorial.csv'
        clean=folder/'clean.parquet';events=folder/'events.parquet'
        preprocess(source,clean,folder/'raw',source='NASA tutorial excerpt: isolated integration test only')
        build_files(clean,events)
        with SessionLocal.begin() as db:
            db.add(User(email='e2e@example.invalid',name='E2E Analyst',role='analyst',is_active=True,password_hash=hash_password('isolated-e2e-password')))
            import_events(events,db)
        import uvicorn
        uvicorn.run('app.main:app',host='127.0.0.1',port=8101,log_level='warning')

if __name__=='__main__':main()
