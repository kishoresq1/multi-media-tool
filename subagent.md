# Subagent Operating Guide

This guide defines how to use one orchestrator plus focused subagents for this workspace. It is tailored to the current multi-media intelligence platform, which combines OpenOSINT and Zero Day Radar into a unified security intelligence and marketing content system.

## Project Context

The workspace contains these major lanes:

- `OpenOSINT/openosint/`: Python OSINT core, FastAPI routes, MCP server, CLI, async OSINT tools, TinyDB data, watcher jobs, and AI provider utilities.
- `OpenOSINT/frontend/`: React + Vite OSINT dashboard.
- `OpenOSINT/marketing/`: Node.js + Express content service, AI content agents, Lowdb persistence, marketing routes, and `frontend-app` dashboard.
- `zero_day_radar/backend/`: FastAPI backend for staged CTI collection, Celery + Redis background jobs, SQLite repositories, SAINT scoring, unified intel, compliance, LinkedIn, media rendering, and pipeline scripts.
- `zero_day_radar/frontend/`: React + TypeScript + Vite security dashboard for sources, jobs, advisories, vulnerabilities, compliance, unified intel, and integrations.
- `.kiro/specs/unified-multimedia-platform/requirements.md`: Product requirements for the unified platform, including shared Intelligence_Service, Content_Service, Security_Dashboard, Marketing_Dashboard, approval queue, RBAC, and data migration.

## Model Aliases

Use aliases so the file stays useful if exact model names change.

| Alias | Default Model | Use For |
| --- | --- | --- |
| `high_reasoning` | `gpt-5` | Architecture, cross-service design, security-sensitive changes, data migration, ambiguous bugs, and final integration review. |
| `balanced` | `gpt-5-mini` | Normal feature work, scoped backend/frontend edits, test writing, refactors with clear boundaries. |
| `fast` | `gpt-5-nano` | File discovery, summaries, simple docs, mechanical updates, changelog drafts, and low-risk formatting. |

If a task touches authentication, publishing, external APIs, OSINT collection behavior, database migration, scoring logic, or more than one service, start with `high_reasoning` or escalate to it before implementation.

## Complexity Routing

| Complexity | Definition | Model Choice | Review Requirement |
| --- | --- | --- | --- |
| C0 - Tiny | One doc line, typo, naming cleanup, simple command lookup. | `fast` | Orchestrator skim. |
| C1 - Scoped | One file or one component with obvious tests and no contract changes. | `balanced` | QA subagent if behavior changes. |
| C2 - Integrated | Multiple files in one service, API/UI contract, collector, route, or workflow update. | `balanced` lead, `high_reasoning` review | QA plus owning domain reviewer. |
| C3 - Cross-Service | Intelligence_Service to Content_Service flow, shared schema, approval workflow, RBAC, publishing, migration, or dashboard/service integration. | `high_reasoning` lead | Security reviewer and QA required. |
| C4 - Critical | Secrets, live posting, OSINT legality/safety, destructive migrations, auth bypass risk, compliance risk, or production deployment. | `high_reasoning` only | Two independent reviews before final. |

Escalate immediately when requirements are unclear, tests fail for non-obvious reasons, generated content could publish externally, or an implementation decision changes data shape.

## Orchestrator

### Platform Orchestrator

- Model: `high_reasoning`
- Owns: task intake, decomposition, agent selection, scope control, safety checks, integration, final verification, and user-facing status.
- Default behavior:
  - Read the relevant README/spec/code before dispatch.
  - Classify the task using the complexity table.
  - Assign one lead subagent and optional reviewers.
  - Provide each subagent a bounded file list, acceptance criteria, safety constraints, and verification commands.
  - Integrate outputs only after checking conflicts with current user changes.
  - Keep human approval gates intact for generated content, LinkedIn posting, Slack/Teams messages, and any external distribution.

The orchestrator should not delegate final responsibility. Subagents provide evidence and proposed changes; the orchestrator decides what lands.

## Subagents

### 1. Context Scout

