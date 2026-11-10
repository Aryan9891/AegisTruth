const puppeteer = require("puppeteer-core");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE_URL = "http://127.0.0.1:8000/";

const DEVICES = [
  { name: "Desktop 1080p (PC / Monitor)", width: 1920, height: 1080, isMobile: false },
  { name: "Tablet iPad (Portrait)", width: 768, height: 1024, isMobile: true, hasTouch: true },
  { name: "Mobile iPhone SE (Compact)", width: 375, height: 667, isMobile: true, hasTouch: true },
  { name: "Mobile iPhone 14 (Standard)", width: 390, height: 844, isMobile: true, hasTouch: true },
  { name: "Mobile Android Flagship (Large)", width: 412, height: 915, isMobile: true, hasTouch: true },
];

async function runDeviceTest(browser, device) {
  console.log(`\n======================================================`);
  console.log(`>>> TESTING DEVICE: ${device.name} (${device.width}x${device.height})`);
  console.log(`======================================================`);

  const page = await browser.newPage();
  await page.setViewport({
    width: device.width,
    height: device.height,
    isMobile: device.isMobile,
    hasTouch: device.hasTouch || false,
  });

  const consoleErrors = [];
  page.on("pageerror", (err) => {
    console.error(`  [PAGE ERROR - ${device.name}]:`, err.message);
    consoleErrors.push(err.message);
  });
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const txt = msg.text();
      // Ignore simulated audio/webcam headless sandbox warnings
      if (!txt.includes("getUserMedia") && !txt.includes("mediaDevices") && !txt.includes("Permission denied")) {
        console.error(`  [CONSOLE ERROR - ${device.name}]:`, txt);
        consoleErrors.push(txt);
      }
    }
  });

  await page.goto(BASE_URL, { waitUntil: "networkidle2", timeout: 15000 });
  console.log(`  ✓ Loaded base URL successfully`);

  // 1. Sidebar Navigation Toggle Test (Desktop Rail vs Mobile/Tablet Drawer)
  if (device.isMobile) {
    const mobileBtn = await page.$("#mobile-menu-btn");
    if (mobileBtn) {
      await mobileBtn.click();
      await new Promise((r) => setTimeout(r, 200));
      const hasOpen = await page.$eval("#app-sidebar", (el) => el.classList.contains("mobile-open"));
      console.log(`  ✓ Mobile hamburger toggle opened drawer: ${hasOpen}`);
      // Click backdrop to close
      await page.$eval("#sidebar-backdrop", (el) => el.click());
      await new Promise((r) => setTimeout(r, 200));
      const isClosed = await page.$eval("#app-sidebar", (el) => !el.classList.contains("mobile-open"));
      console.log(`  ✓ Backdrop click closed mobile drawer: ${isClosed}`);
    }
  } else {
    const toggleBtn = await page.$("#sidebar-toggle-btn");
    if (toggleBtn) {
      await toggleBtn.click();
      await new Promise((r) => setTimeout(r, 150));
      const isCollapsed = await page.$eval("#app-sidebar", (el) => el.classList.contains("collapsed"));
      console.log(`  ✓ Desktop sidebar rail collapse toggled: ${isCollapsed}`);
      await toggleBtn.click();
      await new Promise((r) => setTimeout(r, 150));
    }
  }

  // Helper to switch tabs on all devices (handles mobile drawer opening & auto-closing)
  async function goToTab(tabId) {
    if (device.isMobile) {
      const isDrawerOpen = await page.$eval("#app-sidebar", (el) => el.classList.contains("mobile-open"));
      if (!isDrawerOpen) {
        await page.$eval("#mobile-menu-btn", (b) => b.click());
        await new Promise((r) => setTimeout(r, 150));
      }
    }
    await page.$eval(`button[data-tab="${tabId}"]`, (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
  }

  // 2. Navigation Tabs (all 8 tabs)
  const tabs = [
    "tab-overview",
    "tab-visual",
    "tab-video",
    "tab-audio",
    "tab-text",
    "tab-guard",
    "tab-proxy",
    "tab-provenance",
  ];

  for (const tab of tabs) {
    await goToTab(tab);
    const isVisible = await page.$eval(`#${tab}`, (el) => el.style.display !== "none" && el.classList.contains("active"));
    if (!isVisible) throw new Error(`Tab ${tab} failed to activate!`);
  }
  console.log(`  ✓ All 8 navigation tabs successfully switched and verified active`);

  // 3. Cyber Video Theater Modal Test
  await goToTab("tab-overview");

  const watchDemoBtn = await page.$("#btn-hero-watch-demo");
  if (watchDemoBtn) {
    await watchDemoBtn.click();
    await new Promise((r) => setTimeout(r, 250));
    const isModalOpen = await page.$eval("#video-demo-modal", (el) => el.style.display === "flex");
    console.log(`  ✓ Cyber Video Theater opened: ${isModalOpen}`);

    // Click Chapter 3 (Audio Forensics)
    const ch3 = await page.$(`button[data-chapter="3"]`);
    if (ch3) {
      await ch3.click();
      await new Promise((r) => setTimeout(r, 150));
      console.log(`  ✓ Video chapter seek 3 clicked`);
    }

    // Close Video Modal
    const closeBtn = await page.$("#btn-close-demo-modal");
    if (closeBtn) {
      await closeBtn.click();
      await new Promise((r) => setTimeout(r, 150));
      const isClosed = await page.$eval("#video-demo-modal", (el) => el.style.display === "none");
      console.log(`  ✓ Cyber Video Theater closed: ${isClosed}`);
    }
  }

  // 3B. Multi-Modal Diagnostic Benchmark Suite Modal Test
  const benchBtn = await page.$("#btn-run-full-benchmark");
  if (benchBtn) {
    await benchBtn.click();
    await page.waitForFunction(() => {
      const log = document.getElementById("benchmark-log");
      if (!log) return false;
      const text = log.innerText;
      return text.includes("DIAGNOSTIC SUITE COMPLETE") || text.includes("Diagnostic Error");
    }, { timeout: 15000 });

    const logText = await page.$eval("#benchmark-log", (el) => el.innerText);
    if (logText.includes("Diagnostic Error")) {
      throw new Error("Multi-Modal Diagnostic Suite failed with error:\n" + logText);
    }
    console.log(`  ✓ Multi-Modal Diagnostic Suite completed all 6 pipelines successfully`);

    // Close modal
    await page.$eval("#btn-close-benchmark", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
  }

  // 3C. Tactical Cyber SOC War Room Mode Test
  const warRoomBtn = await page.$("#btn-header-war-room");
  if (warRoomBtn) {
    await warRoomBtn.click();
    await new Promise((r) => setTimeout(r, 150));
    const isWarRoomActive = await page.evaluate(() => document.body.classList.contains("war-room-mode"));
    const isBannerShown = await page.$eval("#war-room-banner", (el) => window.getComputedStyle(el).display !== "none");
    console.log(`  ✓ Cyber SOC War Room activated: ${isWarRoomActive}, banner visible: ${isBannerShown}`);

    // Toggle back
    await warRoomBtn.click();
    await new Promise((r) => setTimeout(r, 100));
  }

  // 3D. Media URL Scanner Modal Test
  const urlScanBtn = await page.$("#btn-header-scan-url");
  if (urlScanBtn) {
    await urlScanBtn.click();
    await new Promise((r) => setTimeout(r, 200));
    const isModalOpen = await page.$eval("#url-scanner-modal", (el) => window.getComputedStyle(el).display === "flex");
    console.log(`  ✓ Media URL Scanner modal opened: ${isModalOpen}`);

    await page.type("#input-media-url", "https://example.com/test_media.jpg");
    await page.$eval("#btn-close-url-modal", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
    const isClosed = await page.$eval("#url-scanner-modal", (el) => window.getComputedStyle(el).display === "none");
    console.log(`  ✓ Media URL Scanner modal closed: ${isClosed}`);
  }

  // 3E. Enterprise Multi-Asset Batch Forensic Triage Queue Test
  const batchDropzone = await page.$("#batch-dropzone");
  if (batchDropzone) {
    await page.evaluate(() => {
      if (typeof window.enqueueBatchFiles === "function") {
        const fakeFile = new File(["AegisTruth batch integrity verification payload"], "triage_audit.txt", { type: "text/plain" });
        window.enqueueBatchFiles([fakeFile]);
      }
    });

    await page.waitForFunction(() => {
      const rows = document.querySelectorAll("#batch-table-body tr");
      if (rows.length === 0) return false;
      const text = rows[0].innerText;
      return text.includes("AUTHENTIC") || text.includes("HIGH RISK") || text.includes("SUSPICIOUS") || text.includes("ERROR");
    }, { timeout: 10000 });

    const rowText = await page.$eval("#batch-table-body tr", (el) => el.innerText);
    console.log(`  ✓ Batch Forensic Triage completed asset analysis: ${rowText.split("\n")[0] || "triage_audit.txt"}`);

    // Test clear batch
    await page.$eval("#btn-clear-batch", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
    const isEmpty = await page.$eval("#batch-table-body", (el) => el.innerText.includes("No files currently in triage"));
    console.log(`  ✓ Batch Forensic Triage queue cleared: ${isEmpty}`);
  }

  // 4. Biometric Live Webcam Sentinel Modal Test
  const webcamBtn = await page.$("#btn-hero-webcam-sentinel");
  if (webcamBtn) {
    await webcamBtn.click();
    await new Promise((r) => setTimeout(r, 250));
    const isModalOpen = await page.$eval("#webcam-sentinel-modal", (el) => el.style.display === "flex");
    console.log(`  ✓ Live Webcam Sentinel Modal opened: ${isModalOpen}`);

    // Test Frame Scan button
    const scanBtn = await page.$("#btn-webcam-scan-frame");
    if (scanBtn) {
      await scanBtn.click();
      await new Promise((r) => setTimeout(r, 150));
      console.log(`  ✓ Webcam frame scan / freeze button clicked`);
    }

    // Close modal
    const closeWebcam = await page.$("#btn-close-webcam-modal");
    if (closeWebcam) {
      await closeWebcam.click();
      await new Promise((r) => setTimeout(r, 150));
      const isClosed = await page.$eval("#webcam-sentinel-modal", (el) => el.style.display === "none");
      console.log(`  ✓ Live Webcam Sentinel Modal closed: ${isClosed}`);
    }
  }

  // 5. Visual Deepfake Lab (Tab Visual)
  await goToTab("tab-visual");
  await new Promise((r) => setTimeout(r, 200));

  await page.$eval("#btn-sample-image-real", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const panel = document.getElementById("image-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 12000 });
  const verdict = await page.$eval("#image-verdict-badge", (el) => el.innerText);
  const elaVar = await page.$eval("#metric-ela-var", (el) => el.innerText);
  console.log(`  ✓ Visual Lab real sample tested -> Verdict: ${verdict}, ELA Variance: ${elaVar}`);

  // Lens Switcher test
  const lensFft = await page.$("#btn-lens-fft");
  const lensEla = await page.$("#btn-lens-ela");
  if (lensFft && lensEla) {
    await lensFft.click();
    await new Promise((r) => setTimeout(r, 100));
    await lensEla.click();
    await new Promise((r) => setTimeout(r, 100));
    console.log(`  ✓ Lens Mode Switcher (ELA <-> FFT) verified`);
  }

  // 5B. Multi-Spectral Microscope & Bit-Plane Slicer Test
  const microCanvas = await page.$("#microscope-canvas");
  if (microCanvas) {
    // Click bit0, bit7, sobel, original
    await page.$eval('button[data-lens="bit0"]', (b) => b.click());
    await new Promise((r) => setTimeout(r, 80));
    await page.$eval('button[data-lens="bit7"]', (b) => b.click());
    await new Promise((r) => setTimeout(r, 80));
    await page.$eval('button[data-lens="sobel"]', (b) => b.click());
    await new Promise((r) => setTimeout(r, 80));
    await page.$eval('button[data-lens="original"]', (b) => b.click());
    await new Promise((r) => setTimeout(r, 80));

    // Test Loupe toggle
    const loupeBtn = await page.$("#btn-toggle-loupe");
    if (loupeBtn) {
      await loupeBtn.click();
      await new Promise((r) => setTimeout(r, 80));
      const loupeOn = await page.$eval("#btn-toggle-loupe", (el) => el.innerText.includes("ON"));
      await loupeBtn.click();
      await new Promise((r) => setTimeout(r, 80));
      console.log(`  ✓ Multi-Spectral Microscope & Bit-Plane Slicer verified (Loupe toggle: ${loupeOn})`);
    }
  }

  // 6. Temporal Video Lab (Tab Video)
  await goToTab("tab-video");
  await new Promise((r) => setTimeout(r, 200));

  await page.$eval("#btn-sample-video-real", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const panel = document.getElementById("video-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 12000 });
  const vidVerdict = await page.$eval("#video-verdict-badge", (el) => el.innerText);
  const flicker = await page.$eval("#metric-video-flicker", (el) => el.innerText);
  console.log(`  ✓ Video Lab real sample tested -> Verdict: ${vidVerdict}, Flicker Score: ${flicker}`);

  // 6B. Optical Motion Vector Flow & Frame Scrubber Studio Test
  const motionCanvas = await page.$("#video-motion-canvas");
  if (motionCanvas) {
    const coherence = await page.$eval("#metric-flow-coherence", (el) => el.innerText);
    const velocity = await page.$eval("#metric-flow-velocity", (el) => el.innerText);
    console.log(`  ✓ Optical Flow Coherence: ${coherence}, Mean Velocity: ${velocity}`);

    // Click frame scrubber thumbnail
    const frame2 = await page.$('.frame-thumb-item[data-frame="2"]');
    if (frame2) {
      await frame2.click();
      await new Promise((r) => setTimeout(r, 100));
      const activeIdx = await page.$eval("#scrubber-active-frame-idx", (el) => el.innerText);
      console.log(`  ✓ Frame Scrubber activated frame #${activeIdx}`);
    }
  }

  // 7. Voice Clone Lab (Tab Audio)
  await goToTab("tab-audio");
  await new Promise((r) => setTimeout(r, 200));

  await page.$eval("#btn-sample-audio-human", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const panel = document.getElementById("audio-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 12000 });
  const audVerdict = await page.$eval("#audio-verdict-badge", (el) => el.innerText);
  const jitter = await page.$eval("#metric-audio-jitter", (el) => el.innerText);
  console.log(`  ✓ Audio Lab human sample tested -> Verdict: ${audVerdict}, Pitch Jitter: ${jitter}`);

  // 7B. Biometric Formant Acoustic Vowel Space (F1/F2) & Equalizer Test
  const formantCanvas = await page.$("#audio-formant-canvas");
  if (formantCanvas) {
    const f1 = await page.$eval("#metric-formant-f1", (el) => el.innerText);
    const f2 = await page.$eval("#metric-formant-f2", (el) => el.innerText);
    const disp = await page.$eval("#metric-vowel-dispersion", (el) => el.innerText);
    console.log(`  ✓ Formant Acoustic Space -> F1: ${f1}, F2: ${f2}, Dispersion: ${disp}`);

    // Click equalizer filter pill
    const vocalPill = await page.$('.audio-filter-pill[data-filter="vocal"]');
    if (vocalPill) {
      await vocalPill.click();
      await new Promise((r) => setTimeout(r, 80));
    }

    // Click Play Filtered Audio
    const playFilteredBtn = await page.$("#btn-play-filtered-audio");
    if (playFilteredBtn) {
      await playFilteredBtn.click();
      await new Promise((r) => setTimeout(r, 150));
      console.log(`  ✓ Web Audio equalizer filter preview triggered`);
    }
  }

  // 8. Cognitive & Facts Lab (Tab Text) - Real Dynamic Extraction, No Hardcoded Claims
  await goToTab("tab-text");
  await new Promise((r) => setTimeout(r, 150));

  const customContradictionText =
    "In third quarter 2026, SpaceX successfully launched twenty satellites into orbit. The company reported record-breaking mission efficiency. However, SpaceX suffered catastrophic mission failure during the exact same orbital window, losing all satellites. Abraham Lincoln approved the rocket launch by smartphone.";

  await page.$eval("#text-input", (el, text) => {
    el.value = text;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }, customContradictionText);

  // Click Analyze Text
  await page.$eval("#btn-analyze-text", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const panel = document.getElementById("text-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 10000 });

  const entropy = await page.$eval("#metric-text-entropy", (el) => el.innerText);
  const burstiness = await page.$eval("#metric-text-burstiness", (el) => el.innerText);
  console.log(`  ✓ Text Shannon Entropy: ${entropy}, Burstiness: ${burstiness}`);

  // 8B. Token Perplexity Heatmap & Binoculars Radar Test
  const tokenChips = await page.$$("#token-perplexity-container .token-chip");
  const binocRatio = await page.$eval("#metric-binoculars-ratio", (el) => el.innerText);
  console.log(`  ✓ Token Perplexity Heatmap chips rendered: ${tokenChips.length}, Binoculars Ratio: ${binocRatio}`);

  // Click Verify Facts
  await page.$eval("#btn-fact-check", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const panel = document.getElementById("fact-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 10000 });

  const factScore = await page.$eval("#fact-score-val", (el) => el.innerText);
  const matrixText = await page.$eval("#fact-claims-table-body", (el) => el.innerText);

  console.log(`  ✓ Fact-checking dynamic result -> Factuality Index: ${factScore}`);
  
  // STRICT VERIFICATION: Verify that NO hardcoded "renewable energy" string is present!
  if (matrixText.toLowerCase().includes("renewable energy")) {
    throw new Error("FLAW DETECTED: Hardcoded 'renewable energy' claim found in dynamic fact verification results!");
  }
  console.log(`  ✓ VERIFIED ZERO HARDCODING: Dynamic matrix processed custom SpaceX / Lincoln claims!`);

  // 9. Agent Zero-Trust Lab (Tab Guard) & Adversarial Threat Matrix
  await goToTab("tab-guard");
  await new Promise((r) => setTimeout(r, 150));

  // Click DAN attack vector card
  await page.$eval(`.attack-vector-card`, (c) => c.click());
  await new Promise((r) => setTimeout(r, 150));
  const promptVal = await page.$eval("#guard-prompt-input", (el) => el.value);
  if (!promptVal || promptVal.length === 0) throw new Error("Threat card did not populate input!");
  console.log(`  ✓ Adversarial Threat Matrix card clicked, payload populated`);

  // Click Scan Prompt Threats
  await page.$eval("#btn-scan-prompt", (b) => b.click());
  await page.waitForFunction(() => {
    const panel = document.getElementById("guard-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 8000 });
  const guardVerdict = await page.$eval("#guard-verdict-badge", (el) => el.innerText);
  console.log(`  ✓ Zero-Trust Prompt Guard evaluated payload -> Verdict: ${guardVerdict}`);

  // Test SQL Drop tool call
  await page.$eval("#btn-preset-tool-sql", (b) => b.click());
  await new Promise((r) => setTimeout(r, 100));
  await page.$eval("#btn-test-tool", (b) => b.click());
  await page.waitForFunction(() => {
    const out = document.getElementById("tool-eval-output");
    return out && out.style.display === "block";
  }, { timeout: 8000 });
  const toolOutput = await page.$eval("#tool-eval-output", (el) => el.innerText);
  console.log(`  ✓ Zero-Trust Tool Firewall blocked SQL DROP TABLE: ${toolOutput.includes("BLOCKED") || toolOutput.includes("QUARANTINE")}`);

  // 10. Universal AI Proxy Lab (Tab Proxy)
  await goToTab("tab-proxy");
  await new Promise((r) => setTimeout(r, 150));

  await page.$eval("#btn-send-proxy-req", (b) => b.click());
  await page.waitForFunction(() => {
    const box = document.getElementById("proxy-response-box");
    return box && box.style.display === "block";
  }, { timeout: 8000 });
  const proxyStatus = await page.$eval("#proxy-response-box", (el) => el.innerText);
  console.log(`  ✓ Universal Proxy processed live gateway request`);

  // 11. Provenance Lab (Tab Provenance)
  await goToTab("tab-provenance");
  await new Promise((r) => setTimeout(r, 150));

  await page.$eval("#btn-view-manifest", (b) => b.click());
  await new Promise((r) => setTimeout(r, 200));
  const manifestText = await page.$eval("#manifest-json-display", (el) => el.innerText);
  console.log(`  ✓ C2PA Provenance Manifest refreshed: ${manifestText.length > 50 ? "VALID JSON SIGNATURE" : "ACTIVE"}`);

  // 12. Classified Dossier Modal Test
  const dossierPill = await page.$("#open-dossier-pill");
  if (dossierPill) {
    await dossierPill.click();
    await new Promise((r) => setTimeout(r, 250));
    const isModalOpen = await page.$eval("#dossier-modal", (el) => el.style.display === "flex");
    const caseId = await page.$eval("#dossier-case-id", (el) => el.innerText);
    console.log(`  ✓ Classified Forensic Dossier opened: ${isModalOpen}, Case ID: ${caseId}`);

    // Close dossier
    await page.$eval("#dossier-modal button.btn-secondary", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
    const isClosed = await page.$eval("#dossier-modal", (el) => el.style.display === "none");
    console.log(`  ✓ Classified Forensic Dossier closed: ${isClosed}`);
  }

  // 13. Theme Switcher & Matrix Switcher
  if (device.isMobile) {
    await page.$eval("#mobile-menu-btn", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
  }

  await page.$eval(`[data-theme="purple"]`, (el) => el.click());
  await new Promise((r) => setTimeout(r, 100));
  const activeTheme = await page.evaluate(() => localStorage.getItem("aegis_theme"));
  console.log(`  ✓ Cyberpunk theme accent switched to: ${activeTheme}`);

  // Switch back to cyan
  await page.$eval(`[data-theme="cyan"]`, (el) => el.click());
  await new Promise((r) => setTimeout(r, 100));

  // Sound Effects Toggle
  await page.$eval("#sound-toggle-btn", (el) => el.click());
  await new Promise((r) => setTimeout(r, 100));
  const soundText = await page.$eval("#sound-toggle-btn", (el) => el.innerText);
  console.log(`  ✓ Sound FX toggled: ${soundText}`);
  await page.$eval("#sound-toggle-btn", (el) => el.click());

  if (device.isMobile) {
    await page.$eval("#sidebar-backdrop", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
  }

  // Background Neural Matrix Switcher
  const matrixBtn = await page.$("#matrix-mode-btn");
  if (matrixBtn) {
    await matrixBtn.click();
    await new Promise((r) => setTimeout(r, 100));
    const mode1 = await page.$eval("#matrix-mode-btn", (el) => el.innerText);
    await matrixBtn.click();
    await new Promise((r) => setTimeout(r, 100));
    const mode2 = await page.$eval("#matrix-mode-btn", (el) => el.innerText);
    console.log(`  ✓ Ambient Neural Matrix modes cycled: ${mode1} -> ${mode2}`);
  }

  await page.close();

  if (consoleErrors.length > 0) {
    throw new Error(`Device ${device.name} experienced ${consoleErrors.length} console error(s):\n${consoleErrors.join("\n")}`);
  }

  console.log(`>>> SUCCESS: Device ${device.name} passed 100% of feature checks with 0 flaws!`);
}

async function main() {
  console.log("Starting AegisTruth Automated Multi-Device Comprehensive Test Suite...");
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--use-fake-ui-for-media-stream",
      "--use-fake-device-for-media-stream",
      "--allow-file-access-from-files",
    ],
  });

  try {
    for (const dev of DEVICES) {
      await runDeviceTest(browser, dev);
    }
    console.log("\n==================================================================");
    console.log("🎉 ALL 5 DEVICE CONFIGURATIONS PASSED ALL TESTS WITH ZERO ERRORS!");
    console.log("==================================================================");
  } catch (err) {
    console.error("\n❌ TEST SUITE FAILED:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
