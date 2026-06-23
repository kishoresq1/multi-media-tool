import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { makeLogger } from './logger.js';

const log = makeLogger('Storage');

// Resolves to marketing/.runtime/assets/ relative to CWD (marketing/)
const BASE_DIR = resolve('.runtime/assets');

async function ensureDir(dir) {
  await mkdir(dir, { recursive: true });
}

export async function saveImagePng(assetId, dataUrl) {
  const dir = join(BASE_DIR, 'images');
  await ensureDir(dir);
  const base64 = dataUrl.replace(/^data:image\/\w+;base64,/, '');
  const buf = Buffer.from(base64, 'base64');
  const filePath = join(dir, `${assetId}.png`);
  await writeFile(filePath, buf);
  log.info('Image PNG saved', { assetId, filePath });
  return filePath;
}

export async function saveImageJson(assetId, content) {
  const dir = join(BASE_DIR, 'images');
  await ensureDir(dir);
  const filePath = join(dir, `${assetId}.json`);
  await writeFile(filePath, JSON.stringify(content, null, 2));
  log.info('Hyperframe JSON saved', { assetId, filePath });
  return filePath;
}

export async function saveVideoJson(assetId, script) {
  const dir = join(BASE_DIR, 'videos');
  await ensureDir(dir);
  const filePath = join(dir, `${assetId}.json`);
  await writeFile(filePath, JSON.stringify(script, null, 2));
  log.info('Video script JSON saved', { assetId, filePath });
  return filePath;
}

export async function saveVideoFile(assetId, buffer) {
  const dir = join(BASE_DIR, 'videos');
  await ensureDir(dir);
  const filePath = join(dir, `${assetId}.webm`);
  await writeFile(filePath, buffer);
  log.info('Video .webm saved', { assetId, filePath, bytes: buffer.length });
  return filePath;
}

export function assetsBaseDir() {
  return BASE_DIR;
}
