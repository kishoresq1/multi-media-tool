# =============================================================================
# KEYWORD PRIORITY (used by scrapers, APIs, and table inserts)
# -----------------------------------------------------------------------------
# 1. PRIMARY  → SEARCH_KEYWORDS below — used FIRST for all scraper/API search
#               and filtering before inserting into SQLite tables.
# 2. FALLBACK → VENDOR_KEYWORDS + VULNERABILITY_KEYWORDS + THREAT_ACTIVITY_KEYWORDS
#               — used ONLY when primary SEARCH_KEYWORDS produce no matches.
# =============================================================================

# --- FALLBACK (use only when SEARCH_KEYWORDS find nothing) -------------------

VENDOR_KEYWORDS: list[str] = [
    "Microsoft",
    "Cisco",
    "Fortinet",
    "FortiOS",
    "FortiGate",
    "Palo Alto",
    "PAN-OS",
    "Prisma",
    "GlobalProtect",
    "Ivanti",
    "Connect Secure",
    "EPMM",
    "VMware",
    "ESXi",
    "vCenter",
    "Citrix",
    "NetScaler",
    "ADC",
    "Juniper",
    "JunOS",
    "SRX",
    "Google Chrome",
    "Adobe",
    "Apple",
    "SAP",
    "Oracle",
    "Atlassian",
    "Jira",
    "Confluence",
    "GitLab",
    "ManageEngine",
    "Zoho",
    "AWS",
    "Azure",
    "Google Cloud",
    "Kubernetes",
    "Docker",
    "HashiCorp",
    "Vault",
    "Consul",
]

VULNERABILITY_KEYWORDS: list[str] = [
    "vulnerability",
    "critical vulnerability",
    "security flaw",
    "security issue",
    "zero day",
    "0day",
    "exploit",
    "exploitation",
    "actively exploited",
    "in the wild",
    "authentication bypass",
    "auth bypass",
    "login bypass",
    "remote code execution",
    "RCE",
    "arbitrary code execution",
    "privilege escalation",
    "privesc",
    "command injection",
    "code injection",
    "SQL injection",
    "SQLi",
    "cross site scripting",
    "XSS",
    "server side request forgery",
    "SSRF",
    "path traversal",
    "directory traversal",
    "buffer overflow",
    "memory corruption",
    "deserialization",
    "sandbox escape",
    "container escape",
    "information disclosure",
    "credential theft",
    "account takeover",
    "bypass",
]

THREAT_ACTIVITY_KEYWORDS: list[str] = [
    "PoC",
    "proof of concept",
    "exploit released",
    "working exploit",
    "public exploit",
    "mass scanning",
    "internet scanning",
    "campaign",
    "ransomware",
    "data breach",
    "leaked database",
    "compromised",
    "attacked",
    "targeted",
    "threat actor",
    "APT",
    "botnet",
    "malware",
    "backdoor",
    "webshell",
    "IOC",
    "indicator of compromise",
]

PRODUCT_SEARCH_TEMPLATES: list[str] = [
    "{product} vulnerability",
    "{product} exploit",
    "{product} authentication bypass",
    "{product} RCE",
    "{product} PoC",
    "{product} actively exploited",
    "{product} zero day",
]

# --- PRIMARY (scrapers + APIs use these FIRST) --------------------------------

SEARCH_KEYWORDS: list[str] = [
    "authentication bypass",
    "auth bypass",
    "RCE",
    "remote code execution",
    "privilege escalation",
    "exploit",
    "PoC",
    "proof of concept",
    "zero day",
    "0day",
    "actively exploited",
    "critical vulnerability",
    "security flaw",
    "in the wild",
    "ransomware",
    "data breach",
    "credential theft",
    "account takeover",
]

# Combined fallback list (vendor + vuln + threat) — do not use before primary
FALLBACK_KEYWORDS: list[str] = list(dict.fromkeys(
    VENDOR_KEYWORDS + VULNERABILITY_KEYWORDS + THREAT_ACTIVITY_KEYWORDS
))
