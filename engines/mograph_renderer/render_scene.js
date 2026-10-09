const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const puppeteer = require('puppeteer-core');

function findChromePath() {
  const commonPaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe'
  ];
  for (const p of commonPaths) {
    if (fs.existsSync(p)) return p;
  }
  throw new Error('Neither Chrome nor Edge was found on the host system.');
}

async function renderScene({
  htmlPath,
  outputPath,
  duration = 5.0,
  fps = 30,
  width = 1080,
  height = 1920
}) {
  const startTime = Date.now();
  console.log(`[Mograph Renderer] Starting render: ${path.basename(htmlPath)} -> ${path.basename(outputPath)}`);
  console.log(`[Mograph Renderer] Resolution: ${width}x${height} | FPS: ${fps} | Duration: ${duration}s`);

  const chromePath = findChromePath();
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--hide-scrollbars',
      '--mute-audio',
      '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding'
    ]
  });

  try {
    const page = await browser.newPage();
    page.on('console', msg => console.log('[CHROME CONSOLE]:', msg.text()));
    page.on('pageerror', err => console.error('[CHROME ERROR]:', err.message));
    await page.setViewport({ width, height, deviceScaleFactor: 1 });

    const fileUrl = 'file:///' + path.resolve(htmlPath).replace(/\\/g, '/');
    await page.goto(fileUrl, { waitUntil: 'load', timeout: 30000 });

    // Wait until animation engine signals readiness
    await page.waitForFunction(() => window.__ready === true, { timeout: 10000 }).catch(() => {
      console.log('[Mograph Renderer] window.__ready not flagged, proceeding with fallback...');
    });

    // Ensure output directory exists
    const outDir = path.dirname(path.resolve(outputPath));
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }

    // Spawn FFmpeg to stream JPEG frames into h264 MP4 (3-4x faster than PNG)
    const ffmpegArgs = [
      '-y',
      '-f', 'image2pipe',
      '-vcodec', 'mjpeg',
      '-framerate', String(fps),
      '-i', '-',
      '-c:v', 'libx264',
      '-preset', 'veryfast',
      '-crf', '20',
      '-pix_fmt', 'yuv420p',
      outputPath
    ];

    const ffmpeg = spawn('ffmpeg', ffmpegArgs, { stdio: ['pipe', 'ignore', 'pipe'] });
    let ffmpegErr = '';
    ffmpeg.stderr.on('data', (d) => {
      ffmpegErr += d.toString();
    });

    const totalFrames = Math.max(1, Math.round(duration * fps));
    console.log(`[Mograph Renderer] Rendering ${totalFrames} frames...`);

    for (let f = 0; f < totalFrames; f++) {
      const timeSec = f / fps;
      await page.evaluate((t) => {
        if (typeof window.seekTimeline === 'function') {
          window.seekTimeline(t);
        }
      }, timeSec);

      const buffer = await page.screenshot({ type: 'jpeg', quality: 95 });

      
      const canWrite = ffmpeg.stdin.write(buffer);
      if (!canWrite) {
        await new Promise((resolve) => ffmpeg.stdin.once('drain', resolve));
      }
    }

    ffmpeg.stdin.end();

    await new Promise((resolve, reject) => {
      ffmpeg.on('close', (code) => {
        if (code === 0) resolve();
        else reject(new Error(`FFmpeg exited with code ${code}: ${ffmpegErr.slice(-500)}`));
      });
      ffmpeg.on('error', reject);
    });

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    console.log(`[Mograph Renderer] Successfully rendered: ${outputPath} in ${elapsed}s`);
    return { success: true, outputPath, elapsed: parseFloat(elapsed), frames: totalFrames };
  } finally {
    await browser.close();
  }
}

// CLI usage: node render_scene.js --html <path> --output <path> --duration <sec> [--fps 30] [--width 1080] [--height 1920]
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].replace(/^--/, '');
    const val = args[i + 1];
    if (key === 'html') options.htmlPath = val;
    else if (key === 'output') options.outputPath = val;
    else if (key === 'duration') options.duration = parseFloat(val);
    else if (key === 'fps') options.fps = parseInt(val, 10);
    else if (key === 'width') options.width = parseInt(val, 10);
    else if (key === 'height') options.height = parseInt(val, 10);
  }

  if (!options.htmlPath || !options.outputPath) {
    console.error('Usage: node render_scene.js --html <path> --output <path> --duration <sec>');
    process.exit(1);
  }

  renderScene(options)
    .then((res) => {
      console.log(JSON.stringify(res));
      process.exit(0);
    })
    .catch((err) => {
      console.error('[Mograph Renderer Error]:', err);
      process.exit(1);
    });
}

module.exports = { renderScene };
