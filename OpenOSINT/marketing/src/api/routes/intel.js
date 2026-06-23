import axios from 'axios';
import { existsSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { resolve } from 'node:path';
import { MOCK_INTEL } from '../../mock/intelMockData.js';

export default function intelRoutes({ osintApiUrl }) {
  async function getUnmarketed(_req, res) {
    if (process.env.MARKETING_ENABLE_MOCK_INTEL === 'true') {
      return res.json({ source: 'mock', items: MOCK_INTEL });
    }
    try {
      const response = await axios.get(`${osintApiUrl}/api/intel/marketing-queue`, { timeout: 2500 });
      return res.json({ source: 'live', items: normalizeItems(response.data) });
    } catch (err) {
      console.error('[intel] SQ1 portal queue fetch failed:', err?.message || err);
      const fallbackItems = readLocalPortalQueue();
      if (fallbackItems.length > 0) {
        return res.json({
          source: 'live',
          fallbackReason: 'portal-api-unavailable-local-db',
          items: normalizeItems(fallbackItems)
        });
      }
      return res.json({ source: 'portal', fallbackReason: 'portal-api-unavailable', items: [] });
    }
  }

  return { getUnmarketed };
}

function normalizeItems(data) {
  const items = Array.isArray(data) ? data : data?.items || [];
  return items.map((item) => ({
    usedInMarketing: false,
    cveIds: [],
    tags: [],
    sourceVerified: false,
    isMisinformation: false,
    readyForMarketing: true,
    ...item
  }));
}

function readLocalPortalQueue() {
  const dbPath = process.env.SQ1_DB_PATH || resolve(homedir(), '.sq1-osint/db.json');
  try {
    if (!existsSync(dbPath)) return [];
    const raw = JSON.parse(readFileSync(dbPath, 'utf8') || '{}');
    const table = raw.intel || {};
    const items = Array.isArray(table) ? table : Object.values(table);
    return items
      .filter((item) =>
        item?.readyForMarketing === true
        && item?.usedInMarketing === false
        && item?.isMisinformation !== true
      )
      .sort((a, b) =>
        String(b.marketingPushedAt || b.timestamp || '').localeCompare(
          String(a.marketingPushedAt || a.timestamp || '')
        )
      );
  } catch (error) {
    console.error('[intel] Local SQ1 queue fallback failed:', error?.message || error);
    return [];
  }
}
