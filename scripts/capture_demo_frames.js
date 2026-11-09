/**
 * Automated High-Definition Frame Capture for AegisTruth Product Demo Video
 * Connects to headless Chrome, operates each forensic lab, and captures 1080p frames.
 */

const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const TEMP_PROFILE = path.join(process.env.TEMP || 'C:\\Temp', 'chrome_demo_profile_' + Date.now());
const TARGET_URL = 'http://127.0.0.1:8000';
const FRAMES_DIR = path.join(__dirname, 'frames');

if (!fs.existsSync(FRAMES_DIR)) {
  fs.mkdirSync(FRAMES_DIR, { recursive: true });
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.msgId = 1;
    this.pending = new Map();
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl);
      this.ws.onopen = () => resolve();
      this.ws.onerror = (err) => reject(err);
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.id && this.pending.has(data.id)) {
            const { resolve, reject } = this.pending.get(data.id);
            this.pending.delete(data.id);
            if (data.error) reject(data.error);
            else resolve(data.result);
          }
        } catch (e) {
          console.error('Error parsing CDP message:', e);
        }
      };
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.msgId++;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send('Runtime.evaluate', {
      expression,
      awaitPromise: true,
      returnByValue: true
    });
    if (res.exceptionDetails) {
      const err = res.exceptionDetails.exception ? res.exceptionDetails.exception.description : res.exceptionDetails.text;
      throw new Error(err || 'Eval exception');
    }
    return res.result ? res.result.value : undefined;
  }

  async wait(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  async captureScreenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png', quality: 95 });
    const buffer = Buffer.from(res.data, 'base64');
    const filePath = path.join(FRAMES_DIR, filename);
    fs.writeFileSync(filePath, buffer);
    console.log(`  [✔ Captured] ${filename} (${buffer.length} bytes)`);
    return filePath;
  }
}

async function getWsUrl(port = 9222) {
  return new Promise((resolve, reject) => {
    let retries = 30;
    const interval = setInterval(() => {
      http.get(`http://127.0.0.1:${port}/json/list`, (res) => {
        let raw = '';
        res.on('data', chunk => raw += chunk);
        res.on('end', () => {
          try {
            const targets = JSON.parse(raw);
            const pageTarget = targets.find(t => t.type === 'page');
            if (pageTarget && pageTarget.webSocketDebuggerUrl) {
              clearInterval(interval);
              resolve(pageTarget.webSocketDebuggerUrl);
            }
          } catch (e) {}
        });
      }).on('error', () => {
        if (--retries <= 0) {
          clearInterval(interval);
          reject(new Error('Timeout connecting to Chrome debugging port'));
        }
      });
    }, 250);
  });
}

