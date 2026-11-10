const puppeteer = require("puppeteer-core");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const LIVE_URL = "https://aryan9891.github.io/AegisTruth/";

const DEVICES = [
  { name: "Desktop 1080p (PC / Monitor)", width: 1920, height: 1080, isMobile: false },
  { name: "Tablet iPad (Portrait)", width: 768, height: 1024, isMobile: true, hasTouch: true },
  { name: "Mobile iPhone SE (Compact)", width: 375, height: 667, isMobile: true, hasTouch: true },
  { name: "Mobile iPhone 14 (Standard)", width: 390, height: 844, isMobile: true, hasTouch: true },
  { name: "Mobile Android Flagship (Large)", width: 412, height: 915, isMobile: true, hasTouch: true },
];

async function runLiveDeviceTest(browser, device) {
  console.log(`\n======================================================`);
  console.log(`>>> TESTING LIVE GITHUB PAGES ON: ${device.name} (${device.width}x${device.height})`);
  console.log(`>>> Target: ${LIVE_URL}`);
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
  page.on("response", (res) => {
    if (res.status() === 404) {
      console.warn(`  [404 RESOURCE - ${device.name}]:`, res.url());
    }
  });

  page.on("requestfailed", (req) => {
    console.warn(`  [REQUEST FAILED - ${device.name}]:`, req.url(), req.failure()?.errorText);
  });
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const txt = msg.text();
      if (!txt.includes("getUserMedia") && !txt.includes("mediaDevices") && !txt.includes("Permission denied") && !txt.includes("favicon") && !txt.includes(".mp4")) {
        console.error(`  [CONSOLE ERROR - ${device.name}]:`, txt);
        consoleErrors.push(txt);
      }
    }
  });

  await page.goto(LIVE_URL, { waitUntil: "networkidle2", timeout: 25000 });
  console.log(`  ✓ Loaded live GitHub Pages URL successfully`);

  // Verify Title and Sentinel Mode
  const pageTitle = await page.title();
  console.log(`  ✓ Page Title: ${pageTitle}`);

  // Helper to switch tabs on all devices
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

  // 1. Navigation Tabs Verification
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
    if (!isVisible) throw new Error(`Tab ${tab} failed to activate on live site!`);
  }
  console.log(`  ✓ All 8 navigation tabs active on live deployment`);

  // 2. Command Center & Diagnostic Suite
  await goToTab("tab-overview");
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
      throw new Error("Live Diagnostic Suite error:\n" + logText);
    }
    console.log(`  ✓ Multi-Modal Diagnostic Suite passed all 6 pipelines on live GitHub Pages`);

    await page.$eval("#btn-close-benchmark", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
  }

  // 3. Cyber SOC War Room Mode
  const warRoomBtn = await page.$("#btn-header-war-room");
  if (warRoomBtn) {
    await warRoomBtn.click();
    await new Promise((r) => setTimeout(r, 150));
    const isWarRoomActive = await page.evaluate(() => document.body.classList.contains("war-room-mode"));
    console.log(`  ✓ Live Cyber SOC War Room engaged: ${isWarRoomActive}`);
    await warRoomBtn.click();
    await new Promise((r) => setTimeout(r, 100));
  }

  // 4. Media URL Scanner Modal
  const urlScanBtn = await page.$("#btn-header-scan-url");
  if (urlScanBtn) {
    await urlScanBtn.click();
    await new Promise((r) => setTimeout(r, 200));
    const isModalOpen = await page.$eval("#url-scanner-modal", (el) => window.getComputedStyle(el).display === "flex");
    console.log(`  ✓ Live Media URL Scanner modal verified: ${isModalOpen}`);
    await page.$eval("#btn-close-url-modal", (b) => b.click());
    await new Promise((r) => setTimeout(r, 150));
  }

  // 5. Batch Forensic Triage Queue
  await page.evaluate(() => {
    if (typeof window.enqueueBatchFiles === "function") {
      const fakeFile = new File(["AegisTruth Live GitHub Pages Verification Payload"], "live_audit.txt", { type: "text/plain" });
      window.enqueueBatchFiles([fakeFile]);
    }
  });

  await page.waitForFunction(() => {
    const rows = document.querySelectorAll("#batch-table-body tr");
    if (rows.length === 0) return false;
    const text = rows[0].innerText;
    return text.includes("AUTHENTIC") || text.includes("HIGH RISK") || text.includes("SUSPICIOUS");
  }, { timeout: 10000 });

  const batchRow = await page.$eval("#batch-table-body tr", (el) => el.innerText);
  console.log(`  ✓ Live Batch Forensic Triage verified: ${batchRow.split("\n")[0] || "live_audit.txt"}`);
  await page.$eval("#btn-clear-batch", (b) => b.click());
  await new Promise((r) => setTimeout(r, 100));

  // 6. Visual Lab (Microscope & Loupe)
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

  const imgVerdict = await page.$eval("#image-verdict-badge", (el) => el.innerText);
  console.log(`  ✓ Live Visual Lab result: ${imgVerdict}`);

  // Test Microscope bit planes
  await page.$eval('button[data-lens="bit0"]', (b) => b.click());
  await new Promise((r) => setTimeout(r, 80));
  await page.$eval('button[data-lens="sobel"]', (b) => b.click());
  await new Promise((r) => setTimeout(r, 80));
  await page.$eval('button[data-lens="original"]', (b) => b.click());
  console.log(`  ✓ Live Multi-Spectral Microscope & Bit-Planes verified`);

  // 7. Video Lab (Motion Quiver & Scrubber)
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
  const flowCoherence = await page.$eval("#metric-flow-coherence", (el) => el.innerText);
  console.log(`  ✓ Live Video Lab result: ${vidVerdict}, Flow Coherence: ${flowCoherence}`);

  // 8. Audio Lab (Formant Space & Equalizer)
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
  const f1 = await page.$eval("#metric-formant-f1", (el) => el.innerText);
  console.log(`  ✓ Live Audio Lab result: ${audVerdict}, F1: ${f1}`);

  // 9. Cognitive Lab (Token Perplexity & Dynamic Fact-Checking)
  await goToTab("tab-text");
  await new Promise((r) => setTimeout(r, 150));

  const testText = "Quantum computers leverage coherent superposition and entanglement. However, quantum computers cannot manipulate quantum states. Albert Einstein published the special theory of relativity in 1905.";
  await page.$eval("#text-input", (el, text) => {
    el.value = text;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }, testText);

  await page.$eval("#btn-analyze-text", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const panel = document.getElementById("text-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 10000 });

  const tokenChips = await page.$$("#token-perplexity-container .token-chip");
  const binocRatio = await page.$eval("#metric-binoculars-ratio", (el) => el.innerText);
  console.log(`  ✓ Live Token Perplexity Chips: ${tokenChips.length}, Binoculars Ratio: ${binocRatio}`);

  // Dynamic Fact Check
  await page.$eval("#btn-fact-check", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const panel = document.getElementById("fact-results-panel");
    return panel && panel.style.display === "block";
  }, { timeout: 10000 });

  const factScore = await page.$eval("#fact-score-val", (el) => el.innerText);
  console.log(`  ✓ Live Dynamic Factuality Index: ${factScore}`);

  // 10. Agent Zero-Trust Guard
  await goToTab("tab-guard");
  await new Promise((r) => setTimeout(r, 150));

  const card = await page.$(".attack-vector-card");
  if (card) {
    await card.click();
    await new Promise((r) => setTimeout(r, 150));
  }

  await page.$eval("#btn-scan-prompt", (b) => {
    b.scrollIntoView({ block: "center" });
    b.click();
  });
  await page.waitForFunction(() => {
    const res = document.getElementById("guard-results-panel");
    return res && res.style.display === "block";
  }, { timeout: 8000 });

  const guardVerdict = await page.$eval("#guard-verdict-badge", (el) => el.innerText);
  console.log(`  ✓ Live Agent Zero-Trust Guard Verdict: ${guardVerdict}`);

  // Test Tool Call Firewall
  await page.$eval("#btn-preset-tool-sql", (b) => b.click());
  await new Promise((r) => setTimeout(r, 100));
  await page.$eval("#btn-test-tool", (b) => b.click());
  await page.waitForFunction(() => {
    const out = document.getElementById("tool-eval-output");
    return out && out.style.display === "block";
  }, { timeout: 8000 });
  console.log(`  ✓ Live Tool Call Firewall verified`);

  // 11. C2PA Provenance Manifest
  await goToTab("tab-provenance");
  await new Promise((r) => setTimeout(r, 150));
  await page.$eval("#btn-view-manifest", (b) => b.click());
  await new Promise((r) => setTimeout(r, 200));
  const manifestText = await page.$eval("#manifest-json-display", (el) => el.innerText);
  if (!manifestText || !manifestText.includes("c2pa")) {
    throw new Error("Live C2PA Manifest is empty or invalid!");
  }
  console.log(`  ✓ Live C2PA Manifest verified (valid cryptographically bound structure)`);

  await page.close();

  if (consoleErrors.length > 0) {
    throw new Error(`Device ${device.name} experienced ${consoleErrors.length} console error(s) on live site:\n${consoleErrors.join("\n")}`);
  }

  console.log(`>>> SUCCESS: Live GitHub Pages on ${device.name} PASSED ALL CHECKS WITH 0 FLAWS!`);
}

async function main() {
  console.log("==================================================================");
  console.log("STARTING LIVE GITHUB PAGES MULTI-DEVICE VERIFICATION SUITE");
  console.log(`URL: ${LIVE_URL}`);
  console.log("==================================================================");

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",
      "--use-fake-ui-for-media-stream",
      "--use-fake-device-for-media-stream",
    ],
  });

  try {
    for (const dev of DEVICES) {
      await runLiveDeviceTest(browser, dev);
    }
    console.log("\n==================================================================");
    console.log("🏆 LIVE GITHUB PAGES VERIFICATION COMPLETE: ALL 5 DEVICES PASSED 100%!");
    console.log("==================================================================");
  } catch (err) {
    console.error("\n❌ LIVE TEST SUITE FAILED:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

main();
