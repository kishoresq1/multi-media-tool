# 📣 SQ1 OSINT Intelligence Platform — PERSON 2: Marketing Module
### Claude Build Prompt | Sits on top of OpenOSINT Fork | Deadline: 14:40

---

## ⚡ CONTEXT FOR CLAUDE

You are building the **SQ1 Marketing Intelligence Module** — a standalone `marketing/` folder inside the forked OpenOSINT repo. Person 1 is extending the OpenOSINT Python backend and building a FastAPI server at `http://localhost:8000`. Your module is a **separate React + Node.js app** that consumes their API.

**Your app runs on:** Vite port `5174`, backend port `3002`  
**Person 1's API:** `http://localhost:8000`  
**Start time:** 11:40 | **Hard deadline:** 14:40 | **Budget:** 180 min

**Key mindset:** Do NOT wait for Person 1. Use mock data from minute one. Swap to live API at 13:45.

---

## 🏗️ WHAT YOU ARE BUILDING

A `marketing/` folder inside the cloned `sq1-openosint/` repo:

```
sq1-openosint/
├── openosint/        ← Person 1's territory — DO NOT TOUCH
├── frontend/         ← Person 1's territory — DO NOT TOUCH
└── marketing/        ← YOUR ENTIRE WORLD
    ├── src/
    │   ├── agents/
    │   ├── api/
    │   ├── frontend/
    │   ├── templates/
    │   └── mock/
    └── package.json
```

### Agent 2 — Email Campaign Engine
- Pulls intel from Person 1's API (`/api/intel/unmarketed`)
- Claude generates personalized email for each intel classification
- 5 email templates: Threat Alert, Breach Notification, Compliance Update, Weekly Digest, Misinfo Clarification
- **Subscribe to Threats** feature: customers pick severity + threat types + industry → auto-email on match

### Agent 3 — HyperFrame Visual Content Generator
- Claude generates branded graphic copy from intel data
- **6 template types** rendered as 1200×628px React → downloadable PNG via `html2canvas`
- Template types: Threat 🔴 | Compliance 🔵 | Vulnerability 🟡 | Breach ⚫ | Misinfo Clarification 🟢 | Weekly Digest 🟣

### Agent 4 — Remotion Video Builder
- Claude generates scene-by-scene video script from intel
- `@remotion/player` renders preview in browser (no CLI export — too slow)
- Video types: Threat Briefing (30s), CVE Explainer (60s), Breach Timeline (45s)

### Agent 5 — Internal Security Team Comms
- One-click: send Slack + Microsoft Teams alert when critical intel arrives
- Slack: Block Kit format via Incoming Webhook
- Teams: `messageCard` format via Office 365 Connector webhook

### Marketing Portal (Main UI)
- Central dashboard: stats + Intel Queue (items ready to market) + Asset Gallery
- Full pipeline view: intel arrives → queue → create asset → send/export

---

## 📁 FOLDER STRUCTURE

```
marketing/
├── src/
│   ├── agents/
│   │   ├── emailAgent.js         ← Claude → JSON email → nodemailer (or log)
│   │   ├── hyperframeAgent.js    ← Claude → graphic copy JSON
│   │   ├── remotionAgent.js      ← Claude → video scene JSON
│   │   └── slackTeamsAgent.js    ← axios POST to webhooks
│   │
│   ├── api/
│   │   ├── server.js             ← Express on port 3002
│   │   └── routes/
│   │       ├── campaigns.js      ← POST /api/campaigns/generate
│   │       ├── assets.js         ← GET/POST /api/assets
│   │       ├── subscribers.js    ← GET/POST /api/subscribers
│   │       └── comms.js          ← POST /api/comms/alert
│   │
│   ├── frontend/
│   │   ├── components/
│   │   │   ├── MarketingDashboard.jsx
│   │   │   ├── IntelQueue.jsx
│   │   │   ├── HyperFrameStudio.jsx
│   │   │   ├── VideoBuilder.jsx
│   │   │   ├── CampaignBuilder.jsx
│   │   │   ├── SubscribePortal.jsx
│   │   │   ├── CommsPanel.jsx
│   │   │   └── AssetGallery.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── HyperFrame.jsx
│   │   │   ├── Videos.jsx
│   │   │   └── Subscribers.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── templates/
│   │   └── hyperframe/
│   │       ├── ThreatTemplate.jsx       ← 1200×628, red
│   │       ├── ComplianceTemplate.jsx   ← 1200×628, blue
│   │       ├── VulnTemplate.jsx         ← 1200×628, amber
│   │       ├── BreachTemplate.jsx       ← 1200×628, dark
│   │       ├── MisinfoTemplate.jsx      ← 1200×628, green
│   │       └── DigestTemplate.jsx       ← 1200×628, purple
│   │
│   └── mock/
│       └── intelMockData.js            ← CRITICAL: use this until 13:45
│
├── data/
│   └── db.json                          ← lowdb store
├── ROADMAP.md                           ← CREATE FIRST
├── TODO.md                              ← CREATE FIRST
├── .env
├── package.json
└── vite.config.js
```