async function run() {
  console.log('[*] Spawning Headless Chrome for 1080p Video Frame Capture...');
  const chromeProc = spawn(CHROME_PATH, [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--user-data-dir=' + TEMP_PROFILE,
    '--window-size=1920,1080',
    '--hide-scrollbars',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    TARGET_URL
  ]);

  try {
    const wsUrl = await getWsUrl(9222);
    const client = new CDPClient(wsUrl);
    await client.connect();

    await client.send('Emulation.setDeviceMetricsOverride', {
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1,
      mobile: false
    });

    console.log('[*] Connected to Chrome. Loading AegisTruth Sentinel...');
    await client.send('Page.navigate', { url: TARGET_URL });
    await client.wait(2500);

    // --- Scene 1: Command Center & Radar ---
    console.log('\n[1/8] Capturing Scene 1: Command Center & Telemetry Radar...');
    await client.eval(`switchTab('tab-overview')`);
    await client.wait(1200);
    await client.captureScreenshot('scene_1.png');

    // --- Scene 2: Visual Deepfakes Forensics ---
    console.log('\n[2/8] Capturing Scene 2: Visual Deepfakes Forensics Studio...');
    await client.eval(`
      (async () => {
        switchTab('tab-visual');
        await new Promise(r => setTimeout(r, 400));
        const btn = document.getElementById('btn-sample-image-synth');
        if (btn) btn.click();
        await new Promise(r => setTimeout(r, 1200));
      })()
    `);
    await client.wait(1500);
    await client.captureScreenshot('scene_2.png');

    // --- Scene 3: Temporal Video Deepfake Sentinel ---
    console.log('\n[3/8] Capturing Scene 3: Temporal Video Deepfake Sentinel...');
    await client.eval(`
      (async () => {
        switchTab('tab-video');
        await new Promise(r => setTimeout(r, 400));
        const btn = document.getElementById('btn-sample-video-fake');
        if (btn) btn.click();
        await new Promise(r => setTimeout(r, 1200));
      })()
    `);
    await client.wait(1500);
    await client.captureScreenshot('scene_3.png');

    // --- Scene 4: Acoustic Voice Clone Lab ---
    console.log('\n[4/8] Capturing Scene 4: Acoustic Voice Clone Lab...');
    await client.eval(`
      (async () => {
        switchTab('tab-audio');
        await new Promise(r => setTimeout(r, 400));
        const btn = document.getElementById('btn-sample-audio-clone');
        if (btn) btn.click();
        await new Promise(r => setTimeout(r, 1200));
      })()
    `);
    await client.wait(1500);
    await client.captureScreenshot('scene_4.png');

    // --- Scene 5: Cognitive Text Forensics & Fact Sentinel ---
    console.log('\n[5/8] Capturing Scene 5: Cognitive Text Forensics & Fact Sentinel...');
    await client.eval(`
      (async () => {
        switchTab('tab-text');
        await new Promise(r => setTimeout(r, 400));
        const btnAi = document.getElementById('btn-sample-text-ai');
        if (btnAi) btnAi.click();
        await new Promise(r => setTimeout(r, 300));
        const btnAnalyze = document.getElementById('btn-analyze-text');
        if (btnAnalyze) btnAnalyze.click();
        await new Promise(r => setTimeout(r, 600));
        const btnFact = document.getElementById('btn-fact-check');
        if (btnFact) btnFact.click();
        await new Promise(r => setTimeout(r, 800));
      })()
    `);
    await client.wait(1500);
    await client.captureScreenshot('scene_5.png');

    // --- Scene 6: AI Agent Security Guard ---
    console.log('\n[6/8] Capturing Scene 6: AI Agent Security Guard & Tool Firewall...');
    await client.eval(`
      (async () => {
        switchTab('tab-guard');
        await new Promise(r => setTimeout(r, 400));
        const btnDan = document.getElementById('btn-sample-dan');
        if (btnDan) btnDan.click();
        await new Promise(r => setTimeout(r, 300));
        const btnScan = document.getElementById('btn-scan-prompt');
        if (btnScan) btnScan.click();
        await new Promise(r => setTimeout(r, 600));
        const btnRm = document.getElementById('btn-preset-tool-rm');
        if (btnRm) btnRm.click();
        await new Promise(r => setTimeout(r, 300));
        const btnTool = document.getElementById('btn-test-tool');
        if (btnTool) btnTool.click();
        await new Promise(r => setTimeout(r, 600));
      })()
    `);
    await client.wait(1500);
    await client.captureScreenshot('scene_6.png');

    // --- Scene 7: C2PA Cryptographic Provenance ---
    console.log('\n[7/8] Capturing Scene 7: C2PA Cryptographic Provenance Attestation...');
    await client.eval(`
      (async () => {
        switchTab('tab-provenance');
        await new Promise(r => setTimeout(r, 400));
        const btnManifest = document.getElementById('btn-view-manifest');
        if (btnManifest) btnManifest.click();
        await new Promise(r => setTimeout(r, 1000));
      })()
    `);
    await client.wait(1500);
    await client.captureScreenshot('scene_7.png');

    // --- Scene 8: Architecture & Diagnostic Suite ---
    console.log('\n[8/8] Capturing Scene 8: Offline Privacy & Architecture...');
    await client.eval(`
      (async () => {
        switchTab('tab-overview');
        await new Promise(r => setTimeout(r, 400));
        const btnBench = document.getElementById('btn-header-benchmark') || document.getElementById('btn-run-full-benchmark');
        if (btnBench) btnBench.click();
        await new Promise(r => setTimeout(r, 1200));
      })()
    `);
    await client.wait(1500);
    await client.captureScreenshot('scene_8.png');

    console.log('\n[✔ ALL 8 SCENE FRAMES CAPTURED SUCCESSFULLY]');
  } finally {
    try { chromeProc.kill(); } catch (e) {}
    try { fs.rmSync(TEMP_PROFILE, { recursive: true, force: true }); } catch (e) {}
  }
}

run().catch(err => {
  console.error('[FATAL CAPTURE ERROR]:', err);
  process.exit(1);
});
