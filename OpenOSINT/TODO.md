# SQ1 OSINT Core — TODO

## 🔴 P0 — Must Ship (MVP)

- [ ] Clone + install deps (Phase 1)
- [ ] search_intel.py — NVD + CISA feeds
- [ ] validate_source.py — whitelist check
- [ ] detect_misinfo.py — Claude call
- [ ] scan_company.py — orchestrates existing tools
- [ ] FastAPI main.py + all 4 route files
- [ ] TinyDB store.py
- [ ] Main Dashboard UI (stats + intel feed)
- [ ] Company List + Drilldown UI
- [ ] Employee Leak Table UI
- [ ] /api/intel/latest for Person 2
- [ ] API_INTEGRATION.md

## 🟡 P1 — Should Ship If Time

- [ ] track_post.py — Reddit tracker
- [ ] Post Tracker UI component
- [ ] Background web watcher (APScheduler)
- [ ] Extend mcp_server.py with new tools
- [ ] Extend cli.py with new commands

## 🟢 P2 — Nice to Have

- [ ] Animated threat score gauge
- [ ] Real-time poll for new intel
- [ ] Company scan history timeline
- [ ] Export intel as JSON
