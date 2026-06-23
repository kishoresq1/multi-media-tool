"""
Repair a corrupted TinyDB JSON by extracting companies/employees
and rebuilding the file without the corrupted intel table.
"""
import json
import os
import shutil
from datetime import datetime, timezone

DB_PATH = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), ".sq1-osint", "db.json")
BACKUP = DB_PATH + ".bak"

print(f"DB: {DB_PATH}")

# ------ back up the corrupted file ------
shutil.copy2(DB_PATH, BACKUP)
print(f"Backup saved to {BACKUP}")

# ------ try to load; if fails, read raw to extract good tables ------
try:
    with open(DB_PATH, encoding="utf-8") as f:
        data = json.load(f)
    print("DB loaded cleanly (no repair needed).")
except json.JSONDecodeError as exc:
    print(f"JSON error: {exc}")
    # Read raw content up to error position and try to salvage tables
    with open(DB_PATH, encoding="utf-8", errors="replace") as f:
        raw = f.read()

    # Try to parse just the companies and employees tables by extracting them
    # TinyDB format: {"companies": {...}, "employees": {...}, "intel": {...}}
    data = {"companies": {}, "employees": {}, "intel": {}}

    # Use a fresh parse of just the first portion before intel gets corrupted
    # Attempt partial recovery: find the start of "intel" key and truncate before it
    import re
    # Find positions of major table keys
    companies_match = re.search(r'"companies"\s*:\s*\{', raw)
    employees_match = re.search(r'"employees"\s*:\s*\{', raw)
    intel_match = re.search(r'"intel"\s*:\s*\{', raw)

    if companies_match and employees_match:
        print("Attempting to salvage companies and employees tables...")
        # Try loading with a truncated payload — just companies + employees + empty intel
        # Find where 'intel' starts and replace everything from there with empty table + closing brace
        intel_start = intel_match.start() if intel_match else len(raw) - 1
        truncated = raw[:intel_start].rstrip().rstrip(",") + ', "intel": {}}'
        try:
            data = json.loads(truncated)
            print(f"Salvaged: {len(data.get('companies', {}))} companies, {len(data.get('employees', {}))} employees")
        except json.JSONDecodeError as e2:
            print(f"Salvage failed: {e2}")
            data = {"companies": {}, "employees": {}, "intel": {}}

# Always clear the intel table — it will be repopulated by the watcher
data["intel"] = {}

# Write the repaired DB
with open(DB_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)

print(f"Repaired DB written.")
print(f"  companies: {len(data.get('companies', {}))} rows")
print(f"  employees: {len(data.get('employees', {}))} rows")
print(f"  intel: 0 rows (cleared; watcher will repopulate)")
print("\nNow restart the OSINT API (uvicorn) so the watcher repopulates intel from live feeds.")
