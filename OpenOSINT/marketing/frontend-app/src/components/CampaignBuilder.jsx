import { useEffect, useState } from 'react';
import { Mail, Send } from 'lucide-react';
import { createCampaign, sendCampaign } from '../api/marketingApi.js';

const FIXED_RECIPIENT = {
  id: 'fixed-crazywe2119',
  email: 'crazywe2119@gmail.com',
  name: 'Campaign Recipient',
  company: 'SQ1'
};

export default function CampaignBuilder({ intel }) {
  const [campaign, setCampaign] = useState(null);
  const [record, setRecord] = useState(null);
  const [sendStatus, setSendStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (!intel) return;
    setCampaign(null);
    setRecord(null);
    setSendStatus('');
    setSending(false);
    // Generation only happens when the user explicitly clicks "Generate email".
  }, [intel?.id]);

  async function generate() {
    if (!intel || loading || sending) return;
    setLoading(true);
    try {
      const result = await createCampaign(intel);
      setCampaign(result.campaign);
      setRecord(result.record || null);
    } finally {
      setLoading(false);
    }
  }

  async function send() {
    if (!record?.id || sending) return;
    const recipients = [FIXED_RECIPIENT];
    setSending(true);
    setSendStatus(`Sending campaign to ${FIXED_RECIPIENT.email}.`);
    try {
      const result = await sendCampaign(record.id, recipients);
      setRecord(result.campaign);
      setSendStatus(formatDeliveryStatus(result.emailDelivery));
    } catch {
      setSendStatus('Campaign send failed. Please try again.');
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="panel two-column">
      <div>
        <p className="eyebrow">Campaign Builder</p>
        <h2>Email Campaign</h2>
        <IntelSummary intel={intel} />
        <button className="primary-action" onClick={generate} disabled={!intel || loading || sending}>
          <Mail size={16} />
          {loading ? 'Generating email' : 'Generate email'}
        </button>
        {loading && !campaign ? (
          <RecipientSkeleton />
        ) : campaign && (
          <div className="recipient-panel">
            <p className="eyebrow">Campaign Recipient</p>
            <div className="check-row">
              <input type="checkbox" checked readOnly />
              <span>
                {FIXED_RECIPIENT.email}
                <small>Fixed SQ1 delivery recipient</small>
              </span>
            </div>
          </div>
        )}
      </div>
      <div className="preview-pane" aria-busy={loading || sending}>
        {loading && !campaign ? (
          <CampaignPreviewSkeleton />
        ) : campaign ? (
          <>
            <span className="source-chip">{campaign.tone}</span>
            <h3>{campaign.subject}</h3>
            <p className="muted">{campaign.preheader}</p>
            <h4>{campaign.headline}</h4>
            <SafeEmailBody html={campaign.body} />
            <button
              className="secondary-action"
              onClick={send}
              disabled={!record?.id || sending}
            >
              <Send size={15} />
              {sending ? 'Sending campaign' : 'Send campaign'}
            </button>
            {sendStatus && (
              <div className="notice inline" role="status">
                {sendStatus}
              </div>
            )}
          </>
        ) : (
          <div className="empty-state">Select intel from the queue, then generate a campaign.</div>
        )}
      </div>
    </section>
  );
}

function formatDeliveryStatus(delivery) {
  if (delivery?.sent) {
    return `Email sent to ${delivery.to || FIXED_RECIPIENT.email}.`;
  }
  if (delivery?.reason === 'smtp-not-configured') {
    return 'Campaign logged, but email was not sent. Configure EMAIL_USER and EMAIL_PASS in marketing/.env.';
  }
  if (delivery?.error) {
    return `Email send failed: ${delivery.error}`;
  }
  return `Campaign logged for ${FIXED_RECIPIENT.email}.`;
}

function RecipientSkeleton() {
  return (
    <div className="recipient-panel" aria-hidden="true">
      <p className="eyebrow">Matching Subscribers</p>
      <SkeletonLine width="72%" />
      <SkeletonLine width="58%" />
      <SkeletonLine width="66%" />
    </div>
  );
}

function CampaignPreviewSkeleton() {
  return (
    <div role="status" aria-label="Generating email campaign">
      <SkeletonLine width="92px" height={22} />
      <SkeletonLine width="78%" height={28} />
      <SkeletonLine width="62%" />
      <div style={{ marginTop: 18 }}>
        <SkeletonLine width="48%" height={20} />
        <SkeletonLine width="96%" />
        <SkeletonLine width="88%" />
        <SkeletonLine width="72%" />
      </div>
    </div>
  );
}

function SkeletonLine({ width = '100%', height = 14 }) {
  return (
    <span
      style={{
        display: 'block',
        width,
        height,
        margin: '0 0 10px',
        borderRadius: 6,
        background: 'oklch(0.88 0.012 83)'
      }}
    />
  );
}

function SafeEmailBody({ html }) {
  return (
    <div
      className="email-body"
      dangerouslySetInnerHTML={{ __html: sanitizeEmailHtml(html) }}
    />
  );
}

function sanitizeEmailHtml(html = '') {
  const allowed = new Set(['P', 'STRONG', 'EM', 'BR', 'UL', 'OL', 'LI']);
  const doc = new DOMParser().parseFromString(String(html), 'text/html');
  doc.body.querySelectorAll('*').forEach((node) => {
    if (!allowed.has(node.tagName)) {
      node.replaceWith(doc.createTextNode(node.textContent || ''));
      return;
    }
    [...node.attributes].forEach((attribute) => node.removeAttribute(attribute.name));
  });
  return doc.body.innerHTML;
}

export function IntelSummary({ intel }) {
  if (!intel) return <div className="empty-state">No intel selected.</div>;
  return (
    <div className="intel-summary">
      <span className="classification">{intel.classification}</span>
      <span className="severity high">{intel.severity}</span>
      <h3>{intel.title}</h3>
      <p>{intel.summary}</p>
    </div>
  );
}
