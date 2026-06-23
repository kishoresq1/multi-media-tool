# ⚡ SQ1 OSINT Platform — Team Quickref
### Forking: github.com/OpenOSINT/OpenOSINT | Start: 11:40 | Deadline: 14:40

---

## FIRST THING — BOTH RUN THIS

```bash
git clone https://github.com/OpenOSINT/OpenOSINT.git sq1-openosint
cd sq1-openosint
```
Person 1 works inside `sq1-openosint/` | Person 2 creates `sq1-openosint/marketing/`

---

## WHAT OPENOSINT ALREADY GIVES YOU (REUSE, DON'T REBUILD)

| Tool | Person 1 Uses It For |
|------|---------------------|
| `search_breach` | Employee dark web scan ✅ |
| `search_email` | Employee footprint (holehe) ✅ |
| `search_username` | Employee account tracking ✅ |
| `search_paste` | Paste/leak detection ✅ |
| `search_domain` | Company subdomains ✅ |
| `search_whois` | Company registration ✅ |
| `search_ip` | Company infrastructure ✅ |
| `generate_dorks` | Company exposure ✅ |

Person 2 — you don't touch any of these. You call Person 1's REST API.

---

## WHO BUILDS WHAT

| | Person 1 (OSINT Core) | Person 2 (Marketing) |
|--|----------------------|---------------------|
| **Language** | Python + React | Node.js + React |
| **Lives in** | `openosint/` + `frontend/` | `marketing/` |
| **API port** | FastAPI → 8000 | Express → 3002 |
| **UI port** | Vite → 5173 | Vite → 5174 |
| **Prompt file** | `PERSON1_OSINT_MODULE.md` | `PERSON2_MARKETING_MODULE.md` |

---

## TIMELINE

```
11:40 → Both clone repo | Both read their prompt | Both start Phase 1 setup simultaneously
11:55 → Setup done, core dev starts
12:35 → P1: Python tools done | P2: Agents (email/hyperframe/slack) done
13:05 → P1: FastAPI routes up | P2: Express routes up
13:45 → P1: React dashboard done | P2: Frontend done
13:45 → Integration: P2 switches from mock → live API
14:05 → Both: seed data + polish
14:30 → Final test, push to repo
14:40 → DONE
```

---

## CHECKPOINTS

- **12:00** — Both: "Is your dev server running?" quick message
- **13:00** — P1 shares `API_INTEGRATION.md` with endpoints for P2
- **13:45** — P2 runs: `curl http://localhost:8000/api/intel/latest` — should get JSON back
- **14:15** — Full demo run: Intel arrives → P2 queue shows it → click "Create Visual" → HyperFrame renders

---

## REPO MERGE STRUCTURE

```
sq1-openosint/
├── openosint/        ← P1: extended Python MCP tools
├── frontend/         ← P1: React OSINT dashboard (port 5173)
├── marketing/        ← P2: Marketing module (port 5174)
├── ROADMAP.md        ← Both contribute to this (combine at merge)
├── TODO.md           ← Both contribute to this
└── README.md         ← Update together at the end
```

Push to same repo at the end: `git add . && git commit -m "hackathon: sq1 platform" && git push`

---

## TOKEN BUDGET

| Module | Build | Runtime/use |
|--------|-------|-------------|
| OSINT Core (P1) | ~133K | ~2-8K per scan |
| Marketing (P2) | ~142K | ~1-2K per asset |
| **Total** | **~275K** | **~5K per cycle** |

**Combined estimated build cost: ~$3-4**

---

## IF SOMETHING BREAKS

- **P2**: `USE_MOCK = true` is your safety net — always have it available
- **P1**: HIBP rate limit → `asyncio.sleep(1.6)` between bulk email calls  
- **Both**: Claude JSON parse fails → `.replace(/\`\`\`json|\`\`\`/g, '').trim()` before `JSON.parse()`
- **P1**: NVD API slow → cache last response in TinyDB, return cache if < 5 min old
- **P2**: html2canvas breaks → just screenshot the div for demo

---

*Each person: paste your MD file into Claude and say: "Start building step by step, beginning with Phase 1 setup."*
