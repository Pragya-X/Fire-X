# Deployment guide and current limitations

**This repository is not certified production-ready.** Real-data validation, trained-model evaluation, a supported dependency baseline, PostGIS migration execution, load testing and operational controls remain outstanding.

## Local development

Use Python 3.12 and the project virtual environment. Install `backend/requirements.txt`; add `backend/requirements-dev.txt` for coverage. Start the backend from `backend` with `uvicorn app.main:app --reload`. The default SQLite/demo configuration is for local demonstrations. Copy `.env.example` deliberately; never commit credentials.

In `frontend`, use `npm ci`, `npm run build`, then `npm run start`. The start script copies static assets into the Next standalone directory and invokes its server. For development use `npm run dev`. Build-time `NEXT_PUBLIC_API_URL` must be reachable from the user's browser; changing it only at container runtime does not rewrite a built bundle.

## Containers

The base `docker-compose.yml` is a local demonstration configuration. The production override is tooling and has not been executed here: Docker is unavailable in this environment.

```sh
docker compose -f docker-compose.yml -f docker-compose.production.yml config
docker compose -f docker-compose.yml -f docker-compose.production.yml build
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

Supply POSTGRES_PASSWORD, DATABASE_URL (URL-encode credentials), JWT_SECRET, CORS_ORIGINS, FRONTEND_URL and PUBLIC_API_URL through a secret-managed deployment environment. Use a Compose version supporting `!reset`; validate the merged configuration before starting. Arrange TLS termination, restricted ingress, network policy and correct persistent-volume ownership. The PostgreSQL port is removed by the production override. Avoid exposing backend port 8000 directly to an untrusted network; it is intended behind the controlled TLS ingress.

The backend now installs its PostgreSQL driver, runs as a non-root user, and excludes `.env`, databases, uploads and caches from the Docker build context. Frontend builds use `npm ci` and create the optional public directory before copying standalone output. Unused Redis was removed from the base stack.

Production configuration fails closed if DEBUG/DEMO_MODE is enabled, JWT_SECRET is short or a known development value, CORS uses wildcard/non-HTTPS origins, or PostgreSQL is absent. Google OAuth is disabled in production pending state/PKCE and token transport hardening. No demo users are seeded in production. Bootstrap the first administrator interactively using `python -m app.create_admin` inside the backend environment, then create other users through authenticated administration. Never use seeded passwords for a production deployment.

## Database initialization and migration

Application initialization creates the SQLAlchemy tables. Then, with a database backup and appropriate migration privileges, apply `backend/migrations/001_event_postgis.sql`. It adds generated Point/Geometry columns, SRID 4326 and GiST indexes for the new event/facility/observation tables. SQLite tests do not validate native PostGIS behavior. Validate PostGIS_Version, geometry validity/SRID, EXPLAIN plans for spatial queries, role privileges, rollback and restore before claiming production GIS readiness. This is an explicit SQL migration; a complete schema-version migration framework remains technical debt.

The legacy hotspots still store WKT. The new observations have coordinates and timestamps; prediction JSON records anomaly/persistence/risk evidence. Import is atomic and idempotent for an identical artifact. Conflicting event or facility provenance requires explicit version migration rather than silent overwrite.

## Security audit outcomes

- New event routes require authenticated access. Annotation, analysis and model explanations require analyst or admin roles. Independent review and optimistic revisions prevent self-approval and stale writes.
- Legacy classification mutation now requires analyst authentication and logs the acting user.
- Password-reset tokens cannot authorize normal API access. Reset tokens are bound to the current password hash and become invalid after use or a password change.
- Map popup text is escaped. Non-demo satellite imagery never uses the synthetic canvas renderer; unavailable measurements display as unavailable.
- Production disables scenario/demo ingest routes. Unconfigured FIRMS/satellite services do not fall back to synthetic outputs when DEMO_MODE=false. Health reports missing credentials without throwing a server error.
- Request logs include generated request ID, method, status and duration, excluding request bodies, credentials and query strings. Response headers include nosniff and no-referrer.
- Joblib artifacts are executable serialization. Only trusted operator-managed local artifacts are accepted, after hash-bound deployment approval and source-readiness validation.

The earlier recorded npm audit reports **two high-severity findings**, associated with Next.js/PostCSS. See `reports/npm_audit.json`. That recorded fix proposal requires a major migration; check a fresh audit before choosing versions. Next 14 is outside the supported LTS lines listed in the [official support policy](https://nextjs.org/support-policy). A supported Next/React migration and regression verification is required before public deployment; no forced upgrade was applied.

Other open controls: rate limiting and brute-force protection, a hardened OAuth flow, access-token revocation after password changes, HTTP-only session design/CSP review, authenticated policy for remaining legacy read endpoints, per-tenant data authorization if needed, dependency scanning for Python, storage retention/encryption policy, malware controls for any future uploads, SMTP deliverability, backup/restore tests, monitoring and alert routing. These are concrete gaps, not claims of an implemented security certification.

## Health and evidence

`/api/v1/health` is liveness. `/api/v1/system-health` includes database/provider status but is not a load, network or image-processing proof. Event status is `/api/v1/thermal-events/status`; offline dataset readiness is in its hash-bound manifest. Running a server, building a container or opening a dashboard does not establish scientific validation.

Legacy live-ingestion GIS context also respects DEMO_MODE=false: configure REFERENCE_BUNDLE_PATH to a validated real bundle, or context remains empty. It never loads seeded facilities in that mode. Restart after changing a cached bundle or its layers. Prefer the versioned event-artifact workflow for scientifically reviewed operations.
