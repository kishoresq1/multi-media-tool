# Project Structure

## Top-Level Layout

```
multi-media-tool/
├── docker-compose.yml          # 8-service orchestration (postgres, redis, ollama, intelligence-service, content-service, celery-worker, celery-beat, nginx)
├── nginx/default.conf          # Path-based routing: /api/v1/intel/* → :8000, /api/v1/content/* → :3000, /security/ and /marketing/ → static bundles
├── .env.example                # All env vars documented; copy to .env before running
├── migrations/                 # SQL init scripts mounted into postgres container
│
├── intelligence-service/       # Python/FastAPI — migration target for Zero Day Radar
├── content-service/            # Node.js/TypeScript — migration target for OpenOSINT marketing
├── security-dashboard/         # React SPA — built output served at /security/
├── marketing-dashboard/        # React SPA — built output served at /marketing/
│
├── zero_day_radar/             # Legacy CTI product (fully functional, standalone)
├── OpenOSINT/                  # Legacy OSINT + marketing product (fully functional, standalone)
└── .kiro/specs/unified-multimedia-platform/  # Migration spec (requirements, design, tasks)
```

## Intelligence Service (`intelligence-service/`)

```
intelligence-service/
├── app/
│   ├── main.py                 # FastAPI app, lifespan, CORS, router registration
│   ├── api/                    # FastAPI routers — one file per domain
│   ├── collectors/             # One class per source; all extend BaseCollector
│   │   └── base.py             # Abstract BaseCollector + CollectorResult + _make_signal()
│   ├── config/
│   │   └── settings.py         # pydantic-settings Settings singleton (ZDR_ prefix)
│   ├── db/
│   │   ├── database.py         # AsyncEngine, AsyncSession, init_db()
│   │   ├── models.py           # SQLAlchemy 2.0 ORM models (Mapped[type] style)
│   │   └── *_repository.py     # One repository class per table
│   ├── models/
│   │   └── schemas.py          # Pydantic v2 request/response schemas
│   ├── processors/             # SAINT scoring, classification, enrichment (pure functions)
│   ├── services/               # Domain services — orchestrate collectors + repositories
│   └── worker/
│       ├── celery_app.py       # Celery app instance
│       ├── tasks.py            # @app.task definitions (one per pipeline)
│       └── jobs.py             # Job management helpers
├── scripts/                    # Standalone pipeline runners + shell scripts
├── alembic.ini
└── requirements.txt
```

## Content Service (`content-service/`)

```
content-service/
├── prisma/
│   ├── schema.prisma           # Tables: content_assets, campaigns, subscribers, linkedin_oauth_tokens, approval_queue_history
│   └── migrations/
├── src/
│   ├── db/prisma.ts            # Prisma client singleton
│   ├── api/                    # Express routers
│   ├── agents/                 # AI content generators (one per content type)
│   └── middleware/             # JWT validation, requireMarketingTeam guard
└── package.json
```

## React Dashboards

```
security-dashboard/   (or marketing-dashboard/)
├── src/
│   ├── pages/                  # One component per route
│   ├── components/             # Shared UI components
│   ├── api/                    # API client module (JWT attach interceptor, 401 redirect)
│   └── lib/                    # Utility functions
├── index.html
├── vite.config.ts
├── tsconfig.app.json
└── package.json
```

## Zero Day Radar Legacy (`zero_day_radar/`)

```
zero_day_radar/
├── backend/
│   ├── app/
│   │   ├── api/                # FastAPI routers (routes, unified, linkedin, linkedin_auth, jobs)
│   │   ├── collectors/         # 16 collectors (rss, scraper, vendor_advisory, social, compliance, etc.)
│   │   ├── config/             # settings.py, keywords, source registry, scoring configs
│   │   ├── db/                 # SQLAlchemy models + per-table repositories
│   │   ├── models/             # Pydantic schemas
│   │   ├── processors/         # SAINT threat + compliance scoring engines, classifier
│   │   ├── services/           # Pipeline orchestration, search services
│   │   └── worker/             # Celery app, tasks, async runner
│   ├── scripts/                # Shell scripts + standalone Python runners
│   ├── data/                   # SQLite .db files
│   └── requirements.txt
└── frontend/
    └── src/
        ├── pages/              # 16 page components
        ├── components/         # Layout, Sidebar, shared UI
        ├── api/client.ts       # Fetch/Axios client (proxied via Vite to :8009)
        └── lib/                # Formatting + LinkedIn helpers
```

## OpenOSINT Legacy (`OpenOSINT/`)

```
OpenOSINT/
├── openosint/                  # Python package (pip install -e ".[all]")
│   ├── tools/                  # 23 async OSINT tool functions (one file each)
│   ├── api/
│   │   ├── main.py             # FastAPI app + CORS
│   │   └── routes/             # intel.py, companies.py, employees.py, tracker.py
│   ├── data/                   # TinyDB store.py + seed.py
│   ├── watcher/                # APScheduler background poller (60s interval)
│   ├── llm.py                  # Multi-provider AI abstraction
│   ├── mcp_server.py           # MCP server (all 23 tools)
│   └── cli.py                  # Click CLI entry point
├── marketing/
│   ├── src/
│   │   ├── api/                # Express REST server (:3002)
│   │   └── agents/             # AI content generators
│   ├── frontend-app/           # React + Vite marketing dashboard (:5174)
│   └── data/db.json            # Lowdb persistence
├── frontend/                   # React OSINT dashboard (:5173)
├── tests/                      # pytest suite
└── pyproject.toml              # Package definition, extras, ruff + pytest config
```

## Nginx Routing

| Path prefix | Upstream |
|---|---|
| `/api/v1/intel/*` | `intelligence-service:8000` |
| `/auth/*` | `intelligence-service:8000` |
| `/api/v1/content/*` | `content-service:3000` |
| `/security/` | Static files from `security-dashboard/dist` |
| `/marketing/` | Static files from `marketing-dashboard/dist` |
| `/` | Redirects to `/security/` |

## Key Conventions

- **New intelligence collectors** go in `intelligence-service/app/collectors/`, extending `BaseCollector` and implementing `collect()`. Register in the source registry.
- **New API endpoints** go in `intelligence-service/app/api/` (Python) or `content-service/src/api/` (Node.js). All routes are prefixed `/api/v1/`.
- **Database models** (intelligence-service): add to `app/db/models.py` + create a matching repository in `app/db/`. Always use `Mapped[type]` / `mapped_column()` — no legacy `Column()`.
- **Database models** (content-service): edit `prisma/schema.prisma`, then run `npx prisma migrate dev`.
- **Environment config**: never hardcode secrets. Add new vars to `.env.example` and read via `settings` (Python) or `process.env` (Node.js).
- **Content hash deduplication**: all intel tables include a `content_hash` unique constraint (SHA-256 of normalized title + content). Always compute and check before inserting.