---

## 🔑 ENVIRONMENT VARIABLES

```env
ANTHROPIC_API_KEY=your_key_here
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/XXX
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your@gmail.com
EMAIL_PASS=your_app_password
OSINT_API_URL=http://localhost:8000
PORT=3002
```

---

## 🚀 PHASE 1 — SETUP (15 min | 11:40–11:55)

```bash
# You should already be inside sq1-openosint/
mkdir marketing && cd marketing

# Init package
npm init -y

# Backend deps
npm install express cors dotenv lowdb axios nodemailer

# Frontend deps (Vite React)
npm create vite@latest frontend-app -- --template react
cd frontend-app && npm install
npm install tailwindcss @tailwindcss/vite html2canvas lucide-react
npm install @remotion/player remotion
cd ..
```

`package.json` scripts:
```json
{
  "scripts": {
    "dev:api": "node src/api/server.js",
    "dev:ui": "cd frontend-app && npm run dev -- --port 5174"
  }
}
```

**Immediately create:**
```bash
touch ROADMAP.md TODO.md
# Fill in the templates at the bottom of this doc
```

**Immediately create mock data:**
```bash
mkdir -p src/mock && touch src/mock/intelMockData.js
```

Paste this into `intelMockData.js` right now:
```javascript
export const MOCK_INTEL = [
  {
    id: "intel-001",
    title: "Critical RCE in Apache HTTP Server 2.4.x (CVE-2024-38476)",
    classification: "VULNERABILITY",
    severity: "CRITICAL",
    summary: "Remote code execution vulnerability affects Apache HTTP Server 2.4.x versions below 2.4.62. Active exploitation in the wild confirmed by CISA KEV. Patch immediately.",
    cveIds: ["CVE-2024-38476"],
    tags: ["rce", "apache", "web-server", "enterprise"],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false
  },
  {
    id: "intel-002",
    title: "GDPR Q3 2025 Amendment: AI Data Pipeline Audit Required by Nov 30",
    classification: "COMPLIANCE",
    severity: "HIGH",
    summary: "New EU guidance mandates companies audit all AI-processed data for cross-border transfer violations. Non-compliance fines up to 4% of global revenue.",
    cveIds: [],
    tags: ["gdpr", "compliance", "ai", "eu", "data-privacy"],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false
  },
  {
    id: "intel-003",
    title: "VIRAL CLAIM: Major US Bank Lost $4B in Crypto Hack — UNVERIFIED",
    classification: "MISINFORMATION",
    severity: "INFO",
    summary: "A claim circulating on social media alleges a major financial institution suffered a $4B crypto theft. No regulatory filings, FDIC notices, or credible sources confirm this. Likely fabricated.",
    cveIds: [],
    tags: ["misinformation", "crypto", "fake-news", "financial"],
    timestamp: new Date().toISOString(),
    sourceVerified: false,
    isMisinformation: true
  },
  {
    id: "intel-004",
    title: "73 Million AT&T Customer Records Exposed on Dark Web",
    classification: "BREACH",
    severity: "CRITICAL",
    summary: "A database containing personal details of 73 million AT&T customers appeared on a cybercrime forum. Data includes SSNs, account numbers, and encrypted passcodes.",
    cveIds: [],
    tags: ["breach", "telecom", "pii", "dark-web"],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false
  },
  {
    id: "intel-005",
    title: "Ransomware Group BlackCat Targeting Healthcare Sector — Active Campaign",
    classification: "THREAT",
    severity: "HIGH",
    summary: "BlackCat/ALPHV ransomware operators are actively targeting hospitals and healthcare networks. Average ransom demand: $4.5M. FBI warns affected organizations not to pay.",
    cveIds: [],
    tags: ["ransomware", "blackcat", "healthcare", "fbi"],
    timestamp: new Date().toISOString(),
    sourceVerified: true,
    isMisinformation: false
  }
];
```

