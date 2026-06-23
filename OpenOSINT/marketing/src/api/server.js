import dotenv from 'dotenv';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createApp } from './app.js';
import { createFileDb } from './db.js';

// Load root .env first (AI keys), then marketing/.env for local overrides
const __dir = dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: resolve(__dir, '../../../.env') });     // repo root .env
dotenv.config({ path: resolve(__dir, '../../.env') });        // marketing/.env

const port = Number(process.env.PORT || 3002);
const db = await createFileDb(process.env.MARKETING_DB_PATH || './.runtime/db.json');
const app = createApp({ db });

app.listen(port, () => {
  console.log(`SQ1 Marketing API listening on http://localhost:${port}`);
});
