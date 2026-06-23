import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import App from '../frontend-app/src/App.jsx';

const fetchMock = vi.fn();

beforeEach(() => {
  window.history.pushState({}, '', '/');
  fetchMock.mockReset();
  global.fetch = fetchMock;
  fetchMock.mockImplementation(async (url, options = {}) => {
    if (url.includes('/intel/marketing-queue')) {
      return jsonResponse({
        source: 'live',
        items: [
          {
            id: 'intel-001',
            title: 'Critical Apache RCE',
            classification: 'VULNERABILITY',
            severity: 'CRITICAL',
            summary: 'Patch immediately.',
            cveIds: ['CVE-2024-38476'],
            tags: ['apache'],
            timestamp: '2026-06-12T00:00:00.000Z',
            sourceVerified: true,
            isMisinformation: false,
            usedInMarketing: false,
            readyForMarketing: true
          }
        ]
      });
    }
    if (url.includes('/campaigns/generate')) {
      return jsonResponse({
        record: {
          id: 'campaign-001',
          intelId: 'intel-001',
          intelTitle: 'Critical Apache RCE',
          createdAt: '2026-06-12T00:00:00.000Z'
        },
        campaign: {
          subject: 'Critical Apache RCE requires action',
          preheader: 'Patch immediately.',
          headline: 'Critical Apache RCE',
          body: '<p>Patch immediately.</p>',
          cta_text: 'Review Exposure',
          recommended_action: 'Patch now',
          tone: 'urgent',
          template_type: 'vuln'
        }
      });
    }
    if (url.includes('/campaigns/send')) {
      const body = JSON.parse(options.body);
      return jsonResponse({
        success: true,
        emailDelivery: {
          attempted: false,
          sent: false,
          reason: 'smtp-not-configured'
        },
        campaign: {
          id: body.campaignId,
          recipients: body.recipients,
          sentAt: '2026-06-12T00:00:00.000Z'
        }
      });
    }
    if (url.includes('/assets/create')) {
      if (url.includes('type=video')) {
        return jsonResponse({
          asset: {
            id: 'video-001',
            kind: 'video',
            content: {
              title: 'Critical Apache RCE',
              durationSeconds: 5,
              scenes: [
                {
                  sceneNumber: 1,
                  durationSeconds: 5,
                  onScreenText: 'New Intel Detected',
                  narration: 'Patch affected servers now.',
                  visualNote: 'Dark SOC grid.',
                  bgStyle: 'dark_grid'
                }
              ],
              closingCta: 'Review Now'
            },
            intel: { id: 'intel-001', classification: 'VULNERABILITY', title: 'Critical Apache RCE' }
          }
        });
      }
      return jsonResponse({
        asset: {
          id: 'asset-001',
          kind: 'hyperframe',
          content: {
            headline: 'Apache RCE Alert',
            subheadline: 'Patch affected servers now',
            bodyText: 'Active exploitation requires rapid response.',
            severityLabel: 'CRITICAL VULNERABILITY',
            cveBadge: 'CVE-2024-38476',
            hashtags: ['apache', 'rce', 'security'],
            callToAction: 'Patch Now',
            colorScheme: 'vuln_amber',
            statHighlight: 'Critical'
          },
          intel: { id: 'intel-001', classification: 'VULNERABILITY', title: 'Critical Apache RCE' }
        }
      });
    }
    if (url.includes('/comms/alerts')) {
      return jsonResponse({
        channels: { slackConfigured: false, teamsConfigured: false },
        alerts: [
          {
            id: 'alert-001',
            title: 'Prior Alert',
            severity: 'HIGH',
            classification: 'THREAT',
            createdAt: '2026-06-12T00:00:00.000Z'
          }
        ]
      });
    }
    if (url.includes('/comms/alert')) {
      return jsonResponse({
        results: {
          slack: { sent: false, payload: { blocks: [] } },
          teams: { sent: false, payload: { '@type': 'MessageCard' } }
        }
      });
    }
    if (url.includes('/subscribers/list')) {
      return jsonResponse({
        subscribers: [
          {
            id: 'sub-001',
            name: 'Maya',
            email: 'ma***@caregrid.example',
            company: 'CareGrid',
            threatTypes: ['VULNERABILITY', 'THREAT'],
            minimumSeverity: 'HIGH+',
            industry: 'Healthcare'
          }
        ]
      });
    }
    if (url.includes('/subscribers/subscribe')) {
      const body = JSON.parse(options.body);
      return jsonResponse({
        subscriber: {
          id: 'sub-new',
          ...body
        }
      });
    }
    if (url.includes('/assets/list')) {
      return jsonResponse({
        assets: [
          {
            id: 'asset-stored',
            kind: 'hyperframe',
            createdAt: '2026-06-12T00:00:00.000Z',
            intel: { title: 'Stored Threat Visual', classification: 'THREAT' }
          }
        ]
      });
    }
    if (url.includes('/campaigns/list')) {
      return jsonResponse({
        campaigns: [
          {
            id: 'campaign-stored',
            intelTitle: 'Stored Email Campaign',
            createdAt: '2026-06-12T00:00:00.000Z',
            sentAt: '2026-06-12T00:00:00.000Z'
          }
        ]
      });
    }
    if (url.includes('/health')) {
      return jsonResponse({ status: 'ok' });
    }
    if (options.method === 'POST') {
      return jsonResponse({ success: true });
    }
    return jsonResponse({});
  });
});

