export const MOCK_INTEL = [
  {
    id: 'intel-001',
    title: 'Critical RCE in Apache HTTP Server 2.4.x (CVE-2024-38476)',
    classification: 'VULNERABILITY',
    severity: 'CRITICAL',
    summary:
      'Remote code execution vulnerability affects Apache HTTP Server versions below 2.4.62. Active exploitation has been observed. Patch immediately.',
    cveIds: ['CVE-2024-38476'],
    tags: ['rce', 'apache', 'web-server', 'enterprise'],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false,
    usedInMarketing: false,
    source: 'mock'
  },
  {
    id: 'intel-002',
    title: 'GDPR AI Data Pipeline Audit Required by November 30',
    classification: 'COMPLIANCE',
    severity: 'HIGH',
    summary:
      'New EU guidance asks companies to audit AI-processed data for cross-border transfer risk and retention policy gaps.',
    cveIds: [],
    tags: ['gdpr', 'compliance', 'ai', 'eu', 'data-privacy'],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false,
    usedInMarketing: false,
    source: 'mock'
  },
  {
    id: 'intel-003',
    title: 'Viral Claim: Major Bank Lost $4B in Crypto Hack',
    classification: 'MISINFORMATION',
    severity: 'INFO',
    summary:
      'A claim circulating on social media alleges a major financial institution suffered a $4B crypto theft. No credible source confirms it.',
    cveIds: [],
    tags: ['misinformation', 'crypto', 'financial'],
    timestamp: new Date().toISOString(),
    sourceVerified: false,
    isMisinformation: true,
    usedInMarketing: false,
    source: 'mock'
  },
  {
    id: 'intel-004',
    title: '73 Million Customer Records Exposed on Dark Web Forum',
    classification: 'BREACH',
    severity: 'CRITICAL',
    summary:
      'A database containing customer PII appeared on a cybercrime forum, including account numbers and encrypted passcodes.',
    cveIds: [],
    tags: ['breach', 'telecom', 'pii', 'dark-web'],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false,
    usedInMarketing: false,
    source: 'mock'
  },
  {
    id: 'intel-005',
    title: 'Ransomware Group Targeting Healthcare Sector',
    classification: 'THREAT',
    severity: 'HIGH',
    summary:
      'Ransomware operators are actively targeting hospitals and healthcare networks with credential theft and extortion playbooks.',
    cveIds: [],
    tags: ['ransomware', 'healthcare', 'fbi'],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false,
    usedInMarketing: false,
    source: 'mock'
  }
];
