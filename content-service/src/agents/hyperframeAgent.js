import { llmComplete, detectProvider } from './llm.js';
import { parseJsonResponse } from './json.js';
import { plainText } from '../utils/safety.js';
import { makeLogger } from '../utils/logger.js';

const log = makeLogger('HyperframeAgent');

const HYPERFRAME_SYSTEM = `You are a cybersecurity visual content designer for SQ1 Security.
You receive structured threat intelligence from RSS feeds and OSINT sources.
Your job is to turn that intel into punchy, high-impact visual content for social media and security briefings.

Return ONLY valid JSON — no markdown, no commentary — with these exact keys:
{
  "headline": "max 10 words, punchy social-media-ready hook",
  "subheadline": "max 18 words, technical context or affected scope",
  "bodyText": "2-3 sentences, actionable insight for security teams and business leaders",
  "severityLabel": "e.g. CRITICAL BREACH or HIGH VULNERABILITY",
  "cveBadge": "CVE-YYYY-XXXXX or null",
  "hashtags": ["up to 5 tags, no # prefix"],
  "callToAction": "3-5 word imperative, e.g. Patch Now or Read Full Report",
  "colorScheme": "one of: threat_red | vuln_amber | breach_dark | compliance_blue | misinfo_green | digest_purple",
  "statHighlight": "a striking stat or CVE or null"
}`;

function buildPrompt(intel) {
  const hooks = intel.contentHooks || {};
  const cves = (intel.cveIds || []).join(', ') || 'None';
  const tags = (intel.tags || []).join(', ') || 'None';
  const source = intel.source || 'Unknown';
  const published = intel.published ? new Date(intel.published).toDateString() : 'Unknown date';
  const alertType = hooks.alertType || 'incident';

  return `Create a HyperFrame graphic for this live threat intelligence item.

=== SOURCE INTEL ===
Source: ${source} (${published})
Title: ${intel.title}
Classification: ${intel.classification || 'THREAT'}
Severity: ${intel.severity || 'HIGH'}
Summary: ${intel.summary || intel.title}
CVEs: ${cves}
Tags: ${tags}
Alert Type: ${alertType}

=== AI PRE-ANALYSIS (use as creative seed, improve on it) ===
Suggested Headline: ${hooks.headline || intel.title}
Blog Angle: ${hooks.blogAngle || 'Security teams should review this immediately.'}
Alert Type: ${alertType}

=== INSTRUCTIONS ===
- The headline must be more punchy than the suggested one — lead with the risk or impact
- bodyText should give security professionals and business leaders one clear takeaway
- statHighlight: pull a striking number, CVE ID, or impact stat from the summary (or null)
- colorScheme must match classification: BREACH→breach_dark, VULNERABILITY→vuln_amber, THREAT→threat_red, COMPLIANCE→compliance_blue, MISINFORMATION→misinfo_green
- hashtags: derive from tags + classification, keep them professional and relevant`;
}

function fallbackHyperframe(intel) {
  const classification = intel?.classification || 'THREAT';
  const severity = intel?.severity || 'INFO';
  const hooks = intel?.contentHooks || {};
  const cve = intel?.cveIds?.[0] || null;
  return {
    headline: hooks.headline ? compactHeadline(hooks.headline) : compactHeadline(intel?.title || 'Security Alert'),
    subheadline: hooks.blogAngle || `${severity} ${classification.toLowerCase()} intelligence requires review`,
    bodyText: intel?.summary || 'SQ1 detected a security item ready for action.',
    severityLabel: `${severity} ${classification}`,
    cveBadge: cve,
    hashtags: normalizeTags(intel?.tags, classification),
    callToAction: severity === 'CRITICAL' ? 'Act Now' : 'Review Now',
    colorScheme: colorSchemeFor(classification),
    statHighlight: cve || severity
  };
}

function compactHeadline(text) {
  return text.split(/\s+/).slice(0, 10).join(' ');
}

function normalizeTags(tags = [], classification) {
  const values = tags.length ? tags : [classification.toLowerCase(), 'sq1', 'security'];
  return values.slice(0, 5).map((tag) => String(tag).replace(/^#/, '').replace(/\s+/g, '-'));
}

function colorSchemeFor(classification = '') {
  const key = classification.toUpperCase();
  if (key === 'COMPLIANCE') return 'compliance_blue';
  if (key === 'VULNERABILITY') return 'vuln_amber';
  if (key === 'BREACH') return 'breach_dark';
  if (key === 'MISINFORMATION') return 'misinfo_green';
  if (key === 'DIGEST') return 'digest_purple';
  return 'threat_red';
}

export async function generateHyperframeContent(intel) {
  log.info('Hyperframe generation requested', { intelId: intel?.id, title: intel?.title, severity: intel?.severity });
  const fallback = fallbackHyperframe(intel);

  if (process.env.MARKETING_USE_AI_VISUALS !== 'true') {
    log.info('AI visuals disabled (MARKETING_USE_AI_VISUALS != true) — using fallback template');
    return normalizeHyperframe(fallback, fallback);
  }

  const provider = detectProvider();
  if (!provider) {
    log.warn('No LLM provider detected — using fallback template');
    return normalizeHyperframe(fallback, fallback);
  }

  log.info('Calling LLM for hyperframe content', { provider });
  try {
    const raw = await llmComplete({
      system: HYPERFRAME_SYSTEM,
      user: buildPrompt(intel),
      maxTokens: 800,
      provider
    });
    log.info('LLM hyperframe generation succeeded');
    return normalizeHyperframe(parseJsonResponse(raw, fallback), fallback);
  } catch (err) {
    log.error('LLM hyperframe generation failed — using fallback', { error: err?.message });
    return normalizeHyperframe(fallback, fallback);
  }
}

function normalizeHyperframe(value, fallback) {
  const data = { ...fallback, ...(value || {}) };
  return {
    headline: plainText(data.headline, 80),
    subheadline: plainText(data.subheadline, 120),
    bodyText: plainText(data.bodyText, 240),
    severityLabel: plainText(data.severityLabel, 60),
    cveBadge: data.cveBadge ? plainText(data.cveBadge, 40) : null,
    hashtags: Array.isArray(data.hashtags)
      ? data.hashtags.slice(0, 5).map((tag) => plainText(tag, 24))
      : [],
    callToAction: plainText(data.callToAction, 40),
    colorScheme: plainText(data.colorScheme, 40),
    statHighlight: data.statHighlight ? plainText(data.statHighlight, 60) : null
  };
}
