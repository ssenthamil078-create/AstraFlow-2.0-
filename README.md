# AstraFlow — deploy layout

```
astraflow-deploy/
├── backend/    FastAPI app -> deploy to Render
├── frontend/   Vite + React app -> deploy to Vercel
└── render.yaml Optional Render Blueprint (one-click backend setup)
```

Push this whole folder as one Git repo (or two separate repos, if you'd
rather) — both platforms let you point at a subfolder as the project root.

## 1. Backend on Render

1. New Web Service → connect the repo → set **Root Directory** to `backend`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (already captured in `backend/Procfile` and `render.yaml` if you use the
   Blueprint flow instead of manual setup).
4. Add environment variables (see `backend/.env.example` for the full list
   with explanations) — at minimum:
   - `ASTRAFLOW_ENV=production`
   - `ASTRAFLOW_SECRET_KEY` — generate with `openssl rand -hex 32`
   - `ASTRAFLOW_EXPOSE_VERIFICATION_TOKEN=false`
   - `ASTRAFLOW_DATABASE_URL` — your Postgres/Supabase connection string
     (Render's disk is ephemeral, so SQLite will not persist between
     deploys/restarts — don't use it in production)
   - `GEMINI_API_KEY`
   - `ASTRAFLOW_CORS_ORIGINS` — your Vercel URL (add after step 2, then
     redeploy)
   - `ASTRAFLOW_FRONTEND_BASE_URL` — same Vercel URL, used in email links
5. Deploy. Your API will be at `https://<your-service>.onrender.com`.

## 2. Frontend on Vercel

1. New Project → connect the repo → set **Root Directory** to `frontend`.
2. Framework preset: Vite (auto-detected). Build command `vite build`,
   output directory `dist` (both are Vite defaults, no changes needed).
3. Add environment variable:
   - `VITE_API_BASE_URL=https://<your-service>.onrender.com` (no trailing
     slash) — the exact URL from step 1.5 above.
4. Deploy. `frontend/vercel.json` is already set up to rewrite all routes
   to `index.html`, so client-side routing (react-router) won't 404 on a
   hard refresh or direct link.
5. Once you have the Vercel URL, go back to Render and set
   `ASTRAFLOW_CORS_ORIGINS` / `ASTRAFLOW_FRONTEND_BASE_URL` to it, then
   redeploy the backend so CORS and email links point at the right place.

## What changed from the original zip

- Split `astraflow_phase6_auth/astraflow/backend` and `.../untitled` into
  top-level `backend/` and `frontend/` folders.
- Dropped `venv/`, `.venv/`, `node_modules/`, `dist/`, `__pycache__/`,
  `.pytest_cache/`, `.git/`, and the local `astraflow.db` SQLite file —
  none of these belong in a deploy repo.
- **Removed real committed secrets** — the original `backend/.env` had a
  live Supabase Postgres password and a Gemini API key checked into the
  zip, and `untitled/.env` had the same Gemini key. Both `.env` files
  were dropped and replaced with `.env.example` templates. **Rotate that
  Supabase DB password and the Gemini key before deploying** — they were
  sitting in a file that already left your machine.
- Removed `frontend/server.ts`, a leftover standalone Express server that
  isn't referenced by any `package.json` script and duplicates the real
  FastAPI backend (its own in-memory data, direct Gemini calls, a
  hardcoded demo user) — dead code, not part of the actual app.
- `frontend/src/services/api.ts` now prepends `VITE_API_BASE_URL` to every
  request instead of assuming same-origin `/api/...` paths, since the
  frontend and backend are on different domains once split.
- `backend/app/main.py` now reads allowed CORS origins from
  `ASTRAFLOW_CORS_ORIGINS` (comma-separated) instead of hardcoding `"*"`.
- Added `backend/Procfile`, `render.yaml`, and `frontend/vercel.json`.
