import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { resolve } from 'node:path';
import { normalizeDb, seedSubscribers } from './db.js';
import intelRoutes from './routes/intel.js';
import campaignRoutes from './routes/campaigns.js';
import assetRoutes from './routes/assets.js';
import subscriberRoutes from './routes/subscribers.js';
import commsRoutes from './routes/comms.js';

dotenv.config();

export function createApp({ db, osintApiUrl = process.env.OSINT_API_URL || 'http://127.0.0.1:8000' }) {
  normalizeDb(db);
  void seedSubscribers(db);

  const app = express();
  app.disable('x-powered-by');
  app.use(
    cors({
      origin: ['http://localhost:5174', 'http://127.0.0.1:5174', 'http://localhost:5173']
    })
  );
  app.use(express.json({ limit: '1mb' }));
  app.use(requireTokenWhenConfigured);

  const intel = intelRoutes({ osintApiUrl });
  const campaigns = campaignRoutes(db, { osintApiUrl });
  const assets = assetRoutes(db, { osintApiUrl });
  const subscribers = subscriberRoutes(db);
  const comms = commsRoutes(db);

  app.get('/api/health', (_req, res) => {
    res.json({
      status: 'ok',
      service: 'sq1-marketing',
      mode: process.env.MARKETING_ENABLE_MOCK_INTEL === 'true' ? 'mock' : 'portal',
      emailConfigured: Boolean(process.env.EMAIL_USER && process.env.EMAIL_PASS)
    });
  });

  app.get('/api/intel/marketing-queue', intel.getUnmarketed);
  app.get('/api/intel/unmarketed', intel.getUnmarketed);

  app.post('/api/campaigns/generate', campaigns.generate);
  app.get('/api/campaigns/list', campaigns.list);
  app.post('/api/campaigns/send', campaigns.send);

  app.get('/api/assets/list', assets.list);
  app.get('/api/assets', assets.list);
  app.get('/api/assets/search', assets.search);
  app.post('/api/assets/create', assets.create);
  app.post('/api/assets/:id/video', express.raw({ type: 'application/octet-stream', limit: '80mb' }), assets.uploadVideo);
  app.post('/api/assets/:id/image', assets.uploadImage);
  app.post('/api/assets', assets.save);

  // Serve saved asset files (images + video JSON) from the runtime dir
  app.use('/api/assets/files', express.static(resolve('.runtime/assets'), { dotfiles: 'deny' }));

  app.get('/api/subscribers/list', subscribers.list);
  app.get('/api/subscribers', subscribers.list);
  app.post('/api/subscribers/subscribe', subscribers.subscribe);
  app.post('/api/subscribers', subscribers.subscribe);
  app.delete('/api/subscribers/:id/unsubscribe', subscribers.unsubscribe);

  app.post('/api/comms/alert', comms.alert);
  app.get('/api/comms/alerts', comms.list);

  return app;
}

function requireTokenWhenConfigured(req, res, next) {
  const token = process.env.MARKETING_API_TOKEN;
  if (!token) return next();
  const isReadOnly = req.method === 'GET' && !req.path.includes('/subscribers');
  if (req.path === '/api/health' || isReadOnly) return next();
  const provided = req.get('authorization')?.replace(/^Bearer\s+/i, '');
  if (provided !== token) {
    return res.status(401).json({ error: 'marketing API token required' });
  }
  return next();
}
