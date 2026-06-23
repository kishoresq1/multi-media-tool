import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { rm } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const marketingDir = resolve(here, '..');
const frontendDir = join(marketingDir, 'frontend-app');
const repoRoot = resolve(marketingDir, '..');
const python = join(repoRoot, '.venv', 'bin', 'python');
const viteBin = resolveViteBin();
const stamp = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
const osintDbPath = join(tmpdir(), `sq1-osint-smoke-${stamp}.json`);
const marketingDbPath = join(tmpdir(), `sq1-marketing-smoke-${stamp}.json`);
const processes = [];
let cleanupPromise;

async function main() {
  const osint = start('osint-api', python, ['-m', 'uvicorn', 'openosint.api.main:app', '--host', '127.0.0.1', '--port', '8000'], {
    cwd: repoRoot,
    env: { ...process.env, SQ1_DB_PATH: osintDbPath }
  });
  const api = start('marketing-api', process.execPath, [join(marketingDir, 'src', 'api', 'server.js')], {
    cwd: marketingDir,
    env: {
      ...process.env,
      PORT: '3002',
      MARKETING_USE_LIVE_OSINT: 'true',
      MARKETING_API_TOKEN: '',
      OSINT_API_URL: 'http://127.0.0.1:8000',
      MARKETING_DB_PATH: marketingDbPath
    }
  });
  const ui = start(
    'marketing-ui',
    process.execPath,
    [viteBin, '--host', '127.0.0.1', '--port', '5174', '--strictPort'],
    { cwd: frontendDir, env: process.env }
  );
  processes.push(osint, api, ui);

  await waitForJson('http://127.0.0.1:8000/health', 'OSINT health');
  const marketingHealth = await waitForJson('http://127.0.0.1:3002/api/health', 'Marketing health');
  assert(marketingHealth.mode === 'live', `Expected Marketing API live mode, received ${marketingHealth.mode}`);
  await waitForText('http://127.0.0.1:5174', 'Marketing UI');

  const before = await waitForJson('http://127.0.0.1:3002/api/intel/unmarketed', 'Marketing live intel');
  assert(before.source === 'live', `Expected live marketing source, received ${before.source}`);
  assert(Array.isArray(before.items) && before.items.length > 0, 'Expected live unmarketed intel items');

  const intel = before.items[0];
  const create = await postJson('http://127.0.0.1:3002/api/assets/create?type=hyperframe', {
    intel
  });
  assert(create.asset?.id, 'Expected created asset id');

  const after = await waitForJson('http://127.0.0.1:8000/api/intel/unmarketed', 'OSINT unmarketed after asset');
  assert(Array.isArray(after), 'Expected OSINT unmarketed response array');
  assert(!after.some((item) => item.id === intel.id), 'Expected created intel to be marked used');

  console.log(`integration smoke ok: asset ${create.asset.id} created from ${intel.id}`);
}

function start(name, command, args, options) {
  const child = spawn(command, args, {
    ...options,
    detached: process.platform !== 'win32',
    stdio: ['ignore', 'pipe', 'pipe']
  });
  const service = {
    name,
    child,
    expectedExit: false,
    closed: new Promise((resolveClose) => {
      child.on('close', (code, signal) => resolveClose({ code, signal }));
    })
  };
  child.stdout.on('data', (chunk) => process.stdout.write(`[${name}] ${chunk}`));
  child.stderr.on('data', (chunk) => process.stderr.write(`[${name}] ${chunk}`));
  child.on('error', (error) => {
    process.stderr.write(`[${name}] failed to start: ${error.message}\n`);
  });
  child.on('exit', (code, signal) => {
    if (!service.expectedExit) {
      const reason = code === null ? `signal ${signal}` : `code ${code}${signal ? ` (${signal})` : ''}`;
      process.stderr.write(`[${name}] exited with ${reason}\n`);
    }
  });
  return service;
}

async function waitForJson(url, label) {
  return retry(label, async () => {
    const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
    if (!response.ok) throw new Error(`${label} returned ${response.status}`);
    return response.json();
  });
}

async function waitForText(url, label) {
  return retry(label, async () => {
    const response = await fetch(url, { signal: AbortSignal.timeout(2000) });
    if (!response.ok) throw new Error(`${label} returned ${response.status}`);
    return response.text();
  });
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(5000)
  });
  if (!response.ok) {
    throw new Error(`POST ${url} returned ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function retry(label, fn) {
  const started = Date.now();
  let lastError;
  while (Date.now() - started < 30000) {
    const failed = processes.find((service) => service.child.exitCode !== null || service.child.signalCode !== null);
    if (failed) {
      throw new Error(`${label} cannot continue because ${failed.name} exited`);
    }
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      await new Promise((resolveDelay) => setTimeout(resolveDelay, 500));
    }
  }
  throw new Error(`${label} did not become ready: ${lastError?.message || 'unknown error'}`);
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function resolveViteBin() {
  let dir = dirname(require.resolve('vite', { paths: [frontendDir, marketingDir] }));
  while (dir !== dirname(dir)) {
    const candidate = join(dir, 'bin', 'vite.js');
    if (existsSync(candidate)) return candidate;
    dir = dirname(dir);
  }
  throw new Error('Unable to locate vite/bin/vite.js');
}

async function cleanup() {
  cleanupPromise ??= (async () => {
    const closing = [...processes].reverse().map(stop);
    await Promise.allSettled(closing);
    await Promise.allSettled([rm(osintDbPath, { force: true }), rm(marketingDbPath, { force: true })]);
  })();
  await cleanupPromise;
}

async function stop(service) {
  service.expectedExit = true;
  if (service.child.exitCode !== null || service.child.signalCode !== null) {
    await service.closed;
    return;
  }

  signal(service.child, 'SIGTERM');
  let closed = await waitForClose(service, 5000);
  if (!closed) {
    signal(service.child, 'SIGKILL');
    closed = await waitForClose(service, 2000);
  }
  if (!closed) {
    process.stderr.write(`[${service.name}] did not exit after SIGKILL\n`);
  }
}

async function waitForClose(service, timeoutMs) {
  let timeoutId;
  const timeout = new Promise((resolveTimeout) => {
    timeoutId = setTimeout(() => resolveTimeout(false), timeoutMs);
  });
  try {
    return await Promise.race([service.closed.then(() => true), timeout]);
  } finally {
    clearTimeout(timeoutId);
  }
}

function signal(child, signalName) {
  try {
    if (process.platform === 'win32') {
      child.kill(signalName);
    } else {
      process.kill(-child.pid, signalName);
    }
  } catch (error) {
    if (error.code !== 'ESRCH') throw error;
  }
}

for (const signalName of ['SIGINT', 'SIGTERM']) {
  process.once(signalName, async () => {
    await cleanup();
    process.exit(signalName === 'SIGINT' ? 130 : 143);
  });
}

try {
  await main();
} finally {
  await cleanup();
}
