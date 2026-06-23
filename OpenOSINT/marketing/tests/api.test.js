import request from 'supertest';
import axios from 'axios';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { createApp } from '../src/api/app.js';
import { createMemoryDb } from '../src/api/db.js';
import {
  PERSON1_INTEL_CONTRACT_ITEM,
  PERSON1_REQUIRED_INTEL_FIELDS
} from './fixtures/intelContract.js';

async function buildApp() {
  const db = createMemoryDb();
  await db.read();
  const app = createApp({ db, osintApiUrl: 'http://127.0.0.1:8000' });
  return { app, db };
}

describe('marketing API', () => {
  afterEach(() => {
    delete process.env.MARKETING_USE_LIVE_OSINT;
    delete process.env.MARKETING_ENABLE_MOCK_INTEL;
    delete process.env.SLACK_WEBHOOK_URL;
    delete process.env.TEAMS_WEBHOOK_URL;
    vi.restoreAllMocks();
  });

  test('health reports the marketing service', async () => {
    const { app } = await buildApp();

    const res = await request(app).get('/api/health');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      status: 'ok',
      service: 'sq1-marketing',
      emailConfigured: false
    });
  });

  test('returns an empty portal-gated queue by default', async () => {
    const { app } = await buildApp();

    const res = await request(app).get('/api/intel/marketing-queue');

    expect(res.status).toBe(200);
    expect(res.body.source).toBe('portal');
    expect(res.body.items).toHaveLength(0);
  });

  test('returns mock intel only when explicitly enabled', async () => {
    process.env.MARKETING_ENABLE_MOCK_INTEL = 'true';
    const { app } = await buildApp();

    const res = await request(app).get('/api/intel/marketing-queue');

    expect(res.status).toBe(200);
    expect(res.body.source).toBe('mock');
    expect(res.body.items).toHaveLength(5);
  });

  test('returns an empty queue when live OSINT mode cannot reach the API', async () => {
    process.env.MARKETING_USE_LIVE_OSINT = 'true';
    vi.spyOn(axios, 'get').mockRejectedValue(new Error('offline'));
    const { app } = await buildApp();

    const res = await request(app).get('/api/intel/marketing-queue');

    expect(res.status).toBe(200);
    expect(res.body.source).toBe('live');
    expect(res.body.fallbackReason).toBe('live-api-unavailable');
    expect(res.body.items).toHaveLength(0);
  });

  test('normalizes live OSINT items', async () => {
    process.env.MARKETING_USE_LIVE_OSINT = 'true';
    vi.spyOn(axios, 'get').mockResolvedValue({
      data: [{ id: 'live-1', title: 'Live item', classification: 'THREAT', severity: 'HIGH' }]
    });
    const { app } = await buildApp();

    const res = await request(app).get('/api/intel/marketing-queue');

    expect(res.status).toBe(200);
    expect(res.body.source).toBe('live');
    expect(axios.get).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/intel/marketing-queue',
      { timeout: 2500 }
    );
    expect(res.body.items[0]).toMatchObject({
      id: 'live-1',
      cveIds: [],
      tags: [],
      sourceVerified: false,
      isMisinformation: false,
      usedInMarketing: false
    });
  });

  test('accepts the shared Person 1 intel contract fields', async () => {
    process.env.MARKETING_USE_LIVE_OSINT = 'true';
    vi.spyOn(axios, 'get').mockResolvedValue({ data: [PERSON1_INTEL_CONTRACT_ITEM] });
    const { app } = await buildApp();

    const res = await request(app).get('/api/intel/marketing-queue');

    expect(res.status).toBe(200);
    expect(res.body.source).toBe('live');
    for (const field of PERSON1_REQUIRED_INTEL_FIELDS) {
      expect(res.body.items[0]).toHaveProperty(field);
    }
    expect(res.body.items[0]).toMatchObject(PERSON1_INTEL_CONTRACT_ITEM);
  });

  test('generates a fallback campaign without an Anthropic key', async () => {
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/campaigns/generate')
      .send({
        intel: {
          id: 'intel-test',
          title: 'Critical Apache RCE',
          classification: 'VULNERABILITY',
          severity: 'CRITICAL',
          summary: 'Patch immediately.',
          cveIds: ['CVE-2024-38476']
        }
      });

    expect(res.status).toBe(200);
    expect(res.body.campaign.subject).toContain('Critical Apache RCE');
    expect(res.body.campaign.tone).toBe('urgent');
    expect(db.data.campaigns).toHaveLength(1);
  });

  test('marks live OSINT intel as used after campaign generation in live mode', async () => {
    process.env.MARKETING_USE_LIVE_OSINT = 'true';
    const postSpy = vi.spyOn(axios, 'post').mockResolvedValue({ data: { success: true } });
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/campaigns/generate')
      .send({
        intel: {
          ...PERSON1_INTEL_CONTRACT_ITEM,
          id: 'live-campaign-1',
          title: 'Live Campaign Item'
        }
      });

    expect(res.status).toBe(200);
    expect(db.data.campaigns).toHaveLength(1);
    expect(res.body.markUsed).toMatchObject({ attempted: true, marked: true });
    expect(postSpy).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/intel/live-campaign-1/mark-used',
      null,
      { timeout: 2500 }
    );
  });

  test('campaign generation still succeeds when live mark-used fails', async () => {
    process.env.MARKETING_USE_LIVE_OSINT = 'true';
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('osint offline'));
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/campaigns/generate')
      .send({
        intel: {
          ...PERSON1_INTEL_CONTRACT_ITEM,
          id: 'live-campaign-offline',
          title: 'Live Offline Item'
        }
      });

    expect(res.status).toBe(200);
    expect(db.data.campaigns).toHaveLength(1);
    expect(res.body.markUsed).toMatchObject({
      attempted: true,
      marked: false,
      error: 'osint offline'
    });
  });

  test('escapes unsafe campaign body content', async () => {
    const { app } = await buildApp();

    const res = await request(app)
      .post('/api/campaigns/generate')
      .send({
        intel: {
          id: 'intel-xss',
          title: 'Unsafe Summary',
          classification: 'THREAT',
          severity: 'HIGH',
          summary: '<img src=x onerror=alert(1)>Patch now',
          cveIds: []
        }
      });

    expect(res.status).toBe(200);
    expect(res.body.campaign.body).not.toContain('<img');
    expect(res.body.campaign.body).not.toContain('onerror');
    expect(res.body.campaign.body).toContain('&lt;img');
  });

  test('creates and persists a visual asset', async () => {
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/assets/create')
      .send({
        type: 'hyperframe',
        intel: {
          id: 'intel-asset',
          title: 'Ransomware Group Active',
          classification: 'THREAT',
          severity: 'HIGH',
          summary: 'Healthcare targeting observed.',
          cveIds: []
        }
      });

    expect(res.status).toBe(200);
    expect(res.body.asset.kind).toBe('hyperframe');
    expect(res.body.asset.content.headline).toBeTruthy();
    expect(db.data.assets).toHaveLength(1);
  });

  test('creates and persists a video asset', async () => {
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/assets/create?type=video')
      .send({
        intel: {
          id: 'intel-video',
          title: 'Breach Timeline',
          classification: 'BREACH',
          severity: 'CRITICAL',
          summary: 'Data exposure requires briefing.',
          cveIds: []
        }
      });

    expect(res.status).toBe(200);
    expect(res.body.asset.kind).toBe('video');
    expect(res.body.asset.content.durationSeconds).toBe(5);
    expect(res.body.asset.content.scenes.length).toBeGreaterThan(0);
    expect(db.data.assets).toHaveLength(1);
  });

  test('sends campaigns to the fixed Gmail recipient', async () => {
    const { app, db } = await buildApp();
    db.data.campaigns.push({
      id: 'campaign-fixed',
      intelId: 'intel-fixed',
      intelTitle: 'Fixed Recipient Test',
      createdAt: '2026-06-12T00:00:00.000Z',
      campaign: { subject: 'Fixed recipient test' }
    });

    const res = await request(app)
      .post('/api/campaigns/send')
      .send({
        campaignId: 'campaign-fixed',
        recipients: [{ email: 'somebody-else@example.com' }]
      });

    expect(res.status).toBe(200);
    expect(res.body.recipients).toEqual([
      expect.objectContaining({ email: 'crazywe2119@gmail.com' })
    ]);
    expect(res.body.emailDelivery).toMatchObject({
      attempted: false,
      sent: false,
      reason: 'smtp-not-configured'
    });
    expect(db.data.campaigns[0].recipients).toEqual([
      expect.objectContaining({ email: 'crazywe2119@gmail.com' })
    ]);
  });

  test('marks live OSINT intel as used after creating an asset in live mode', async () => {
    process.env.MARKETING_USE_LIVE_OSINT = 'true';
    const postSpy = vi.spyOn(axios, 'post').mockResolvedValue({ data: { success: true } });
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/assets/create')
      .send({
        type: 'hyperframe',
        intel: {
          ...PERSON1_INTEL_CONTRACT_ITEM,
          id: 'live-intel-1',
          title: 'Live OSINT Item'
        }
      });

    expect(res.status).toBe(200);
    expect(db.data.assets).toHaveLength(1);
    expect(postSpy).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/intel/live-intel-1/mark-used',
      null,
      { timeout: 2500 }
    );
  });

  test('marks live OSINT intel as used after saving a manual asset', async () => {
    process.env.MARKETING_USE_LIVE_OSINT = 'true';
    const postSpy = vi.spyOn(axios, 'post').mockResolvedValue({ data: { success: true } });
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/assets')
      .send({
        kind: 'email',
        intel: { id: 'live-manual-asset', title: 'Manual Asset Intel' },
        content: { title: 'Manual saved asset' }
      });

    expect(res.status).toBe(201);
    expect(db.data.assets).toHaveLength(1);
    expect(res.body.markUsed).toMatchObject({ attempted: true, marked: true });
    expect(postSpy).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/intel/live-manual-asset/mark-used',
      null,
      { timeout: 2500 }
    );
  });

  test('supports subscriber create, list, and unsubscribe', async () => {
    const { app } = await buildApp();

    const createRes = await request(app)
      .post('/api/subscribers/subscribe')
      .send({
        name: 'Asha Rao',
        email: 'asha@example.com',
        company: 'SQ1 Customer',
        threatTypes: ['THREAT', 'BREACH'],
        minimumSeverity: 'HIGH+',
        industry: 'Healthcare'
      });

    expect(createRes.status).toBe(201);
    expect(createRes.body.subscriber.email).toBe('asha@example.com');

    const listRes = await request(app).get('/api/subscribers/list');
    const listed = listRes.body.subscribers.find((s) => s.id === createRes.body.subscriber.id);
    expect(listed.email).toBe('as***@example.com');
    expect(listed.fullEmail).toBeUndefined();

    const deleteRes = await request(app).delete(
      `/api/subscribers/${createRes.body.subscriber.id}/unsubscribe`
    );
    expect(deleteRes.status).toBe(200);
    expect(deleteRes.body.success).toBe(true);
  });

  test('returns Slack and Teams payloads without configured webhooks', async () => {
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/comms/alert')
      .send({
        intel: {
          id: 'intel-alert',
          title: 'Breach Data Published',
          classification: 'BREACH',
          severity: 'CRITICAL',
          summary: 'Customer records appeared online.',
          cveIds: []
        }
      });

    expect(res.status).toBe(200);
    expect(res.body.results.slack.sent).toBe(false);
    expect(res.body.results.teams.sent).toBe(false);
    expect(res.body.results.slack.payload.blocks).toBeTruthy();
    expect(res.body.results.teams.payload['@type']).toBe('MessageCard');
    expect(db.data.alerts).toHaveLength(1);
  });

  test('returns alert payloads when configured webhooks fail', async () => {
    process.env.SLACK_WEBHOOK_URL = 'https://hooks.slack.test/fail';
    process.env.TEAMS_WEBHOOK_URL = 'https://teams.test/fail';
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('webhook offline'));
    const { app, db } = await buildApp();

    const res = await request(app)
      .post('/api/comms/alert')
      .send({
        intel: {
          id: 'intel-alert-fail',
          title: 'Webhook Failure Still Safe',
          classification: 'THREAT',
          severity: 'HIGH',
          summary: 'Configured channels are unavailable.',
          cveIds: []
        }
      });

    expect(res.status).toBe(200);
    expect(res.body.results.slack).toMatchObject({
      sent: false,
      error: 'webhook offline',
      payload: expect.any(Object)
    });
    expect(res.body.results.teams).toMatchObject({
      sent: false,
      error: 'webhook offline',
      payload: expect.any(Object)
    });
    expect(db.data.alerts).toHaveLength(1);
  });
});