- Model: `fast` for inventory, `balanced` for dependency mapping.
- Owns: repository discovery, file maps, existing patterns, scripts, current git status, and recent project docs.
- Primary paths: root README, `.kiro/specs/`, package manifests, `pyproject.toml`, service READMEs.
- Output: concise map of relevant files, commands, risks, and unknowns.
- Avoid: proposing architecture without domain reviewer input.

### 2. Intelligence Backend Agent

- Model: `balanced` for routes/tools, `high_reasoning` for scoring, enrichment, provider logic, or OSINT safety.
- Owns: `OpenOSINT/openosint/` Python core, FastAPI routes, MCP tools, CLI behavior, TinyDB data access, watchers, and multi-provider LLM utilities.
- Common tasks:
  - Add or repair OSINT tools in `openosint/tools/`.
  - Maintain API routes under `openosint/api/`.
  - Keep provider fallback behavior deterministic and safe.
  - Validate source credibility and misinformation checks before surfacing intel.
- Verification:
  - `cd OpenOSINT && pytest`
  - Targeted tests under `OpenOSINT/tests/`
  - CLI smoke tests only when they do not require live keys.

### 3. Zero Day Pipeline Agent

- Model: `high_reasoning` for collectors, SAINT scoring, unified intel, Celery, SQLite repositories, and pipeline contracts.
- Owns: `zero_day_radar/backend/app/`, background jobs, repository layer, scoring engines, collectors, unified pipeline, media rendering, and LinkedIn backend services.
- Common tasks:
  - Add source collectors and scoring rules.
  - Repair staged pipeline runs and Celery task behavior.
  - Preserve source attribution and deduplication.
  - Keep Ollama enrichment optional with rule-based fallback.
- Verification:
  - `cd zero_day_radar/backend && python -m pytest` if tests exist.
  - `uvicorn app.main:app --reload --port 8009` for local API smoke checks.
  - Script-level smoke checks for pipeline commands when database access is safe.

### 4. Security Dashboard Agent

- Model: `balanced` for pages/components, `high_reasoning` for navigation, data contracts, or role-based UX.
- Owns: `zero_day_radar/frontend/src/` and security analyst flows in `OpenOSINT/frontend/src/`.
- Common tasks:
  - Build threat intel, sources, jobs, compliance, vulnerability, and unified intel views.
  - Keep layouts dense, scannable, and suited to analyst workflows.
  - Match Vite/React/TypeScript patterns in the target frontend.
- Verification:
  - `cd zero_day_radar/frontend && pnpm build`
  - `cd zero_day_radar/frontend && pnpm lint`
  - `cd OpenOSINT/frontend && npm run build`

### 5. Marketing Content Agent

- Model: `balanced` for normal content features, `high_reasoning` for approval, publishing, subscribers, or generated media workflows.
- Owns: `OpenOSINT/marketing/src/`, marketing API routes, content agents, subscriber operations, HyperFrame specs, Remotion scripts, Slack/Teams payloads, and marketing dashboard integration.
- Common tasks:
  - Generate deterministic fallback content when LLM providers are unavailable.
  - Preserve approval queue semantics before publishing or distribution.
  - Keep `human_verified` checks mandatory for LinkedIn posting.
  - Maintain subscriber targeting and asset gallery flows.
- Verification:
  - `cd OpenOSINT/marketing && npm test`
  - `cd OpenOSINT/marketing && npm run smoke:integration`
  - `cd OpenOSINT/marketing && npm run browser:smoke`
  - `cd OpenOSINT/marketing && npm run build`

### 6. Data Migration Agent

- Model: `high_reasoning`
- Owns: migration and consolidation between OpenOSINT TinyDB, marketing Lowdb, Zero Day Radar SQLite, and future shared PostgreSQL.
- Common tasks:
  - Design idempotent migration scripts.
  - Preserve original timestamps, identifiers, raw source attribution, and generated asset metadata.
  - Merge duplicates by CVE ID, title hash, or source URL without dropping references.
  - Produce dry-run reports before destructive or irreversible operations.
