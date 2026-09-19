# ForgeSight Web — Investigation Workspace

## Local development

```bash
cp .env.example .env
npm install
npm run dev
```

Requires the Phase 7 FastAPI backend running (default `http://localhost:8000`).
The Vite dev server proxies `/api` to it, so CORS is not an issue locally.

## Build

```bash
npm run build
```

Produces a static `dist/` directory. Serve it behind the same reverse proxy
as the API, or with any static file server (e.g. `npx serve dist`, nginx).
Set `VITE_API_BASE_URL` at build time to point at the deployed API.

## Tests

```bash
npm test
```