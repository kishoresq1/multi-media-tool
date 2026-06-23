# Combined Repository Layout

The two original projects are now copied into one top-level monorepo layout. The original `OpenOSINT/` and `zero_day_radar/` folders are kept as compatibility references until the unified folders are fully verified.

## Unified Folders

- `intelligence-service/`: Python/FastAPI intelligence backend based on Zero Day Radar, with OpenOSINT's Python package copied under `intelligence-service/openosint/` for OSINT tools and customer intelligence reuse.
- `content-service/`: Node.js/Express content backend based on OpenOSINT marketing automation.
- `security-dashboard/`: React/TypeScript dashboard based on Zero Day Radar frontend.
- `marketing-dashboard/`: React/Vite dashboard based on OpenOSINT marketing frontend.
- `nginx/`: reverse proxy routes for `/api/v1/intel`, `/api/v1/content`, `/security`, and `/marketing`.
- `migrations/`: reserved for cross-project data migration utilities.

## Source Mapping

| Original | Combined Target |
| --- | --- |
| `zero_day_radar/backend/` | `intelligence-service/` |
| `OpenOSINT/openosint/` | `intelligence-service/openosint/` |
| `OpenOSINT/marketing/` | `content-service/` |
| `zero_day_radar/frontend/` | `security-dashboard/` |
| `OpenOSINT/marketing/frontend-app/` | `marketing-dashboard/` |

## Next Step

Wire the copied services to the unified API prefixes and shared contracts, then remove old source roots only after the combined services pass their build/test checks.

