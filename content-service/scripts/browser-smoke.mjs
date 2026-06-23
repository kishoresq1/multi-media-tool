import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync } from 'node:fs';
import { readFile, rm, stat } from 'node:fs/promises';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const marketingDir = resolve(here, '..');
const frontendDir = join(marketingDir, 'frontend-app');
const distDir = join(frontendDir, 'dist');
const apiUrl = process.env.MARKETING_SMOKE_API_URL || 'http://127.0.0.1:3002';
const uiPort = Number(process.env.MARKETING_SMOKE_UI_PORT || 5174);
const uiUrl = `http://127.0.0.1:${uiPort}`;
const stamp = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
const marketingDbPath = join(tmpdir(), `sq1-marketing-browser-smoke-${stamp}.json`);
const processes = [];
let staticServer;
let cleanupPromise;

async function main() {
  await runBuild();

  const apiOwner = await ensureApi();
  if (apiOwner) processes.push(apiOwner);

  staticServer = await startStaticServer();

  const health = await waitForJson(`${apiUrl}/api/health`, 'Marketing API health');
  assert(health.status === 'ok', `Expected API health status ok, received ${health.status}`);
  assert(health.service === 'sq1-marketing', `Expected sq1-marketing service, received ${health.service}`);

  const intel = await waitForJson(`${uiUrl}/mkt/intel/unmarketed`, 'Marketing UI proxy intel');
  assert(Array.isArray(intel.items), 'Expected proxied intel response to include items');
  assert(intel.items.length > 0, 'Expected at least one marketing intel item');

  const playwright = await loadPlaywright();
  if (playwright) {
    try {
      await runPlaywrightSmoke(playwright);
    } catch (error) {
      if (!isPlaywrightRuntimeUnavailable(error)) throw error;
      console.log(`playwright browser unavailable; falling back to HTTP/HTML smoke checks: ${error.message}`);
      await runHttpSmoke();
    }
  } else {
    await runHttpSmoke();
  }

  console.log(`browser smoke ok: ${playwright ? 'playwright' : 'http/html'} checks passed at ${uiUrl}`);
}

async function runBuild() {
  await runCommand('frontend-build', process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'build'], {
    cwd: frontendDir,
    env: process.env
  });
}

async function ensureApi() {
  try {
    const health = await fetchJson(`${apiUrl}/api/health`, 1500);
    if (health.status === 'ok' && health.service === 'sq1-marketing') {
      console.log(`using existing Marketing API at ${apiUrl}`);
      return null;
    }
  } catch {
    // Start a local API below.
  }

  const api = startProcess('marketing-api', process.execPath, [join(marketingDir, 'src', 'api', 'server.js')], {
    cwd: marketingDir,
    env: {
      ...process.env,
      PORT: '3002',
      MARKETING_USE_LIVE_OSINT: 'false',
      MARKETING_API_TOKEN: '',
      MARKETING_DB_PATH: marketingDbPath
    }
  });
  await waitForJson(`${apiUrl}/api/health`, 'Marketing API health');
  return api;
}

async function startStaticServer() {
  const indexHtml = await readFile(join(distDir, 'index.html'), 'utf8');
  assert(indexHtml.includes('<div id="root"></div>'), 'Expected built index.html to include the React root');

  const server = createServer(async (req, res) => {
    try {
      const requestUrl = new URL(req.url || '/', uiUrl);
      if (requestUrl.pathname.startsWith('/mkt')) {
        await proxyApiRequest(req, res, requestUrl);
        return;
      }
      await serveDistAsset(res, requestUrl.pathname);
    } catch (error) {
      res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' });
      res.end(error.stack || error.message);
    }
  });

  const listenResult = await new Promise((resolveListen, rejectListen) => {
    server.once('error', rejectListen);
    server.listen(uiPort, '127.0.0.1', () => {
      server.off('error', rejectListen);
      resolveListen('started');
    });
  }).catch(async (error) => {
    if (error.code !== 'EADDRINUSE') throw error;
    const existingHtml = await fetchText(uiUrl);
    assert(existingHtml.includes('<div id="root"></div>'), `Expected existing UI at ${uiUrl} to serve app HTML`);
    console.log(`using existing Marketing UI at ${uiUrl}`);
    return 'existing';
  });

  if (listenResult === 'existing') return null;

  console.log(`serving built Marketing UI at ${uiUrl}`);
  return server;
}

async function proxyApiRequest(req, res, requestUrl) {
  const targetPath = requestUrl.pathname.replace(/^\/mkt/, '/api') + requestUrl.search;
  const headers = { ...req.headers };
  delete headers.host;
  const hasBody = !['GET', 'HEAD'].includes(req.method || 'GET');

  const response = await fetch(`${apiUrl}${targetPath}`, {
    method: req.method,
    headers,
    body: hasBody ? req : undefined,
    duplex: hasBody ? 'half' : undefined,
    signal: AbortSignal.timeout(5000)
  });

  res.writeHead(response.status, Object.fromEntries(response.headers.entries()));
  if (req.method === 'HEAD') {
    res.end();
    return;
  }
  const body = Buffer.from(await response.arrayBuffer());
  res.end(body);
}

