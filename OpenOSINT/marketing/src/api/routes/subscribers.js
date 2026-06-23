import { randomUUID } from 'node:crypto';
import { persist } from '../db.js';
import { maskEmail } from '../../utils/safety.js';

const VALID_SEVERITY = new Set(['CRITICAL only', 'HIGH+', 'MEDIUM+', 'ALL']);

export default function subscriberRoutes(db) {
  function list(_req, res) {
    return res.json({ subscribers: db.data.subscribers.map(publicSubscriber) });
  }

  async function subscribe(req, res) {
    const body = req.body || {};
    if (!body.email || !String(body.email).includes('@')) {
      return res.status(400).json({ error: 'valid email is required' });
    }
    const subscriber = {
      id: randomUUID(),
      name: body.name || '',
      email: String(body.email).trim().toLowerCase(),
      company: body.company || '',
      threatTypes: Array.isArray(body.threatTypes) ? body.threatTypes : [],
      minimumSeverity: VALID_SEVERITY.has(body.minimumSeverity) ? body.minimumSeverity : 'ALL',
      industry: body.industry || 'Other',
      createdAt: new Date().toISOString()
    };
    db.data.subscribers.push(subscriber);
    await persist(db);
    return res.status(201).json({ subscriber });
  }

  async function unsubscribe(req, res) {
    const before = db.data.subscribers.length;
    db.data.subscribers = db.data.subscribers.filter((item) => item.id !== req.params.id);
    await persist(db);
    return res.json({ success: db.data.subscribers.length < before });
  }

  return { list, subscribe, unsubscribe };
}

function publicSubscriber(subscriber) {
  return {
    id: subscriber.id,
    name: subscriber.name,
    email: maskEmail(subscriber.email),
    company: subscriber.company,
    threatTypes: subscriber.threatTypes,
    minimumSeverity: subscriber.minimumSeverity,
    industry: subscriber.industry,
    createdAt: subscriber.createdAt
  };
}