---

## 🧠 PHASE 2 — AGENT BACKENDS (45 min | 11:55–12:40)

### `src/agents/emailAgent.js`

```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const EMAIL_SYSTEM = `You are a cybersecurity marketing expert for SQ1 Security.
Generate a professional email campaign from threat intelligence.

Rules:
- Match tone: CRITICAL/BREACH → urgent but not panicking | COMPLIANCE → professional | MISINFO → calm + corrective
- Body under 300 words, HTML allowed, no external images
- Always include actionable next steps
- Return ONLY valid JSON (no markdown fences)

Schema:
{
  "subject": string,
  "preheader": string,
  "headline": string,
  "body": string,
  "cta_text": string,
  "recommended_action": string,
  "tone": "urgent|informative|corrective|digest",
  "template_type": "threat|compliance|breach|vuln|misinfo|digest"
}`;

export async function generateEmail(intel) {
  const message = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1000,
    system: EMAIL_SYSTEM,
    messages: [{
      role: "user",
      content: `Generate email for this intel:\nTitle: ${intel.title}\nClassification: ${intel.classification}\nSeverity: ${intel.severity}\nSummary: ${intel.summary}\nCVEs: ${(intel.cveIds || []).join(', ') || 'None'}`
    }]
  });

  const raw = message.content[0].text.replace(/```json|```/g, '').trim();
  return JSON.parse(raw);
}
```

### `src/agents/hyperframeAgent.js`

```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const HYPERFRAME_SYSTEM = `You are a cybersecurity visual content designer for SQ1 Security.
Create branded graphic content from intel data.

Return ONLY valid JSON:
{
  "headline": string (max 7 words — punchy, no jargon),
  "subheadline": string (max 14 words),
  "bodyText": string (max 35 words),
  "severityLabel": string (e.g. "CRITICAL THREAT" or "COMPLIANCE UPDATE"),
  "cveBadge": string | null,
  "hashtags": string[] (3-5 tags),
  "callToAction": string (max 5 words),
  "colorScheme": "threat_red|compliance_blue|vuln_amber|breach_dark|misinfo_green|digest_purple",
  "statHighlight": string | null (e.g. "73M records leaked" or "CVSSv3: 9.8")
}`;

export async function generateHyperframeContent(intel) {
  const message = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 600,
    system: HYPERFRAME_SYSTEM,
    messages: [{
      role: "user",
      content: `Create graphic content:\nTitle: ${intel.title}\nClassification: ${intel.classification}\nSeverity: ${intel.severity}\nSummary: ${intel.summary}\nCVEs: ${(intel.cveIds || []).join(', ') || 'None'}`
    }]
  });

  const raw = message.content[0].text.replace(/```json|```/g, '').trim();
  return JSON.parse(raw);
}
```

### `src/agents/remotionAgent.js`

```javascript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const VIDEO_SYSTEM = `You are a cybersecurity video script writer for SQ1 Security.
Write short-form cybersecurity explainer video scripts.

