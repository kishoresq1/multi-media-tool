export async function fetchJson(url, options = {}) {
  const { headers, ...rest } = options;
  const response = await fetch(url, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {})
    }
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export async function getIntel(options = {}) {
  try {
    return await fetchJson('/mkt/intel/marketing-queue', options);
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    return { source: 'portal', fallbackReason: 'marketing-api-unavailable', items: [] };
  }
}

export async function createCampaign(intel) {
  return fetchJson('/mkt/campaigns/generate', {
    method: 'POST',
    body: JSON.stringify({ intel })
  });
}

export async function sendCampaign(campaignId, recipients) {
  return fetchJson('/mkt/campaigns/send', {
    method: 'POST',
    body: JSON.stringify({ campaignId, recipients })
  });
}

export async function createAsset(intel, type = 'hyperframe') {
  return fetchJson(`/mkt/assets/create?type=${encodeURIComponent(type)}`, {
    method: 'POST',
    body: JSON.stringify({ intel, type })
  });
}

export async function sendAlert(intel) {
  return fetchJson('/mkt/comms/alert', {
    method: 'POST',
    body: JSON.stringify({ intel })
  });
}

export async function listAlerts(options = {}) {
  return fetchJson('/mkt/comms/alerts', options);
}

export async function listSubscribers(options = {}) {
  return fetchJson('/mkt/subscribers/list', options);
}

export async function listCampaigns(options = {}) {
  return fetchJson('/mkt/campaigns/list', options);
}

export async function subscribe(payload) {
  return fetchJson('/mkt/subscribers/subscribe', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function listAssets(options = {}) {
  return fetchJson('/mkt/assets/list', options);
}

export async function searchAssets(q = '', kind = '') {
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (kind) params.set('kind', kind);
  return fetchJson(`/mkt/assets/search?${params.toString()}`);
}

export async function uploadAssetImage(assetId, dataUrl) {
  return fetchJson(`/mkt/assets/${encodeURIComponent(assetId)}/image`, {
    method: 'POST',
    body: JSON.stringify({ dataUrl })
  });
}

export async function uploadAssetVideo(assetId, blob) {
  const res = await fetch(`/mkt/assets/${encodeURIComponent(assetId)}/video`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: blob
  });
  if (!res.ok) throw new Error(`Video upload failed: ${res.status}`);
  return res.json();
}
