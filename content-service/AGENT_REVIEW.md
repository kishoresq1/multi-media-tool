# SQ1 Marketing Module - Agent Review Lanes

This module follows `Agent_usage.MD` as a coordination guide, not as an in-app multi-agent runtime.

## Review Lanes Used

- Repository Analyst: confirmed `marketing/` owns the Node/React module and avoids `openosint/` plus existing `frontend/`.
- API Analyzer: checked the Person 1 HTTP contract for `/health`, `/api/intel/unmarketed`, and `/api/intel/{id}/mark-used`.
- Test Engineer: added backend and frontend tests for mock fallback, generation flows, subscriber CRUD, alert payloads, contract fields, and mark-used behavior.
- Code Reviewer: checked maintainability risks around generated state, unsafe HTML, UI action wiring, and route behavior.
- Security Auditor: reviewed secrets/webhook handling, PII exposure, LLM output safety, and optional API-token protection.
- Documentation Writer: kept Marketing status in `ROADMAP.md`, `TODO.md`, and this review-lane note.

## Conflict Rules

- Marketing code must stay inside `marketing/`.
- Person 1 code in `openosint/` and the existing `frontend/` should only be read for HTTP contract verification.
- Marketing integration with Person 1 must use HTTP, never direct imports from `openosint/`.
- Mock mode remains the default so Marketing work is not blocked by Person 1 runtime availability.