Return ONLY valid JSON:
{
  "title": string,
  "durationSeconds": 30|45|60,
  "scenes": [
    {
      "sceneNumber": number,
      "durationSeconds": number,
      "onScreenText": string (max 8 words),
      "narration": string (what a voiceover would say, max 25 words),
      "visualNote": string (describe what appears on screen),
      "bgStyle": "dark_grid|red_pulse|blue_wave|amber_static|matrix_rain"
    }
  ],
  "closingCta": string (max 6 words)
}`;

export async function generateVideoScript(intel) {
  const message = await client.messages.create({
    model: "claude-sonnet-4-6",
    max_tokens: 1000,
    system: VIDEO_SYSTEM,
    messages: [{
      role: "user",
      content: `Create video script:\nTitle: ${intel.title}\nClassification: ${intel.classification}\nSeverity: ${intel.severity}\nSummary: ${intel.summary}`
    }]
  });

  const raw = message.content[0].text.replace(/```json|```/g, '').trim();
  return JSON.parse(raw);
}
```

### `src/agents/slackTeamsAgent.js`

```javascript
import axios from 'axios';

// Slack — Block Kit format
export async function sendSlackAlert(intel) {
  const severity_emoji = {
    CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🔵', INFO: '⚪'
  };
  const emoji = severity_emoji[intel.severity] || '⚪';

  const payload = {
    blocks: [
      {
        type: "header",
        text: { type: "plain_text", text: `${emoji} SQ1 OSINT: ${intel.classification} Alert` }
      },
      {
        type: "section",
        text: { type: "mrkdwn", text: `*${intel.title}*\n${intel.summary}` }
      },
      {
        type: "section",
        fields: [
          { type: "mrkdwn", text: `*Severity:*\n${intel.severity}` },
          { type: "mrkdwn", text: `*Type:*\n${intel.classification}` },
          { type: "mrkdwn", text: `*CVEs:*\n${(intel.cveIds || []).join(', ') || 'N/A'}` },
          { type: "mrkdwn", text: `*Source Verified:*\n${intel.sourceVerified ? '✅ Yes' : '❌ No'}` }
        ]
      },
      { type: "divider" },
      {
        type: "context",
        elements: [{ type: "mrkdwn", text: `SQ1 OSINT Platform • ${new Date().toUTCString()}` }]
      }
    ]
  };

  if (process.env.SLACK_WEBHOOK_URL) {
    await axios.post(process.env.SLACK_WEBHOOK_URL, payload);
  }
  return { platform: 'slack', sent: !!process.env.SLACK_WEBHOOK_URL, payload };
}

// Teams — messageCard format (different from Slack!)
export async function sendTeamsAlert(intel) {
  const color_map = { CRITICAL: 'FF0000', HIGH: 'FF6600', MEDIUM: 'FFCC00', LOW: '00D4FF', INFO: '888888' };

  const payload = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": color_map[intel.severity] || '888888',
    "summary": `SQ1 Alert: ${intel.title}`,
    "sections": [{
      "activityTitle": `🛡️ SQ1 OSINT — ${intel.classification} Alert`,
      "activitySubtitle": intel.title,
      "facts": [
        { "name": "Severity", "value": intel.severity },
        { "name": "Classification", "value": intel.classification },
        { "name": "CVEs", "value": (intel.cveIds || []).join(', ') || 'None' },
        { "name": "Source Verified", "value": intel.sourceVerified ? "Yes ✅" : "No ❌" }
      ],
      "text": intel.summary
    }]
  };

  if (process.env.TEAMS_WEBHOOK_URL) {
    await axios.post(process.env.TEAMS_WEBHOOK_URL, payload);
  }
  return { platform: 'teams', sent: !!process.env.TEAMS_WEBHOOK_URL, payload };
}
```

---

## ⚙️ PHASE 3 — EXPRESS BACKEND (25 min | 12:40–13:05)

```javascript
// src/api/server.js
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import campaignRoutes from './routes/campaigns.js';
import assetRoutes from './routes/assets.js';
import subscriberRoutes from './routes/subscribers.js';
import commsRoutes from './routes/comms.js';

dotenv.config();

const adapter = new JSONFile('./data/db.json');
const db = new Low(adapter, { campaigns: [], assets: [], subscribers: [] });
await db.read();

const app = express();
app.use(cors({ origin: ['http://localhost:5174', 'http://localhost:5173'] }));
app.use(express.json());

// Pass db to routes
app.use('/api/campaigns', campaignRoutes(db));
app.use('/api/assets', assetRoutes(db));
app.use('/api/subscribers', subscriberRoutes(db));
app.use('/api/comms', commsRoutes(db));

app.listen(process.env.PORT || 3002);
```

