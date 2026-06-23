import { Image, Mail, Radio, Users } from 'lucide-react';
import IntelQueue from './IntelQueue.jsx';

export default function MarketingDashboard({
  intelItems,
  subscribers,
  assets,
  campaigns,
  loading,
  feedSource,
  onOpenTool,
  onNotice
}) {
  const stats = [
    { label: 'Pending Intel', value: intelItems.length, icon: Radio },
    { label: 'Assets Created', value: assets.length, icon: Image },
    { label: 'Subscribers', value: subscribers.length, icon: Users },
    { label: 'Emails Sent', value: campaigns.filter((campaign) => campaign.sentAt).length, icon: Mail }
  ];

  return (
    <section className="dashboard-grid">
      <div className="stats-row">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div className="stat-card" key={stat.label}>
              <Icon size={18} />
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </div>
          );
        })}
      </div>
      <IntelQueue
        items={intelItems}
        subscribers={subscribers}
        loading={loading}
        feedSource={feedSource}
        onOpenTool={onOpenTool}
        onNotice={onNotice}
      />
    </section>
  );
}
