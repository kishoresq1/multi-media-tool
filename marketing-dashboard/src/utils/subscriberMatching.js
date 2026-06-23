const SEVERITY_RANK = {
  INFO: 0,
  LOW: 1,
  MEDIUM: 2,
  HIGH: 3,
  CRITICAL: 4
};

const MINIMUM_SEVERITY_RANK = {
  ALL: 0,
  'MEDIUM+': 2,
  'HIGH+': 3,
  'CRITICAL ONLY': 4
};

export function subscriberMatchesIntel(subscriber, intel) {
  return scoreSubscriberIntelMatch(subscriber, intel) > 0;
}

export function scoreSubscriberIntelMatch(subscriber, intel) {
  if (!subscriber || !intel) return 0;

  return matchesClassification(subscriber, intel) && meetsMinimumSeverity(intel, subscriber) ? 1 : 0;
}

export function getMatchedSubscribers(intel, subscribers = []) {
  return subscribers.filter((subscriber) => subscriberMatchesIntel(subscriber, intel));
}

export function countMatchedSubscribers(intel, subscribers = []) {
  return getMatchedSubscribers(intel, subscribers).length;
}

function matchesClassification(subscriber, intel) {
  const threatTypes = Array.isArray(subscriber.threatTypes) ? subscriber.threatTypes : [];
  if (threatTypes.length === 0) return true;

  return threatTypes.includes(intel.classification);
}

function meetsMinimumSeverity(intel, subscriber) {
  const severityRank = SEVERITY_RANK[String(intel.severity || '').toUpperCase()] ?? 0;
  const minimumRank =
    MINIMUM_SEVERITY_RANK[String(subscriber.minimumSeverity || 'ALL').toUpperCase()] ?? 0;

  return severityRank >= minimumRank;
}