**4 route files to build:**

```javascript
// campaigns.js  — POST /generate (call emailAgent), GET /list
// assets.js     — GET /list, POST /create (call hyperframeAgent or remotionAgent)
// subscribers.js — GET /list, POST /subscribe, DELETE /:id/unsubscribe
// comms.js      — POST /alert (call slackTeamsAgent for both platforms)
```

---

## 🖥️ PHASE 4 — FRONTEND (50 min | 13:05–13:55)

Vite config for port 5174 + proxy:
```javascript
// frontend-app/vite.config.js
export default {
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/mkt': { target: 'http://localhost:3002', rewrite: (p) => p.replace(/^\/mkt/, '/api') },
      '/osint': { target: 'http://localhost:8000', rewrite: (p) => p.replace(/^\/osint/, '/api') }
    }
  }
}
```

### Component Build Order (strict — do in this sequence)

**1. `IntelQueue.jsx`** — Build this FIRST. It's the heart of the UI.
```jsx
// Polls /osint/intel/unmarketed every 30s (falls back to MOCK_INTEL)
// Each item shows: severity badge | title | summary | classification chip
// Action buttons per item:
//   📧 "Email Campaign"  → opens CampaignBuilder modal with this intel pre-loaded
//   🎨 "Create Visual"   → opens HyperFrameStudio with this intel pre-loaded  
//   🎬 "Create Video"    → opens VideoBuilder with this intel pre-loaded
//   🔔 "Alert Team"      → calls POST /mkt/comms/alert immediately
```

**2. `MarketingDashboard.jsx`** — Main home page
```jsx
// 4 stat cards:
//   📧 Emails Sent (from db.campaigns.length)
//   🎨 Assets Created (from db.assets.length)
//   👥 Subscribers (from db.subscribers.length)
//   📬 Pending Intel (from unmarketed count)
// Below stats: <IntelQueue /> component
```

**3. `HyperFrameStudio.jsx`** — Visual template generator
```jsx
// Props: intel (pre-loaded from IntelQueue or empty)
// Step 1: Select template type (6 buttons with color swatches)
// Step 2: Click "Generate Content" → POST /mkt/assets/create?type=hyperframe
//         Shows loading spinner while Claude runs
// Step 3: Preview renders the correct Template component
// Step 4: "Download PNG" button → html2canvas on the template div
// Step 5: "Save to Gallery" → POST /mkt/assets (saves to db)
```

**4. `CampaignBuilder.jsx`** — Email generator + sender
```jsx
// Props: intel (pre-loaded from IntelQueue or empty)
// Step 1: Shows intel summary, classification, severity
// Step 2: Click "Generate Email" → POST /mkt/campaigns/generate
//         Loading state while Claude runs
// Step 3: Preview: subject line, preheader, headline, body (rendered HTML)
// Step 4: Subscriber selector (checkboxes filtered by matching preferences)
// Step 5: "Send Campaign" → POST /mkt/campaigns/send (logs or actually sends)
```

**5. `SubscribePortal.jsx`** — Public subscribe page (route: /subscribe)
```jsx
// Fields:
//   Name (text)
//   Email (email, required)
//   Company (text)
//   Threat Types (checkboxes): VULNERABILITY | THREAT | BREACH | COMPLIANCE | MISINFORMATION
//   Minimum Severity (dropdown): CRITICAL only | HIGH+ | MEDIUM+ | ALL
//   Industry (dropdown): Healthcare | Finance | Tech | Retail | Government | Other
// Submit → POST /mkt/subscribers
// Show: "You're subscribed! You'll receive alerts matching your preferences."
// List current subscribers in a table below (admin view)
```

**6. `VideoBuilder.jsx`** — Remotion video preview
```jsx
// Props: intel (pre-loaded from IntelQueue or empty)
// Step 1: Select video type (30s Threat Briefing | 45s Breach Timeline | 60s CVE Explainer)
// Step 2: Click "Generate Script" → POST /mkt/assets/create?type=video
// Step 3: Show generated scene list (cards with onScreenText + narration)
// Step 4: @remotion/player renders a simple animated preview
// Note: Use a simple CyberScene component, NOT full Remotion CLI render
```

