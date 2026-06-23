# Zero Day Radar — Frontend

React + Vite + TypeScript UI for the CTI hunter backend.

## Stack

- **pnpm** — package manager
- **Vite** — dev server & build
- **React Router** — navigation
- **Lucide** — icons

## Quick start

```bash
cd frontend
pnpm install
cp .env.example .env

# Terminal 1 — backend API
cd ../backend && uvicorn app.main:app --reload --port 8009

# Terminal 2 — frontend
pnpm dev
```

Open http://localhost:5173

API requests proxy to `http://127.0.0.1:8009` via Vite (`/api` → backend).

## Pages

| Route | Menu |
|-------|------|
| `/` | Dashboard |
| `/sources` | Sources list |
| `/sources/configure` | Source configuration |
| `/integrations` | Tools & integrations (Twitter, LinkedIn, Instagram, Teams, Slack, Mail) |

## Build

```bash
pnpm build
pnpm preview
```
