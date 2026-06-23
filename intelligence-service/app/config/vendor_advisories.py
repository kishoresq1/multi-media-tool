"""Vendor advisory source registry for Step 2 advisory search."""

VENDOR_ADVISORY_SOURCE_IDS: list[str] = [
    "msrc",
    "cisco_advisories",
    "fortinet_psirt",
    "palo_alto_advisories",
    "vmware_advisories",
    "ivanti_advisories",
    "citrix_bulletins",
    "juniper_advisories",
    "chrome_releases",
    "adobe_security",
    "apple_security",
    "oracle_security",
    "sap_security",
    "atlassian_security",
    "gitlab_security",
    "manageengine_security",
    "aws_security",
    "gcp_security",
    "docker_security",
    "hashicorp_security",
]

# Map source ID → vendor names for keyword-less matching on official feeds
SOURCE_VENDOR_MAP: dict[str, list[str]] = {
    "msrc": ["Microsoft", "Azure", "Windows"],
    "cisco_advisories": ["Cisco"],
    "fortinet_psirt": ["Fortinet", "FortiOS", "FortiGate"],
    "palo_alto_advisories": ["Palo Alto", "PAN-OS", "GlobalProtect", "Prisma"],
    "vmware_advisories": ["VMware", "ESXi", "vCenter", "Broadcom"],
    "ivanti_advisories": ["Ivanti", "Connect Secure", "EPMM"],
    "citrix_bulletins": ["Citrix", "NetScaler", "ADC"],
    "juniper_advisories": ["Juniper", "JunOS", "SRX"],
    "chrome_releases": ["Google Chrome", "Chrome"],
    "adobe_security": ["Adobe"],
    "apple_security": ["Apple"],
    "oracle_security": ["Oracle"],
    "sap_security": ["SAP"],
    "atlassian_security": ["Atlassian", "Jira", "Confluence"],
    "gitlab_security": ["GitLab"],
    "manageengine_security": ["ManageEngine", "Zoho"],
    "aws_security": ["AWS", "Amazon"],
    "gcp_security": ["Google Cloud", "GCP"],
    "docker_security": ["Docker"],
    "hashicorp_security": ["HashiCorp", "Vault", "Consul"],
}

# Extra feed URLs for sources missing or needing override
ADVISORY_FEED_OVERRIDES: dict[str, str] = {
    "hashicorp_security": "https://discuss.hashicorp.com/c/security/security-announcements.rss",
    "docker_security": "https://docs.docker.com/security/security-announcements/index.xml",
}