**7. `CommsPanel.jsx`** — Internal team alerts
```jsx
// Shows: Slack status (green dot if webhook configured, red if not)
// Shows: Teams status (same)
// "Send Alert to Security Team" button → POST /mkt/comms/alert
// Shows log of last 5 alerts sent (platform, time, severity)
```

**8. `AssetGallery.jsx`** — History of all created content
```jsx
// GET /mkt/assets → grid of cards
// Each card: asset type badge | title | creation date | intel classification
// Type badges: 📧 Email | 🎨 Visual | 🎬 Video
```

---

## 🎨 HYPERFRAME TEMPLATES

Each template is a React component rendered to a `1200×628px` div (OG image dimensions). 

```jsx
// Pattern for ALL templates — fill in the colors/styles per type
const BaseTemplate = ({ data, accentColor, bgGradient, label }) => (
  <div id="hyperframe-canvas" style={{
    width: 1200, height: 628,
    background: bgGradient,
    border: `2px solid ${accentColor}`,
    position: 'relative', overflow: 'hidden',
    fontFamily: "'IBM Plex Mono', monospace",
    display: 'flex', flexDirection: 'column', padding: 48
  }}>
    {/* Top bar: SQ1 logo left | classification label right */}
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 32 }}>
      <span style={{ color: '#fff', fontSize: 20, fontWeight: 700 }}>SQ1 SECURITY</span>
      <span style={{ background: accentColor, color: '#0a0e1a', padding: '4px 16px', borderRadius: 4, fontSize: 14, fontWeight: 700 }}>{label}</span>
    </div>
    
    {/* CVE Badge if present */}
    {data.cveBadge && (
      <span style={{ color: accentColor, fontSize: 14, marginBottom: 12 }}>{data.cveBadge}</span>
    )}
    
    {/* Main headline */}
    <h1 style={{ color: '#fff', fontSize: 52, lineHeight: 1.1, margin: '0 0 16px', maxWidth: 900 }}>
      {data.headline}
    </h1>
    
    {/* Subheadline */}
    <p style={{ color: '#a0aec0', fontSize: 24, margin: '0 0 24px', maxWidth: 800 }}>
      {data.subheadline}
    </p>
    
    {/* Stat highlight if present */}
    {data.statHighlight && (
      <div style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${accentColor}`, 
                    padding: '8px 20px', borderRadius: 4, display: 'inline-block', marginBottom: 24 }}>
        <span style={{ color: accentColor, fontWeight: 700, fontSize: 18 }}>{data.statHighlight}</span>
      </div>
    )}
    
    {/* Body text */}
    <p style={{ color: '#718096', fontSize: 18, maxWidth: 700, flex: 1 }}>{data.bodyText}</p>
    
    {/* Bottom: hashtags left | CTA right */}
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 32 }}>
      <span style={{ color: '#4a5568', fontSize: 14 }}>{(data.hashtags || []).map(h => `#${h}`).join(' ')}</span>
      <span style={{ background: accentColor, color: '#0a0e1a', padding: '10px 24px', borderRadius: 4, fontWeight: 700, fontSize: 16 }}>
        {data.callToAction}
      </span>
    </div>
  </div>
);

// The 6 specific templates just pass different styles to BaseTemplate:
// ThreatTemplate:     accentColor="#ff3366"  bgGradient="linear-gradient(135deg, #0a0e1a, #1a0a0a)"
// ComplianceTemplate: accentColor="#4a90e2"  bgGradient="linear-gradient(135deg, #0a0e1a, #0a0a1a)"
// VulnTemplate:       accentColor="#ffcc00"  bgGradient="linear-gradient(135deg, #0a0e1a, #1a1000)"
// BreachTemplate:     accentColor="#ff6600"  bgGradient="linear-gradient(135deg, #050505, #0a0501)"
// MisinfoTemplate:    accentColor="#00ff88"  bgGradient="linear-gradient(135deg, #0a0e1a, #0a1a0a)"
// DigestTemplate:     accentColor="#a855f7"  bgGradient="linear-gradient(135deg, #0a0e1a, #0f0a1a)"
```

**Download as PNG:**
```jsx
import html2canvas from 'html2canvas';

