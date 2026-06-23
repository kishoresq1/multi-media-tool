// Canvas-based video capture that replicates CyberVideoComposition visually.
// Draws each frame manually → records with MediaRecorder → returns a .webm Blob.

const FPS = 30;

const BG_DRAWERS = {
  dark_grid(ctx, w, h) {
    ctx.fillStyle = '#0a0e1a';
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(0,212,255,0.05)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
    for (let y = 0; y < h; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
  },
  red_pulse(ctx, w, h) {
    const g = ctx.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
    g.addColorStop(0, 'rgba(255,51,102,0.45)');
    g.addColorStop(1, '#0a0e1a');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  },
  blue_wave(ctx, w, h) {
    const g = ctx.createLinearGradient(0, 0, w, h);
    g.addColorStop(0, '#071426');
    g.addColorStop(1, '#10253d');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  },
  amber_static(ctx, w, h) {
    const g = ctx.createLinearGradient(0, 0, w, h);
    g.addColorStop(0, '#101014');
    g.addColorStop(1, '#2b2108');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  },
  matrix_rain(ctx, w, h) {
    ctx.fillStyle = '#06100b';
    ctx.fillRect(0, 0, w, h);
  }
};

function splitLines(text, maxChars) {
  const words = String(text || '').split(' ');
  const lines = [];
  let cur = '';
  for (const word of words) {
    const next = cur ? `${cur} ${word}` : word;
    if (next.length > maxChars && cur) { lines.push(cur); cur = word; }
    else cur = next;
  }
  if (cur) lines.push(cur);
  return lines;
}

function drawFrame(ctx, scene, frameInScene, w, h) {
  ctx.clearRect(0, 0, w, h);

  // Background
  (BG_DRAWERS[scene.bgStyle] || BG_DRAWERS.dark_grid)(ctx, w, h);

  // Fade-in over first 10 frames
  ctx.globalAlpha = Math.min(1, frameInScene / 10);

  // Top label
  ctx.fillStyle = '#00d4ff';
  ctx.font = '26px Inter,system-ui,sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'alphabetic';
  ctx.fillText('SQ1 SECURITY INTELLIGENCE', w / 2, h / 2 - 130);

  // Headline
  ctx.fillStyle = '#f8fafc';
  ctx.font = 'bold 68px Inter,system-ui,sans-serif';
  const headLines = splitLines(scene.onScreenText, 22);
  headLines.forEach((line, i) => ctx.fillText(line, w / 2, h / 2 - 30 + i * 80));

  // Narration (max 2 lines)
  ctx.fillStyle = '#cbd5e1';
  ctx.font = '28px Inter,system-ui,sans-serif';
  splitLines(scene.narration, 62).slice(0, 2).forEach((line, i) =>
    ctx.fillText(line, w / 2, h / 2 + 150 + i * 40)
  );

  ctx.globalAlpha = 1;
}

export function recordVideoFromScenes(scenes, fps = FPS) {
  return new Promise((resolve, reject) => {
    if (!window.MediaRecorder || typeof HTMLCanvasElement.prototype.captureStream !== 'function') {
      return reject(new Error('MediaRecorder / captureStream not supported in this browser'));
    }

    const W = 1280, H = 720;
    const canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    canvas.style.cssText = 'position:fixed;left:-9999px;top:-9999px;pointer-events:none';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    const mimeType = ['video/webm;codecs=vp9', 'video/webm'].find(
      (m) => MediaRecorder.isTypeSupported(m)
    ) ?? 'video/webm';

    const stream = canvas.captureStream(fps);
    const recorder = new MediaRecorder(stream, { mimeType, videoBitsPerSecond: 2_500_000 });
    const chunks = [];

    recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
    recorder.onstop = () => {
      canvas.remove();
      resolve(new Blob(chunks, { type: mimeType }));
    };
    recorder.onerror = (e) => { canvas.remove(); reject(e.error ?? new Error('recorder error')); };

    // Expand scenes into a flat frame list
    const frames = scenes.flatMap((scene) =>
      Array.from({ length: Math.round(scene.durationSeconds * fps) }, (_, f) => ({ scene, frameInScene: f }))
    );

    recorder.start();
    let idx = 0;
    const interval = setInterval(() => {
      if (idx >= frames.length) {
        clearInterval(interval);
        recorder.stop();
        return;
      }
      const { scene, frameInScene } = frames[idx++];
      drawFrame(ctx, scene, frameInScene, W, H);
    }, Math.floor(1000 / fps));
  });
}
