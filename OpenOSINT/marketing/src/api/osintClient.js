import axios from 'axios';

export async function markLiveIntelUsed(intelId, osintApiUrl) {
  if (process.env.MARKETING_USE_LIVE_OSINT !== 'true' || !osintApiUrl || !intelId) {
    return { attempted: false, marked: false };
  }
  try {
    await axios.post(`${osintApiUrl}/api/intel/${encodeURIComponent(intelId)}/mark-used`, null, {
      timeout: 2500
    });
    return { attempted: true, marked: true };
  } catch (error) {
    return {
      attempted: true,
      marked: false,
      error: error?.message || 'mark-used failed'
    };
  }
}