async function serveDistAsset(res, pathname) {
  const filePath = resolveStaticPath(pathname);
  const exists = await isFile(filePath);
  const finalPath = exists ? filePath : join(distDir, 'index.html');
  const body = await readFile(finalPath);
  res.writeHead(200, {
    'content-type': contentType(finalPath),
    'cache-control': 'no-store'
  });
  res.end(body);
}

function resolveStaticPath(pathname) {
  const decoded = decodeURIComponent(pathname);
  const requested = decoded === '/' ? '/index.html' : decoded;
  const candidate = normalize(join(distDir, requested));
  const distPrefix = distDir.endsWith(sep) ? distDir : `${distDir}${sep}`;
  if (candidate !== distDir && !candidate.startsWith(distPrefix)) {
    return join(distDir, 'index.html');
  }
  return candidate;
}

async function runPlaywrightSmoke({ chromium }) {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const consoleErrors = [];
    page.on('console', (message) => {
      if (message.type() === 'error') consoleErrors.push(message.text());
    });
    page.on('pageerror', (error) => {
      consoleErrors.push(error.message);
    });

    await page.goto(uiUrl, { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Marketing Intelligence Console' }).waitFor();
    await page.getByRole('navigation', { name: 'Marketing sections' }).waitFor();
    await page.getByRole('button', { name: /Dashboard/ }).waitFor();
    await page.getByRole('button', { name: /Subscribers/ }).click();
    await page.waitForURL('**/subscribe');
    await page.getByRole('button', { name: /Dashboard/ }).click();
    await page.waitForURL(uiUrl);

    assert(consoleErrors.length === 0, `Expected no browser console errors, saw: ${consoleErrors.join(' | ')}`);
  } finally {
    await browser.close();
  }
}

async function runHttpSmoke() {
  const indexHtml = await fetchText(uiUrl);
  assert(indexHtml.includes('<div id="root"></div>'), 'Expected app root in built index HTML');

  const subscribeHtml = await fetchText(`${uiUrl}/subscribe`);
  assert(subscribeHtml.includes('<div id="root"></div>'), 'Expected SPA fallback root for /subscribe');

  const assetPaths = [...indexHtml.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g)].map((match) => match[1]);
  assert(assetPaths.length > 0, 'Expected built index to reference JS/CSS assets');

  const assetBodies = await Promise.all(assetPaths.map((assetPath) => fetchText(new URL(assetPath, uiUrl).toString())));
  const bundleText = assetBodies.join('\n');
  for (const expected of ['Marketing Intelligence Console', 'Dashboard', 'Subscribers', 'Mock intel feed']) {
    assert(bundleText.includes(expected), `Expected built bundle to include "${expected}"`);
  }
}

async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch {
    console.log('playwright not available; falling back to HTTP/HTML smoke checks');
    return null;
  }
}

function isPlaywrightRuntimeUnavailable(error) {
  return /Executable doesn't exist|browserType\.launch|Host system is missing dependencies/i.test(error.message || '');
}

async function runCommand(name, command, args, options) {
  const child = startProcess(name, command, args, options);
  child.expectedExit = true;
  processes.push(child);
  const { code, signal } = await child.closed;
  processes.splice(processes.indexOf(child), 1);
  assert(code === 0, `${name} exited with ${code === null ? `signal ${signal}` : `code ${code}`}`);
}

function startProcess(name, command, args, options) {
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
  return retry(label, () => fetchJson(url, 2000));
}

async function fetchJson(url, timeoutMs) {
  const response = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  return response.json();
}

async function fetchText(url) {
  const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  return response.text();
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

async function isFile(filePath) {
  try {
    return (await stat(filePath)).isFile();
  } catch {
    return false;
  }
}

function contentType(filePath) {
  switch (extname(filePath)) {
    case '.css':
      return 'text/css; charset=utf-8';
    case '.html':
      return 'text/html; charset=utf-8';
    case '.js':
      return 'text/javascript; charset=utf-8';
    case '.json':
      return 'application/json; charset=utf-8';
    case '.svg':
      return 'image/svg+xml';
    default:
      return 'application/octet-stream';
  }
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function cleanup() {
  cleanupPromise ??= (async () => {
    const closing = [...processes].reverse().map(stopProcess);
    await Promise.allSettled(closing);
    if (staticServer) {
      await new Promise((resolveClose) => staticServer.close(resolveClose));
    }
    if (existsSync(marketingDbPath)) {
      await rm(marketingDbPath, { force: true });
    }
  })();
  await cleanupPromise;
}

async function stopProcess(service) {
  service.expectedExit = true;
  if (service.child.exitCode !== null || service.child.signalCode !== null) {
    await service.closed;
    return;
  }

  signalProcess(service.child, 'SIGTERM');
  let closed = await waitForClose(service, 5000);
  if (!closed) {
    signalProcess(service.child, 'SIGKILL');
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

function signalProcess(child, signalName) {
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
