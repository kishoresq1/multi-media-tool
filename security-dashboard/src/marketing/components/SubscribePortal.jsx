import { useState } from 'react';
import { UserPlus } from 'lucide-react';
import { subscribe } from '../api/marketingApi.js';

const TYPES = ['VULNERABILITY', 'THREAT', 'BREACH', 'COMPLIANCE', 'MISINFORMATION'];
const INDUSTRIES = ['Healthcare', 'Finance', 'Tech', 'Retail', 'Government', 'Other'];

export default function SubscribePortal({ subscribers, onSubscriberAdded }) {
  const [form, setForm] = useState({
    name: '',
    email: '',
    company: '',
    threatTypes: ['THREAT'],
    minimumSeverity: 'HIGH+',
    industry: 'Tech'
  });
  const [message, setMessage] = useState('');

  async function submit(event) {
    event.preventDefault();
    try {
      const result = await subscribe(form);
      setMessage(`${result.subscriber.email} is subscribed.`);
      onSubscriberAdded?.();
    } catch {
      setMessage('Subscription failed. Check the email address and try again.');
    }
  }

  function toggleType(type) {
    setForm((current) => ({
      ...current,
      threatTypes: current.threatTypes.includes(type)
        ? current.threatTypes.filter((item) => item !== type)
        : [...current.threatTypes, type]
    }));
  }

  return (
    <section className="panel two-column">
      <form onSubmit={submit}>
        <p className="eyebrow">Subscribe Portal</p>
        <h2>Threat Preferences</h2>
        <label>
          Name
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </label>
        <label>
          Email
          <input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </label>
        <label>
          Company
          <input
            value={form.company}
            onChange={(e) => setForm({ ...form, company: e.target.value })}
          />
        </label>
        <div className="checkbox-grid">
          {TYPES.map((type) => (
            <label key={type} className="check-row">
              <input
                type="checkbox"
                checked={form.threatTypes.includes(type)}
                onChange={() => toggleType(type)}
              />
              {type}
            </label>
          ))}
        </div>
        <label>
          Minimum Severity
          <select
            value={form.minimumSeverity}
            onChange={(e) => setForm({ ...form, minimumSeverity: e.target.value })}
          >
            <option>CRITICAL only</option>
            <option>HIGH+</option>
            <option>MEDIUM+</option>
            <option>ALL</option>
          </select>
        </label>
        <label>
          Industry
          <select
            value={form.industry}
            onChange={(e) => setForm({ ...form, industry: e.target.value })}
          >
            {INDUSTRIES.map((industry) => (
              <option key={industry}>{industry}</option>
            ))}
          </select>
        </label>
        <button className="primary-action" type="submit">
          <UserPlus size={16} />
          Subscribe
        </button>
        {message && <div className="notice inline" role="status">{message}</div>}
      </form>
      <div>
        <p className="eyebrow">Audience</p>
        <h2>Current Subscribers</h2>
        <div className="subscriber-table">
          {subscribers.length === 0 ? (
            <div className="empty-state compact-empty">No subscribers yet.</div>
          ) : subscribers.map((subscriber) => (
            <div className="subscriber-row" key={subscriber.id}>
              <strong>{subscriber.email}</strong>
              <span>{subscriber.industry} - {subscriber.minimumSeverity}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
