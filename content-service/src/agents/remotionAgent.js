import { llmComplete, detectProvider } from './llm.js';
import { parseJsonResponse } from './json.js';
import { plainText } from '../utils/safety.js';
import { makeLogger } from '../utils/logger.js';

const log = makeLogger('RemotionAgent');

const VIDEO_SYSTEM = `You are a cybersecurity video script writer for SQ1 Security.
You receive structured threat intelligence from live RSS feeds and OSINT sources.
Your job is to craft punchy, professional video scripts that brief security teams and business leaders.

Return ONLY valid JSON — no markdown, no commentary — with this exact shape:
{
  "title": "video title, max 12 words",
  "durationSeconds": 30 | 45 | 60,
  "scenes": [
    {
      "sceneNumber": 1,
      "durationSeconds": 8,
      "onScreenText": "max 8 words displayed on screen",
      "narration": "1-2 sentences spoken aloud, max 30 words",
      "visualNote": "brief art direction note for the designer",
      "bgStyle": "dark_grid | red_pulse | amber_static | blue_wave | matrix_rain"
    }
  ],
  "closingCta": "3-6 word call to action"
}

bgStyle guide: CRITICAL/BREACH → red_pulse, VULNERABILITY → amber_static, THREAT → dark_grid or matrix_rain, COMPLIANCE → blue_wave, default → dark_grid.
Scene count: 3 scenes for 30s, 4 for 45s, 5 for 60s.`;

function buildPrompt(intel) {
  const hooks = intel.contentHooks || {};
  const cves = (intel.cveIds || []).join(', ') || 'None';
  const source = intel.source || 'Unknown';
  const published = intel.published ? new Date(intel.published).toDateString() : 'Unknown date';
  const alertType = hooks.alertType || 'incident';
  const requestedDuration = Number(intel.requestedDurationSeconds) || 30;

  return `Create a ${requestedDuration}-second video script for this live threat intelligence item.

=== SOURCE INTEL ===
Source: ${source} (${published})
Title: ${intel.title}
Classification: ${intel.classification || 'THREAT'}
Severity: ${intel.severity || 'HIGH'}
Summary: ${intel.summary || intel.title}
CVEs: ${cves}
Alert Type: ${alertType}

=== AI PRE-ANALYSIS (use as creative foundation) ===
Hook Headline: ${hooks.headline || intel.title}
Blog Angle / Narrative: ${hooks.blogAngle || 'Security teams should act immediately.'}
Alert Type: ${alertType}

=== VIDEO STRUCTURE GUIDE ===
Scene 1 (~8s): HOOK — open with the hook headline, grab attention, set urgency.
  - onScreenText: the hook headline adapted for screen
  - bgStyle: match severity (CRITICAL→red_pulse, HIGH→amber_static, else dark_grid)
Scene 2 (~12s): CONTEXT — use the blog angle as the narrative. Cover: what happened, who is affected, business impact.
  - onScreenText: the key impact in 5-7 words
  - bgStyle: amber_static or matrix_rain for technical depth
Scene 3 (for 30s) or Scenes 3-4 (for 45/60s): ACTION — what should viewers do? Reference CVEs if present.
  - bgStyle: blue_wave for action/compliance tone
Final Scene: ATTRIBUTION — credit the source, CTA.
  - onScreenText: "Source: ${source}"
  - bgStyle: dark_grid

Make narration conversational and urgent. Never use jargon without explanation. Duration must be exactly ${requestedDuration}.`;
}

function fallbackVideoScript(intel) {
  const title = intel?.title || 'Security Briefing';
  const hooks = intel?.contentHooks || {};
  const duration = Number(intel?.requestedDurationSeconds) || 5;
  const source = intel?.source || 'SQ1 Intel';
  return {
    title,
    durationSeconds: duration,
    scenes: [
      {
        sceneNumber: 1,
        durationSeconds: duration,
        onScreenText: hooks.headline ? compactSceneText(hooks.headline) : 'New Intel Detected',
        narration: `${intel?.classification || 'Security'} intelligence from ${source}: ${compactSceneText(title)}.`,
        visualNote: 'SQ1 logo pulse on dark background.',
        bgStyle: intel?.severity === 'CRITICAL' ? 'red_pulse' : 'dark_grid'
      }
    ],
    closingCta: intel?.severity === 'CRITICAL' ? 'Patch Now' : 'Review Now'
  };
}

function compactSceneText(text) {
  return text.split(/\s+/).slice(0, 8).join(' ');
}

export async function generateVideoScript(intel) {
  log.info('Video script generation requested', { intelId: intel?.id, title: intel?.title, severity: intel?.severity, durationSeconds: intel?.requestedDurationSeconds });

  const fallback = fallbackVideoScript(intel);

  if (process.env.MARKETING_USE_AI_VIDEO !== 'true') {
    log.info('AI video disabled (MARKETING_USE_AI_VIDEO != true) — using fallback template');
    return normalizeScript(fallback, fallback);
  }

  const provider = detectProvider();
  if (!provider) {
    log.warn('No LLM provider detected — using fallback video template');
    return normalizeScript(fallback, fallback);
  }

  log.info('Calling LLM for video script', { provider, durationSeconds: Number(intel?.requestedDurationSeconds) || 30 });
  try {
    const raw = await llmComplete({
      system: VIDEO_SYSTEM,
      user: buildPrompt(intel),
      maxTokens: 1200,
      provider
    });
    log.info('LLM video script generation succeeded');
    return normalizeScript(parseJsonResponse(raw, fallback), fallback);
  } catch (err) {
    log.error('LLM video script generation failed — using fallback', { error: err?.message });
    return normalizeScript(fallback, fallback);
  }
}

function normalizeScript(value, fallback) {
  const script = { ...fallback, ...(value || {}) };
  const scenes = Array.isArray(script.scenes) ? script.scenes : fallback.scenes;
  return {
    title: plainText(script.title, 120),
    durationSeconds: [3, 4, 5, 30, 45, 60].includes(Number(script.durationSeconds))
      ? Number(script.durationSeconds)
      : fallback.durationSeconds,
    scenes: scenes.slice(0, 8).map((scene, index) => ({
      sceneNumber: Number(scene.sceneNumber || index + 1),
      durationSeconds: Number(scene.durationSeconds || 8),
      onScreenText: plainText(scene.onScreenText, 80),
      narration: plainText(scene.narration, 220),
      visualNote: plainText(scene.visualNote, 180),
      bgStyle: plainText(scene.bgStyle, 40)
    })),
    closingCta: plainText(script.closingCta, 60)
  };
}
