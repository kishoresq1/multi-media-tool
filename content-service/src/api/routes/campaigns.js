import { randomUUID } from 'node:crypto';
import { Resend } from 'resend';
import { generateEmail } from '../../agents/emailAgent.js';
import { persist } from '../db.js';
import { markLiveIntelUsed } from '../osintClient.js';
import { makeLogger } from '../../utils/logger.js';

const log = makeLogger('CampaignsRoute');

export const FIXED_CAMPAIGN_RECIPIENT = {
  id: 'fixed-aaddy18',
  email: process.env.CAMPAIGN_RECIPIENT_EMAIL || 'aaddy18@gmail.com',
  name: 'Campaign Recipient',
  company: 'SQ1'
};

export default function campaignRoutes(db, { osintApiUrl } = {}) {
  async function generate(req, res) {
    const intel = req.body?.intel;
    if (!intel?.id || !intel?.title) {
      log.warn('Campaign generation rejected — missing intel id or title');
      return res.status(400).json({ error: 'intel with id and title is required' });
    }

    log.info('Campaign generation started', { intelId: intel.id, title: intel.title });
    const campaign = await generateEmail(intel);
    const record = {
      id: randomUUID(),
      intelId: intel.id,
      intelTitle: intel.title,
      createdAt: new Date().toISOString(),
      recipients: [FIXED_CAMPAIGN_RECIPIENT],
      campaign
    };
    db.data.campaigns.push(record);
    await persist(db);
    const markUsed = await markLiveIntelUsed(intel.id, osintApiUrl);
    log.info('Campaign created and persisted', { campaignId: record.id, intelId: intel.id });
    return res.json({ campaign, record, markUsed });
  }

  function list(_req, res) {
    return res.json({ campaigns: db.data.campaigns });
  }

  async function send(req, res) {
    const campaignId = req.body?.campaignId;
    const record = db.data.campaigns.find((item) => item.id === campaignId);
    if (!record) return res.status(404).json({ error: 'campaign not found' });
    record.sentAt = new Date().toISOString();
    record.recipients = [FIXED_CAMPAIGN_RECIPIENT];
    const emailDelivery = await deliverCampaignEmail(record);
    record.emailDelivery = emailDelivery;
    await persist(db);
    return res.json({ success: true, campaign: record, recipients: record.recipients, emailDelivery });
  }

  return { generate, list, send };
}

async function deliverCampaignEmail(record) {
  if (!process.env.RESEND_API_KEY) {
    return { attempted: false, sent: false, reason: 'resend-not-configured' };
  }

  const resend = new Resend(process.env.RESEND_API_KEY);
  const from = process.env.EMAIL_FROM || 'SQ1 Security <onboarding@resend.dev>';
  const subject = record.campaign?.subject || record.intelTitle || 'SQ1 Security Alert';
  const html = record.campaign?.body || `<p>${record.campaign?.headline || record.intelTitle}</p>`;

  try {
    const { data, error } = await resend.emails.send({
      from,
      to: FIXED_CAMPAIGN_RECIPIENT.email,
      subject,
      html,
      text: stripHtml(html)
    });

    if (error) {
      return { attempted: true, sent: false, error: error.message, to: FIXED_CAMPAIGN_RECIPIENT.email };
    }

    return { attempted: true, sent: true, messageId: data?.id || null, to: FIXED_CAMPAIGN_RECIPIENT.email };
  } catch (err) {
    return { attempted: true, sent: false, error: err?.message || 'send-failed', to: FIXED_CAMPAIGN_RECIPIENT.email };
  }
}

function stripHtml(value) {
  return String(value).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
}
