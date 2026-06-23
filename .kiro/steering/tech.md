# Tech Stack

## Intelligence Service (`intelligence-service/`)
- **Language**: Python 3.10+
- **API framework**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy 2.0 async (`AsyncSession`, `Mapped[type]` / `mapped_column()` style — no legacy `Column()`)
- **DB migrations**: Alembic
- **Background jobs**: Celery (worker + beat) with Redis broker
- **Config**: pydantic-settings with `ZDR_` env prefix; optional keys degrade gracefully
- **HTTP clients**: httpx (async), aiohttp
- **Testing**: pytest + pytest-asyncio, Hypothesis (property-based tests)
- **Linting**: Ruff (`line-length = 100`, select E/F/I/W)
- **Local LLM**: Ollama (`llama3.2`) for intel enrichment
- **Multi-provider AI**: Anthropic → OpenAI → OpenRouter → Gemini (auto-detected from env keys)

## Content Service (`content-service/`)
- **Language**: TypeScript (Node.js 18+)
- **API framework**: Express
- **ORM**: Prisma (PostgreSQL)
- **Testing**: Vitest + fast-check (property-based tests)
- **AI**: `@anthropic-ai/sdk` with deterministic template fallbacks
- **Video**: Remotion
- **Email**: nodemailer / Resend
- **Module system**: ES modules (`"type": "module"`)

## React Dashboards (`security-dashboard/`, `marketing-dashboard/`)
- **Framework**: React 18/19 + TypeScript
- **Build tool**: Vite
- **Styling**: TailwindCSS
- **Data fetching**: React Query
- **Routing**: React Router v7
- **Icons**: lucide-react
- **Testing**: Vitest + Testing Library

## Shared Infrastructure
- **Database**: PostgreSQL 16 (target), SQLite (zero_day_radar legacy), TinyDB/Lowdb (OpenOSINT legacy)
- **Cache / message broker**: Redis 7
- **Reverse proxy**: Nginx 1.27 (routes by path prefix)
- **Container orchestration**: Docker Compose (8 services)
- **Auth**: JWT (access token 1h, refresh token 7d); shared `JWT_SECRET` across services

## Environment Variables
All secrets live in `.env` at the repo root. See `.env.example` for the full list.
Key groups: `POSTGRES_*`, `REDIS_*`, `JWT_SECRET`, `ANTHROPIC/OPENAI/OPENROUTER/GEMINI_API_KEY`, `LINKEDIN_CLIENT_*`, `SLACK/TEAMS_WEBHOOK_URL`, `OLLAMA_*`.

---

## Common Commands

### Full platform
```bash
cp .env.example .env          # fill in secrets first
docker compose up             # start all 8 services
docker compose up intelligence-service content-service nginx  # subset
```

### Intelligence Service (local dev)
```bash
cd intelligence-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery (separate terminals)
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info

# Tests
pytest
pytest --hypothesis-seed=0    # deterministic property tests
```

### Content Service (local dev)
```bash
cd content-service
npm install
npx prisma migrate dev        # apply DB migrations
npx prisma generate           # regenerate Prisma client
npm run dev                   # ts-node / tsx watch

# Tests
npm test                      # vitest run
npm run test:watch            # vitest watch
```

### Security / Marketing Dashboards
```bash
cd security-dashboard   # or marketing-dashboard
npm install
npm run dev             # Vite dev server
npm run build           # tsc + vite build → dist/
npm run lint            # eslint
npm run preview         # preview production build
```

### Zero Day Radar (legacy, standalone)
```bash
cd zero_day_radar/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8009

# Background workers
./scripts/start_background.sh      # all-in-one
./scripts/start_celery_worker.sh
./scripts/start_celery_beat.sh

# Manual pipeline triggers
python -m scripts.run_unified_pipeline
python -m scripts.refresh_intel
python -m scripts.refresh_vulnerabilities
```

```bash
cd zero_day_radar/frontend
pnpm install
pnpm dev          # :5173
pnpm build        # tsc -b && vite build
pnpm lint
```

### OpenOSINT (legacy, standalone)
```bash
cd OpenOSINT
pip install -e ".[all]"
uvicorn openosint.api.main:app --reload --port 8000
openosint                     # interactive REPL
pytest tests/

cd marketing
npm install
npm run dev:api               # Express API :3002
npm run dev:ui                # Vite frontend :5174
npm test                      # vitest run
```
