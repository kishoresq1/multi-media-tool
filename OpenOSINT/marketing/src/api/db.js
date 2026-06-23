import { mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';

const DEFAULT_DATA = {
  campaigns: [],
  assets: [],
  subscribers: [],
  alerts: []
};

const DEMO_SUBSCRIBERS = [
  {
    name: 'Maya Srinivasan',
    email: 'maya@caregrid.example',
    company: 'CareGrid Health',
    threatTypes: ['THREAT', 'BREACH', 'VULNERABILITY'],
    minimumSeverity: 'HIGH+',
    industry: 'Healthcare'
  },
  {
    name: 'Noah Kim',
    email: 'noah@finshield.example',
    company: 'FinShield Bank',
    threatTypes: ['BREACH', 'COMPLIANCE', 'MISINFORMATION'],
    minimumSeverity: 'MEDIUM+',
    industry: 'Finance'
  },
  {
    name: 'Elena Park',
    email: 'elena@cloudforge.example',
    company: 'CloudForge',
    threatTypes: ['VULNERABILITY', 'THREAT'],
    minimumSeverity: 'ALL',
    industry: 'Tech'
  },
  {
    name: 'Samir Patel',
    email: 'samir@retailops.example',
    company: 'RetailOps',
    threatTypes: ['BREACH', 'COMPLIANCE'],
    minimumSeverity: 'HIGH+',
    industry: 'Retail'
  },
  {
    name: 'Grace Moreno',
    email: 'grace@govsecure.example',
    company: 'GovSecure',
    threatTypes: ['THREAT', 'MISINFORMATION', 'COMPLIANCE'],
    minimumSeverity: 'CRITICAL only',
    industry: 'Government'
  }
];

export function createMemoryDb(initialData = {}) {
  const adapter = {
    read: async () => structuredClone({ ...DEFAULT_DATA, ...initialData }),
    write: async () => {}
  };
  return new Low(adapter, structuredClone(DEFAULT_DATA));
}

export async function createFileDb(filePath = './data/db.json') {
  const absolutePath = resolve(filePath);
  await mkdir(dirname(absolutePath), { recursive: true });
  const db = new Low(new JSONFile(absolutePath), structuredClone(DEFAULT_DATA));
  await db.read();
  db.data ||= structuredClone(DEFAULT_DATA);
  normalizeDb(db);
  await seedSubscribers(db);
  await db.write();
  return db;
}

export function normalizeDb(db) {
  db.data ||= structuredClone(DEFAULT_DATA);
  for (const key of Object.keys(DEFAULT_DATA)) {
    if (!Array.isArray(db.data[key])) {
      db.data[key] = [];
    }
  }
  return db;
}

export async function seedSubscribers(db) {
  normalizeDb(db);
  if (db.data.subscribers.length > 0) return;
  const now = new Date().toISOString();
  db.data.subscribers.push(
    ...DEMO_SUBSCRIBERS.map((subscriber, index) => ({
      id: `demo-sub-${index + 1}`,
      createdAt: now,
      ...subscriber
    }))
  );
}

export async function persist(db) {
  normalizeDb(db);
  await db.write();
}
