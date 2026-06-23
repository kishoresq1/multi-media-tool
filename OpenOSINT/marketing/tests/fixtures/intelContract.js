export const PERSON1_INTEL_CONTRACT_ITEM = {
  id: 'live-contract-1',
  title: 'Contract Threat Item',
  classification: 'THREAT',
  severity: 'HIGH',
  summary: 'Person 1 OSINT item ready for Person 2 marketing workflows.',
  cveIds: [],
  tags: ['contract', 'osint'],
  timestamp: '2026-06-12T00:00:00.000Z',
  sourceVerified: true,
  isMisinformation: false,
  usedInMarketing: false,
  source: 'contract-fixture'
};

export const PERSON1_REQUIRED_INTEL_FIELDS = [
  'id',
  'title',
  'classification',
  'severity',
  'summary',
  'cveIds',
  'tags',
  'timestamp',
  'sourceVerified',
  'isMisinformation',
  'usedInMarketing'
];