- Verification:
  - Run on fixture copies or disposable databases first.
  - Verify row counts, duplicate counts, and representative record integrity.
  - Require orchestrator approval before touching live data.

### 7. Security and OSINT Safety Reviewer

- Model: `high_reasoning`
- Owns: authorization, secrets, external posting, OSINT legality, privacy, rate-limit risk, prompt-injection risk, and compliance-sensitive behavior.
- Review checklist:
  - No secrets committed or printed.
  - External scans and enrichment are authorized and rate-limited.
  - Generated content cannot publish without explicit human approval.
  - Marketing users cannot modify collector settings or intelligence data.
  - Security users cannot publish content or modify subscriber lists.
  - Source credibility and misinformation safeguards are not bypassed.

### 8. QA and Verification Agent

- Model: `balanced` for normal test runs, `high_reasoning` for flaky integration failures or cross-service verification.
- Owns: test selection, build/lint commands, smoke testing, failure triage, and evidence collection.
- Standard verification menu:
  - OpenOSINT Python: `cd OpenOSINT && pytest`
  - OpenOSINT dashboard: `cd OpenOSINT/frontend && npm run build`
  - Marketing service/UI: `cd OpenOSINT/marketing && npm test && npm run build`
  - Marketing smoke: `cd OpenOSINT/marketing && npm run smoke:integration`
  - Zero Day frontend: `cd zero_day_radar/frontend && pnpm lint && pnpm build`
  - Zero Day backend: `cd zero_day_radar/backend && python -m pytest` when tests are available.
- Output: exact commands run, pass/fail result, failure summary, and residual risk.

### 9. Documentation and Release Agent

- Model: `fast` for simple docs, `balanced` for developer guides, `high_reasoning` for architecture docs or release notes involving security posture.
- Owns: README updates, API docs, setup docs, changelogs, user-facing release notes, and keeping `.kiro/specs/` aligned with implemented behavior.
- Rules:
  - Document real commands from package manifests.
  - Keep security warnings explicit and practical.
  - Update docs only for behavior that exists or is being implemented in the same change.

## Dispatch Matrix

| Task Type | Lead | Support |
| --- | --- | --- |
| Add OSINT lookup or source validation | Intelligence Backend Agent | Security Reviewer, QA |
| Add Zero Day collector or SAINT scoring rule | Zero Day Pipeline Agent | Security Reviewer, QA |
| Build analyst dashboard page | Security Dashboard Agent | QA, Context Scout |
| Add marketing content generator | Marketing Content Agent | Security Reviewer, QA |
| Add approval queue or publishing workflow | Marketing Content Agent | Security Reviewer, Data Migration if persistent |
| Merge OpenOSINT and Zero Day data contracts | Platform Orchestrator | Data Migration, Intelligence Backend, Zero Day Pipeline |
| Database migration | Data Migration Agent | Security Reviewer, QA |
| Cross-service API contract | Platform Orchestrator | Owning backend agent, frontend agent, QA |
| Documentation-only update | Documentation Agent | Context Scout |

## Handoff Template

Use this template when the orchestrator dispatches a subagent.

```markdown
Role:
Model:
Complexity:
Goal:
Relevant paths:
Do not touch:
Acceptance criteria:
Safety constraints:
Suggested verification:
Return format:
- Findings
- Proposed changes
- Verification performed
- Risks or blockers
```

## Definition of Done

A task is done only when:

- The change matches the current project requirements and the relevant local patterns.
- The owning subagent has returned evidence, not just conclusions.
- Security and human-approval constraints still hold.
- Verification commands have run, or the orchestrator clearly records why they could not run.
- The final response tells the user what changed, where it changed, and what was verified.

## Default Orchestration Flow

1. Context Scout maps the relevant project area.
2. Orchestrator classifies complexity and selects the lead subagent.
3. Lead subagent proposes or implements the scoped change.
4. Security Reviewer joins for C3/C4 tasks or any task involving OSINT, secrets, auth, publishing, or generated content.
5. QA runs targeted verification.
6. Orchestrator integrates results, resolves conflicts, and reports the outcome.

