import { randomUUID } from 'node:crypto';
import { generateHyperframeContent } from '../../agents/hyperframeAgent.js';
import { generateVideoScript } from '../../agents/remotionAgent.js';
import { persist } from '../db.js';
import { markLiveIntelUsed } from '../osintClient.js';
import { makeLogger } from '../../utils/logger.js';
import { saveImageJson, saveImagePng, saveVideoFile } from '../../utils/storage.js';

const log = makeLogger('AssetsRoute');

export default function assetRoutes(db, { osintApiUrl } = {}) {
  function list(_req, res) {
    return res.json({ assets: db.data.assets });
  }

  function search(req, res) {
    const q = (req.query?.q || '').toLowerCase().trim();
    const kind = (req.query?.kind || '').toLowerCase().trim();

    let results = [...db.data.assets].reverse(); // newest first

    if (kind === 'video' || kind === 'hyperframe') {
      results = results.filter((a) => a.kind === kind);
    }

    if (q) {
      results = results.filter((a) => {
        const title = (a.intel?.title || '').toLowerCase();
        const classification = (a.intel?.classification || '').toLowerCase();
        const severity = (a.intel?.severity || '').toLowerCase();
        const contentTitle = (a.content?.title || '').toLowerCase();
        const headline = (a.content?.headline || '').toLowerCase();
        return (
          title.includes(q) ||
          classification.includes(q) ||
          severity.includes(q) ||
          contentTitle.includes(q) ||
          headline.includes(q)
        );
      });
    }

    log.info('Asset search', { q, kind, results: results.length });
    return res.json({ assets: results, total: results.length });
  }

  async function create(req, res) {
    const type = req.query?.type || req.body?.type || 'hyperframe';
    const intel = req.body?.intel;
    if (!intel?.id || !intel?.title) {
      log.warn('Asset creation rejected — missing intel id or title');
      return res.status(400).json({ error: 'intel with id and title is required' });
    }

    log.info('Asset creation started', { type, intelId: intel.id, title: intel.title });

    const content =
      type === 'video' ? await generateVideoScript(intel) : await generateHyperframeContent(intel);

    const assetId = randomUUID();
    let localFile = null;

    // For images: persist the JSON spec immediately.
    // For videos: the actual .webm is uploaded by the browser after rendering;
    //             nothing written to disk here — localFile stays null until then.
    if (type !== 'video') {
      try {
        localFile = await saveImageJson(assetId, content);
      } catch (err) {
        log.warn('Failed to save image JSON to disk', { error: err?.message });
      }
    }

    const asset = {
      id: assetId,
      kind: type === 'video' ? 'video' : 'hyperframe',
      intel: {
        id: intel.id,
        title: intel.title,
        classification: intel.classification,
        severity: intel.severity
      },
      content,
      localFile,
      createdAt: new Date().toISOString()
    };
    db.data.assets.push(asset);
    await persist(db);
    const markUsed = await markLiveIntelUsed(intel.id, osintApiUrl);
    log.info('Asset created and persisted', { assetId: asset.id, kind: asset.kind, localFile });
    return res.json({ asset });
  }

  async function uploadVideo(req, res) {
    const { id } = req.params;
    const asset = db.data.assets.find((a) => a.id === id);
    if (!asset) return res.status(404).json({ error: 'asset not found' });

    const buf = req.body;
    if (!Buffer.isBuffer(buf) || buf.length === 0) {
      return res.status(400).json({ error: 'binary video body required (Content-Type: application/octet-stream)' });
    }

    log.info('Saving .webm for asset', { assetId: id, bytes: buf.length });
    try {
      const filePath = await saveVideoFile(id, buf);
      asset.localFile = filePath;
      await persist(db);
      log.info('Video .webm persisted', { assetId: id, filePath });
      return res.json({ success: true, filePath });
    } catch (err) {
      log.error('Failed to save video file', { assetId: id, error: err?.message });
      return res.status(500).json({ error: 'failed to save video' });
    }
  }

  async function uploadImage(req, res) {
    const { id } = req.params;
    const { dataUrl } = req.body;

    if (!dataUrl || !dataUrl.startsWith('data:image/')) {
      return res.status(400).json({ error: 'dataUrl (base64 image) is required' });
    }

    const asset = db.data.assets.find((a) => a.id === id);
    if (!asset) return res.status(404).json({ error: 'asset not found' });

    log.info('Saving PNG for asset', { assetId: id });
    try {
      const filePath = await saveImagePng(id, dataUrl);
      asset.localPng = filePath;
      await persist(db);
      log.info('PNG saved', { assetId: id, filePath });
      return res.json({ success: true, filePath });
    } catch (err) {
      log.error('Failed to save PNG', { assetId: id, error: err?.message });
      return res.status(500).json({ error: 'failed to save image' });
    }
  }

  async function save(req, res) {
    const asset = {
      id: randomUUID(),
      createdAt: new Date().toISOString(),
      ...req.body
    };
    db.data.assets.push(asset);
    await persist(db);
    const markUsed = await markLiveIntelUsed(asset.intel?.id || asset.intelId, osintApiUrl);
    return res.status(201).json({ asset, markUsed });
  }

  return { list, search, create, uploadVideo, uploadImage, save };
}