const downloadPNG = async () => {
  const el = document.getElementById('hyperframe-canvas');
  const canvas = await html2canvas(el, { scale: 1, useCORS: true });
  const link = document.createElement('a');
  link.download = `sq1-${intelType}-${Date.now()}.png`;
  link.href = canvas.toDataURL();
  link.click();
};
```

---

## 🎬 REMOTION VIDEO PREVIEW SETUP

```jsx
// frontend-app/src/components/CyberVideoComposition.jsx
import { AbsoluteFill, useCurrentFrame, interpolate, Sequence } from 'remotion';

const SceneView = ({ scene, startFrame, totalFrames }) => {
  const frame = useCurrentFrame();
  const progress = (frame - startFrame) / totalFrames;
  const opacity = interpolate(frame - startFrame, [0, 10], [0, 1]);

  const bgStyles = {
    dark_grid: { background: '#0a0e1a', backgroundImage: 'repeating-linear-gradient(0deg, #1e3a5f33 0px, #1e3a5f33 1px, transparent 1px, transparent 40px), repeating-linear-gradient(90deg, #1e3a5f33 0px, #1e3a5f33 1px, transparent 1px, transparent 40px)' },
    red_pulse: { background: `radial-gradient(circle, #ff336620 0%, #0a0e1a 70%)` },
    blue_wave: { background: 'linear-gradient(135deg, #0a0e1a, #0a0a2a)' },
    amber_static: { background: 'linear-gradient(135deg, #0a0e1a, #1a1000)' },
    matrix_rain: { background: '#050505' }
  };

  return (
    <AbsoluteFill style={{ ...bgStyles[scene.bgStyle], opacity, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: 80 }}>
      <p style={{ color: '#4a90e2', fontFamily: 'monospace', fontSize: 18, marginBottom: 24 }}>SQ1 SECURITY INTELLIGENCE</p>
      <h1 style={{ color: '#fff', fontSize: 64, textAlign: 'center', lineHeight: 1.1 }}>{scene.onScreenText}</h1>
      <p style={{ color: '#a0aec0', fontSize: 24, textAlign: 'center', marginTop: 32, maxWidth: 800 }}>{scene.narration}</p>
    </AbsoluteFill>
  );
};

export const CyberVideoComposition = ({ scenes = [] }) => {
  let frameOffset = 0;
  return (
    <AbsoluteFill style={{ background: '#0a0e1a' }}>
      {scenes.map((scene, i) => {
        const sceneDuration = scene.durationSeconds * 30;
        const comp = (
          <Sequence key={i} from={frameOffset} durationInFrames={sceneDuration}>
            <SceneView scene={scene} startFrame={frameOffset} totalFrames={sceneDuration} />
          </Sequence>
        );
        frameOffset += sceneDuration;
        return comp;
      })}
    </AbsoluteFill>
  );
};
```

```jsx
// In VideoBuilder.jsx — render player:
import { Player } from '@remotion/player';
import { CyberVideoComposition } from './CyberVideoComposition';

const totalFrames = (script?.durationSeconds || 30) * 30;

<Player
  component={CyberVideoComposition}
  inputProps={{ scenes: script?.scenes || [] }}
  durationInFrames={totalFrames}
  fps={30}
  compositionWidth={1280}
  compositionHeight={720}
  style={{ width: '100%', borderRadius: 8 }}
  controls
/>
```

---

## 📄 ROADMAP.md — CREATE THIS FIRST

```markdown
# SQ1 Marketing Module — Roadmap
## Hackathon MVP (due 14:40)
- [x] Forked repo, created marketing/ directory
- [ ] Mock intel data (intelMockData.js)
- [ ] Agent 2: Email generator (Claude + nodemailer)
- [ ] Agent 2: Subscribe to threats (form + storage)
- [ ] Agent 3: HyperFrame — 6 visual templates
- [ ] Agent 3: Claude content generator
- [ ] Agent 3: PNG download (html2canvas)
- [ ] Agent 4: Video script generator (Claude)
- [ ] Agent 4: Remotion player preview
- [ ] Agent 5: Slack Block Kit alert
- [ ] Agent 5: Teams messageCard alert
- [ ] Marketing Dashboard UI
- [ ] Intel Queue UI (core of the app)
- [ ] Asset Gallery UI