function jsonResponse(body) {
  return Promise.resolve({
    ok: true,
    status: 200,
    json: async () => body
  });
}

describe('Marketing app', () => {
  test('renders the portal-approved intel queue on the first screen', async () => {
    render(<App />);

    expect(await screen.findByText('Critical Apache RCE')).toBeInTheDocument();
    expect(screen.getByText('SQ1 portal queue')).toBeInTheDocument();
  });

  test('can generate an email campaign from a queue item', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: /email campaign/i }));
    fireEvent.click(await screen.findByRole('button', { name: /generate email/i }));

    await waitFor(() => {
      expect(screen.getByText('Critical Apache RCE requires action')).toBeInTheDocument();
    });
    const campaignCall = fetchMock.mock.calls.find(([url]) => url.includes('/api/campaigns/generate'));
    expect(campaignCall).toBeUndefined();
    const mktCampaignCall = fetchMock.mock.calls.find(([url]) => url.includes('/mkt/campaigns/generate'));
    expect(mktCampaignCall[1].method).toBe('POST');
    expect(JSON.parse(mktCampaignCall[1].body).intel.id).toBe('intel-001');
  });

  test('can send an email campaign to matching subscribers', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: /email campaign/i }));
    fireEvent.click(await screen.findByRole('button', { name: /generate email/i }));

    await waitFor(() => {
      expect(screen.getByText('Critical Apache RCE requires action')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /send campaign/i }));

    await waitFor(() => {
      expect(screen.getByText(/campaign logged, but email was not sent/i)).toBeInTheDocument();
    });
    const sendCall = fetchMock.mock.calls.find(([url]) => url.includes('/mkt/campaigns/send'));
    expect(JSON.parse(sendCall[1].body).campaignId).toBe('campaign-001');
  });

  test('uses the /mkt proxy prefix for marketing API calls', async () => {
    render(<App />);

    await screen.findByText('Critical Apache RCE');

    expect(fetchMock.mock.calls.some(([url]) => String(url).startsWith('/mkt/'))).toBe(true);
    expect(fetchMock.mock.calls.some(([url]) => String(url).startsWith('/api/'))).toBe(false);
  });

  test('opens the subscribe portal at /subscribe', async () => {
    window.history.pushState({}, '', '/subscribe');
    render(<App />);

    expect(await screen.findByRole('heading', { name: /threat preferences/i })).toBeInTheDocument();
  });

  test('can create a visual asset from a queue item', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: /create visual/i }));
    fireEvent.click(await screen.findByRole('button', { name: /generate content/i }));

    await waitFor(() => {
      expect(screen.getByText('Apache RCE Alert')).toBeInTheDocument();
    });
    const assetCall = fetchMock.mock.calls.find(([url]) => url.includes('/mkt/assets/create'));
    expect(assetCall[0]).toContain('type=hyperframe');
    expect(JSON.parse(assetCall[1].body).intel.id).toBe('intel-001');
  });

  test('can generate a video script from a queue item', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: /5s visual/i }));
    fireEvent.click(await screen.findByRole('button', { name: /generate 5s visual/i }));

    await waitFor(() => {
      expect(screen.getAllByText('New Intel Detected').length).toBeGreaterThan(0);
    });
    expect(screen.getByRole('button', { name: /5s micro visual/i })).toBeInTheDocument();
    const videoCall = fetchMock.mock.calls.find(([url]) => url.includes('/mkt/assets/create?type=video'));
    expect(JSON.parse(videoCall[1].body).type).toBe('video');
    expect(JSON.parse(videoCall[1].body).intel.requestedDurationSeconds).toBe(5);
  });

  test('can trigger a team alert from a queue item', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: /alert team/i }));

    await waitFor(() => {
      expect(screen.getByText(/alert payload prepared/i)).toBeInTheDocument();
    });
  });

  test('Comms Panel send action renders payload preview', async () => {
    render(<App />);

    fireEvent.click(await screen.findByRole('button', { name: /alert team/i }));
    fireEvent.click(await screen.findByRole('button', { name: /send alert to security team/i }));

    await waitFor(() => {
      expect(screen.getByText(/"slack"/i)).toBeInTheDocument();
    });
    expect(screen.getByText('Prior Alert')).toBeInTheDocument();
  });

  test('can submit a subscriber from the Subscribe Portal', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /subscribers/i }));
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'new@example.com' } });
    fireEvent.click(screen.getByRole('button', { name: /^subscribe$/i }));

    await waitFor(() => {
      const subscribeCall = fetchMock.mock.calls.find(([url]) =>
        url.includes('/mkt/subscribers/subscribe')
      );
      expect(JSON.parse(subscribeCall[1].body).email).toBe('new@example.com');
    });
  });

  test('Asset Gallery renders stored assets', async () => {
    render(<App />);

    fireEvent.click(screen.getByRole('button', { name: /gallery/i }));

    expect(await screen.findByText('Stored Threat Visual')).toBeInTheDocument();
    expect(screen.getByText('Stored Email Campaign')).toBeInTheDocument();
    expect(screen.getByText('Visual')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
  });
});
