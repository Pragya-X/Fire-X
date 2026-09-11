# Hosting FIRE-X: Vercel (frontend) + Render (backend) + Supabase (database)

The app is split across two deploy repos (kept in sync from this monorepo via `git subtree`):

- Frontend: https://github.com/Pragya-X/Frontend (deployed on Vercel)
- Backend: https://github.com/Itz-Npg/Backend (deployed on Render)

Total cost: **₹0/month** on the three free tiers.

| Piece | Provider | Plan | Why |
|---|---|---|---|
| Next.js frontend | Vercel | Free | Best Next.js host, free HTTPS + CDN |
| FastAPI backend | Render | Free (Web Service, Docker) | Always-on process — required for SSE live feed + FIRMS scheduler |
| PostgreSQL + PostGIS | Supabase | Free (500 MB) | Managed Postgres with PostGIS built in |

> **Why not AlwaysData?** Its Python hosting runs apps behind uWSGI (WSGI only, no ASGI).
> FIRE-X needs ASGI: the SSE stream (`/api/v1/events/stream`) breaks behind uWSGI and the
> FastAPI lifespan hook that starts the FIRMS scheduler never runs. Its free tier is also
> 256 MB RAM — too small for pandas/sklearn. AlwaysData is great for Django/Flask, not this stack.

---

## Step 1 — Supabase: create the database

