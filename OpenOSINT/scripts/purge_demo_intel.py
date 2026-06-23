"""One-time script: purge seeded demo intel items from the DB."""
from dotenv import load_dotenv
load_dotenv()

from openosint.data.store import purge_seeded_intel, get_intel_latest, get_intel_stats

removed = purge_seeded_intel()
print(f"Purged {removed} demo intel items (no sourceUrl key).")

stats = get_intel_stats()
print(f"DB now: {stats['total']} total intel items")
print(f"  By classification: {stats['by_classification']}")
print(f"  By severity: {stats['by_severity']}")
print(f"  Unmarketed: {stats['unmarketed']}")

items = get_intel_latest(limit=5)
print("\nLatest 5 items:")
for item in items:
    src = item.get("sourceName", item.get("source", "?"))
    print(f"  [{item['severity']}] {item['title'][:65]} | from={src}")