## Post-Hackathon v2
- Real SendGrid/Mailgun email delivery
- LinkedIn + Twitter auto-post integration
- Email open/click rate tracking
- A/B testing for templates
- Scheduled campaign calendar
- Brand kit customization per company
- MP4 video export via Remotion CLI
```

---

## ✅ TODO.md — CREATE THIS FIRST

```markdown
# SQ1 Marketing Module — TODO

## 🔴 P0 — Must Ship
- [ ] mock/intelMockData.js (5 items, all types)
- [ ] emailAgent.js — Claude call + JSON parse
- [ ] hyperframeAgent.js — Claude call + JSON parse
- [ ] slackTeamsAgent.js — Slack Block Kit + Teams messageCard
- [ ] Express server.js + 4 route files
- [ ] lowdb setup
- [ ] IntelQueue.jsx — core queue UI
- [ ] MarketingDashboard.jsx — stats + queue
- [ ] HyperFrameStudio.jsx — template picker + preview
- [ ] SubscribePortal.jsx — subscribe form
- [ ] CommsPanel.jsx — Slack + Teams alert button
- [ ] All 6 HyperFrame template components

## 🟡 P1 — Should Ship
- [ ] CampaignBuilder.jsx — email preview + send
- [ ] VideoBuilder.jsx — Remotion player
- [ ] remotionAgent.js — video script via Claude
- [ ] AssetGallery.jsx — history grid
- [ ] Connect to Person 1's live API

## 🟢 P2 — Nice to Have
- [ ] html2canvas PNG download working
- [ ] Subscriber preference matching (auto-queue)
- [ ] Animated loading skeleton while Claude generates
```

---

## ⏱️ TIME & TOKEN ESTIMATE

| Phase | Time | Claude Tokens |
|-------|------|--------------|
| Setup + mock data | 15 min | ~2K |
| 4 agent backends | 45 min | ~30K |
| Express API | 25 min | ~15K |
| Frontend components | 50 min | ~50K |
| Polish + integration | 25 min | ~20K |
| Debugging iteration | 20 min | ~25K |
| **Total** | **180 min** | **~142K tokens** |

**Build session cost:** ~$1.60–$2.20  
**Runtime per email gen:** ~2,000 tokens (~$0.02)  
**Runtime per HyperFrame gen:** ~1,000 tokens (~$0.01)  
**Runtime per video script:** ~1,500 tokens (~$0.015)  

---

## 🔌 INTEGRATION WITH PERSON 1 (at 13:45)

At 13:45, swap `MOCK_INTEL` for live calls. Only change needed:

```javascript
// src/frontend/hooks/useIntel.js
const USE_MOCK = false; // Switch this from true → false at 13:45

export const useIntel = () => {
  if (USE_MOCK) return MOCK_INTEL;
  return fetch('/osint/intel/unmarketed').then(r => r.json());
};
```

Also call `POST /osint/intel/{id}/mark-used` after creating any asset — this removes the item from Person 1's unmarketed queue.

---

## ⚠️ CRITICAL RULES

1. **Use `claude-sonnet-4-6`** in all agents
2. **Always wrap** `JSON.parse()` in try/catch + strip markdown fences: `.replace(/\`\`\`json|\`\`\`/g, '').trim()`
3. **Never wait for Person 1** — mock data must work day 1
4. **Remotion Player only** — no CLI render (takes minutes, we don't have time)
5. **html2canvas** — test early with a simple div; it breaks with some CSS gradients
6. **Teams webhook format** is `messageCard`, NOT the same as Slack — different JSON schema entirely
7. **Run on port 5174** — do NOT use 5173 (Person 1 uses that)
8. **Seed subscribers**: add 5 demo subscribers with different preferences in db.json at startup
9. **The Intel Queue is your demo centerpiece** — judges will click "Create Visual" and expect something to happen

Good luck. Build fast. Market the threats. 📣