1. Sign up at [supabase.com](https://supabase.com) → **New project** (pick a region near you, e.g. Mumbai/Singapore).
2. Set a strong database password and save it.
3. Go to **Project Settings → Database → Connection string → URI** and copy the **Session pooler** URI. It looks like:
   ```
   postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```
4. **URL-encode the password** if it contains special characters (`@` → `%40`, `#` → `%23`, etc.).
5. This full string becomes `DATABASE_URL` in Step 2. The app enables `CREATE EXTENSION IF NOT EXISTS postgis` automatically on first boot.

## Step 2 — Render: deploy the backend

1. [render.com](https://render.com) → **New → Web Service** → connect the `Itz-Npg/Backend` repo.
2. Settings:
   - **Root Directory:** `.` (default — the repo *is* the backend)
   - **Runtime:** Docker (uses the repo's `Dockerfile`; it honors Render's `PORT`)
   - **Instance Type:** Free
4. Add environment variables:

   | Key | Value |
   |---|---|
   | `ENV` | `production` |
   | `DEBUG` | `false` |
   | `DEMO_MODE` | `false` |
   | `ML_MODE` | `rules` |
   | `DATABASE_URL` | the Supabase URI from Step 1 |
   | `JWT_SECRET` | `openssl rand -hex 32` output (≥32 chars, unique) |
   | `CORS_ORIGINS` | `https://<your-vercel-domain>` (add after Step 4, then redeploy) |
   | `FRONTEND_URL` | `https://<your-vercel-domain>` |
   | `FIRMS_API_KEY` | your NASA FIRMS key (real hotspot data) |
   | `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | your Gmail app-password SMTP config (same values as local `backend/.env`) |
   | `MAIL_ALERT_RECIPIENTS` | comma-separated alert email list (optional) |

   The production config guard **fails closed**: without a real 32+ char JWT secret, an HTTPS
   CORS origin, and Postgres, the backend refuses to boot. That is intentional — supply the real values.
5. **Create Web Service.** First boot creates all tables via `init_db()`.
6. Note your API URL, e.g. `https://firex-api.onrender.com` (visible on the service page).

## Step 3 — Create the first admin (no demo seeding in production)

Run from your own laptop against the remote database (Render's free tier has no SSH):

```sh
cd backend
DATABASE_URL="postgresql://postgres.<ref>:<url-encoded-password>@aws-0-<region>.pooler.supabase.com:5432/postgres" \
  python -m app.create_admin
```

It prompts for email + a 14+ character password, runs `init_db()` (safe if tables already exist),
and inserts the single initial administrator. Create all other users through the authenticated
Admin Panel afterwards. Never reuse the local demo passwords.

## Step 4 — Vercel: deploy the frontend

1. [vercel.com](https://vercel.com) → **Add New → Project** → import `Pragya-X/Frontend`.
2. Framework preset: Next.js. **Root Directory:** `.` (default — the repo *is* the frontend).
3. **Before the first deploy**, add the environment variable — it is baked into the bundle at build time:
   - `NEXT_PUBLIC_API_URL` = `https://firex-api.onrender.com` (your Step 2 URL)
4. **Deploy.** You get `https://<project>.vercel.app` with free HTTPS.
5. Go back to Render and set `CORS_ORIGINS` + `FRONTEND_URL` to this exact URL, then **Manual Deploy → Deploy latest commit**.
6. Optional custom domain: Vercel → Project → **Domains** → add your domain and create the
   DNS record it shows (`A 76.76.21.21` or `CNAME cname.vercel-dns.com`). If the frontend URL
   changes, update the two backend env vars and redeploy.

## Step 5 — Optional PostGIS migration

`init_db()` creates the schema. For the advanced spatial columns/indexes (generated geometry
columns, SRID 4326, GiST indexes), open **Supabase → SQL Editor** and run
`backend/migrations/001_event_postgis.sql` once, after first boot. The platform works without it
(falls back to WKT columns), but spatial queries are faster with it.

## Step 6 — Verify

- `https://firex-api.onrender.com/api/v1/health` → `{"status":"ok"}`
- `https://firex-api.onrender.com/docs` → Swagger UI loads
- Frontend loads, sign in with the admin from Step 3
- **Live Map** → basemaps render; **Sync FIRMS now** → hotspots appear
- **Live Activity Feed** shows events (confirms SSE works through Render's proxy)
- Trigger an alert → email arrives (confirms SMTP env vars)

## Free-tier caveats (and fixes)

- **Render free spins down after ~15 min without traffic** — the first request then waits ~50 s,
  and SSE/scheduler only run while awake. Workaround: a free uptime ping
  ([cron-job.org](https://cron-job.org) or UptimeRobot) hitting `/api/v1/health` every 10 min
  keeps it awake. This also keeps Supabase's free project from pausing after 7 idle days.
  If the spin-down bothers you, Render Starter ($7/mo) is always-on with zero code changes.
- **Render free has an ephemeral disk**: files in `/app/data` and `/app/uploads` are lost on
  redeploy/restart. Everything of record lives in Postgres, so this only affects uploaded
  report attachments and local cache files.
- **Supabase free**: 500 MB, project pauses after ~7 days with zero queries — the ping above prevents both.
- **Google OAuth is disabled in production** by the config guard (pending PKCE hardening). Email+password only.

## Updating deployments after code changes

The deploy repos are pushed from this monorepo. After committing changes here:

```sh
# Push backend/ to Itz-Npg/Backend (Redeploy on Render picks it up)
git subtree split --prefix=backend -b split-backend && \
git push https://github.com/Itz-Npg/Backend.git split-backend:main --force && \
git branch -D split-backend

# Push frontend/ to Pragya-X/Frontend (Vercel picks it up automatically)
git subtree split --prefix=frontend -b split-frontend && \
git push https://github.com/Pragya-X/Frontend.git split-frontend:main --force && \
git branch -D split-frontend
```

`--force` is needed because the subtree has no shared history with the deploy repos. Pushes to
the deploy repos are content snapshots of `backend/` and `frontend/` only — `.env` files and
secrets stay excluded (gitignored in this monorepo).

## Where this deviates from `docs/DEPLOYMENT_GUIDE.md`

That guide describes the repo's Docker Compose tooling for a single VM. This runbook is the
PaaS equivalent: same production guardrails (`ENV=production` fails closed), same env vars,
same admin bootstrap rule. The only code change needed was making `backend/Dockerfile` honor
`$PORT` (already done — it defaults to 8000 for local Compose).