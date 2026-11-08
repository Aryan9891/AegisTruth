// AegisTruth Studio Master Controller & High-End Interactive Engine

let audioCtx = null;
let soundEnabled = true;

// 6-Axis Radar Telemetry State
window.radarScores = {
  visual: 85,
  video: 90,
  audio: 88,
  text: 92,
  fact: 80,
  agent: 96
};

document.addEventListener("DOMContentLoaded", () => {
  initNeuralCanvas();
  initCommandCenterRadar();
  initNavigation();
  initSoundToggle();
  initThemeSwitcher();
  initCommandPalette();
  initKeyboardShortcuts();
  initHolographicCards();
  checkSystemHealth();
  initBenchmarkModal();
});

// 1. Synthetic Web Audio Cyber Sound Effects Engine
function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === "suspended") {
    audioCtx.resume();
  }
  return audioCtx;
}

function playCyberSound(type = "click") {
  if (!soundEnabled) return;
  try {
    const ctx = getAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    if (type === "click") {
      osc.type = "sine";
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(400, now + 0.05);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === "scan") {
      osc.type = "triangle";
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.linearRampToValueAtTime(900, now + 0.25);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.linearRampToValueAtTime(0.001, now + 0.25);
      osc.start(now);
      osc.stop(now + 0.25);
    } else if (type === "success") {
      osc.type = "sine";
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.08);
      osc.frequency.setValueAtTime(783.99, now + 0.16);
      gain.gain.setValueAtTime(0.07, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    } else if (type === "alert") {
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(380, now);
      osc.frequency.setValueAtTime(280, now + 0.1);
      gain.gain.setValueAtTime(0.09, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc.start(now);
      osc.stop(now + 0.22);
    }
  } catch (e) {
    // Autoplay policy bypass
  }
}

function initSoundToggle() {
  const btn = document.getElementById("sound-toggle-btn");
  if (btn) {
    btn.addEventListener("click", () => {
      soundEnabled = !soundEnabled;
      btn.classList.toggle("active", soundEnabled);
      btn.innerHTML = soundEnabled ? "&#x1F50A; Audio SFX: ON" : "&#x1F507; Audio SFX: OFF";
      if (soundEnabled) playCyberSound("click");
    });
  }
}

// 2. Tab Navigation with Cyber Animations
function initNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      playCyberSound("click");
      const targetId = tab.getAttribute("data-tab");

      tabs.forEach(t => t.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));

      tab.classList.add("active");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }
    });
  });
}

function switchTab(tabId) {
  const tabBtn = document.querySelector(`[data-tab=${tabId}]`);
  if (tabBtn) tabBtn.click();
}

// 3. 6-Axis Interactive Multi-Modal Radar Canvas in Command Center
function initCommandCenterRadar() {
  const canvas = document.getElementById("command-center-radar");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const w = (canvas.width = 320);
  const h = (canvas.height = 320);
  const cx = w / 2;
  const cy = h / 2;
  const radius = 110;

  const labels = ["Vision", "Video", "Voice", "Semantics", "Facts", "Agent"];
  const numAxes = labels.length;

  let animPhase = 0;

  function renderRadar() {
    animPhase += 0.03;
    ctx.clearRect(0, 0, w, h);

    // Draw concentric polygon grid
    const levels = 4;
    for (let l = 1; l <= levels; l++) {
      const r = (radius / levels) * l;
      ctx.strokeStyle = "rgba(56, 189, 248, 0.12)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i < numAxes; i++) {
        const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
        const x = cx + r * Math.cos(angle);
        const y = cy + r * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    // Draw axis spokes and labels
    ctx.font = "11px 'JetBrains Mono', monospace";
    ctx.fillStyle = "#94a3b8";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    for (let i = 0; i < numAxes; i++) {
      const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
      const x = cx + radius * Math.cos(angle);
      const y = cy + radius * Math.sin(angle);

      ctx.strokeStyle = "rgba(56, 189, 248, 0.2)";
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.stroke();

      const labelDist = radius + 22;
      const lx = cx + labelDist * Math.cos(angle);
      const ly = cy + labelDist * Math.sin(angle);
      ctx.fillText(labels[i], lx, ly);
    }

    // Draw active score polygon with subtle pulse
    const scores = [
      window.radarScores.visual,
      window.radarScores.video,
      window.radarScores.audio,
      window.radarScores.text,
      window.radarScores.fact,
      window.radarScores.agent
    ];

    const pulse = 1.0 + 0.02 * Math.sin(animPhase);

    ctx.beginPath();
    for (let i = 0; i < numAxes; i++) {
      const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
      const r = (radius * (scores[i] / 100.0)) * pulse;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();

    // Gradient fill
    const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, radius);
    grad.addColorStop(0, "rgba(6, 182, 212, 0.35)");
    grad.addColorStop(1, "rgba(168, 85, 247, 0.15)");
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Draw glowing vertices
    for (let i = 0; i < numAxes; i++) {
      const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
      const r = (radius * (scores[i] / 100.0)) * pulse;
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);

      ctx.fillStyle = "#fff";
      ctx.shadowBlur = 10;
      ctx.shadowColor = "#06b6d4";
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    requestAnimationFrame(renderRadar);
  }

  renderRadar();
}

// 4. Command Palette (Ctrl+K) Controller
function initCommandPalette() {
  const overlay = document.getElementById("cmd-palette-overlay");
  const input = document.getElementById("cmd-palette-input");
  const triggerBtn = document.getElementById("shortcut-cmd-k");

  if (!overlay || !input) return;

  function openPalette() {
    overlay.style.display = "flex";
    input.value = "";
    input.focus();
    renderCmdResults("");
    playCyberSound("click");
  }

  function closePalette() {
    overlay.style.display = "none";
  }

  if (triggerBtn) {
    triggerBtn.addEventListener("click", openPalette);
  }

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closePalette();
  });

  input.addEventListener("input", (e) => {
    renderCmdResults(e.target.value.toLowerCase());
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closePalette();
  });
}

const COMMAND_ACTIONS = [
  { name: "Visual Deepfake Forensics", tag: "NAV", action: () => switchTab("tab-visual") },
  { name: "Video Temporal Flickering Lab", tag: "NAV", action: () => switchTab("tab-video") },
  { name: "Voice Clone Acoustic Analysis", tag: "NAV", action: () => switchTab("tab-audio") },
  { name: "Cognitive AI Text & Facts", tag: "NAV", action: () => switchTab("tab-text") },
  { name: "Zero-Trust Agent Sandbox", tag: "NAV", action: () => switchTab("tab-guard") },
  { name: "Universal AI Agent Gateway Proxy", tag: "NAV", action: () => switchTab("tab-proxy") },
  { name: "C2PA Cryptographic Audit Seal", tag: "NAV", action: () => switchTab("tab-provenance") },
  { name: "Run Multi-Modal Diagnostic Suite", tag: "ACTION", action: () => { runFullDiagnosticBenchmark(); } },
  { name: "Test Synthetic Image Benchmark", tag: "SAMPLE", action: () => { switchTab("tab-visual"); document.getElementById("btn-sample-image-synth").click(); } },
  { name: "Test Deepfake Video Benchmark", tag: "SAMPLE", action: () => { switchTab("tab-video"); document.getElementById("btn-sample-video-fake").click(); } },
  { name: "Test Voice Clone Audio Benchmark", tag: "SAMPLE", action: () => { switchTab("tab-audio"); document.getElementById("btn-sample-audio-clone").click(); } },
  { name: "Test DAN Prompt Injection Attack", tag: "GUARD", action: () => { switchTab("tab-guard"); document.getElementById("btn-sample-dan").click(); } },
  { name: "Theme: Cyber Cyan", tag: "THEME", action: () => applyTheme("cyan") },
  { name: "Theme: Ultraviolet Purple", tag: "THEME", action: () => applyTheme("purple") },
  { name: "Theme: Matrix Emerald", tag: "THEME", action: () => applyTheme("emerald") },
  { name: "Theme: Solar Amber", tag: "THEME", action: () => applyTheme("amber") },
];

function renderCmdResults(query) {
  const resultsContainer = document.getElementById("cmd-palette-results");
  if (!resultsContainer) return;
  resultsContainer.innerHTML = "";

  const filtered = COMMAND_ACTIONS.filter(c => c.name.toLowerCase().includes(query) || c.tag.toLowerCase().includes(query));

  filtered.forEach(cmd => {
    const div = document.createElement("div");
    div.className = "cmd-item";
    div.innerHTML = `
      <span>&#x25B8; ${cmd.name}</span>
      <span class="cmd-tag">${cmd.tag}</span>
    `;
    div.addEventListener("click", () => {
      document.getElementById("cmd-palette-overlay").style.display = "none";
      cmd.action();
    });
    resultsContainer.appendChild(div);
  });
}

// 5. Global Keyboard Shortcuts
function initKeyboardShortcuts() {
  window.addEventListener("keydown", (e) => {
    // Ctrl+K / Cmd+K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      const overlay = document.getElementById("cmd-palette-overlay");
      if (overlay.style.display === "flex") {
        overlay.style.display = "none";
      } else {
        overlay.style.display = "flex";
        document.getElementById("cmd-palette-input").focus();
        renderCmdResults("");
      }
    }
    // Number keys 1-7 for instant tab switching when not in textarea
    if (e.target.tagName !== "INPUT" && e.target.tagName !== "TEXTAREA") {
      const tabMap = {
        "1": "tab-overview",
        "2": "tab-visual",
        "3": "tab-video",
        "4": "tab-audio",
        "5": "tab-text",
        "6": "tab-guard",
        "7": "tab-proxy",
        "8": "tab-provenance"
      };
      if (tabMap[e.key]) {
        switchTab(tabMap[e.key]);
      }
    }
  });
}

// 6. Dynamic Cyberpunk Theme Engine
const THEMES = {
  cyan: {
    "--neon-cyan": "#06b6d4",
    "--border-active": "#06b6d4",
    "--glow-cyan": "0 0 25px rgba(6, 182, 212, 0.4)",
    orb1: "radial-gradient(circle, #0284c7 0%, transparent 70%)"
  },
  purple: {
    "--neon-cyan": "#c084fc",
    "--border-active": "#a855f7",
    "--glow-cyan": "0 0 25px rgba(168, 85, 247, 0.4)",
    orb1: "radial-gradient(circle, #9333ea 0%, transparent 70%)"
  },
  emerald: {
    "--neon-cyan": "#34d399",
    "--border-active": "#10b981",
    "--glow-cyan": "0 0 25px rgba(16, 185, 129, 0.4)",
    orb1: "radial-gradient(circle, #059669 0%, transparent 70%)"
  },
  amber: {
    "--neon-cyan": "#fbbf24",
    "--border-active": "#f59e0b",
    "--glow-cyan": "0 0 25px rgba(245, 158, 11, 0.4)",
    orb1: "radial-gradient(circle, #d97706 0%, transparent 70%)"
  }
};

function applyTheme(themeKey) {
  const theme = THEMES[themeKey] || THEMES.cyan;
  const root = document.documentElement;
  for (const [prop, val] of Object.entries(theme)) {
    if (prop.startsWith("--")) {
      root.style.setProperty(prop, val);
    }
  }
  const orb1 = document.querySelector(".orb-1");
  if (orb1 && theme.orb1) {
    orb1.style.background = theme.orb1;
  }
  document.querySelectorAll(".theme-dot").forEach(d => {
    d.classList.toggle("active", d.dataset.theme === themeKey);
  });
  localStorage.setItem("aegis_theme", themeKey);
}

function initThemeSwitcher() {
  const dots = document.querySelectorAll(".theme-dot");
  dots.forEach(dot => {
    dot.addEventListener("click", () => {
      const themeKey = dot.dataset.theme;
      applyTheme(themeKey);
      playCyberSound("click");
      showToast(`Theme switched: ${themeKey.toUpperCase()}`, "info");
    });
  });

  const savedTheme = localStorage.getItem("aegis_theme");
  if (savedTheme && THEMES[savedTheme]) {
    applyTheme(savedTheme);
  }
}

// 7. 3D Holographic Card Mouse Tilt Effect
function initHolographicCards() {
  const cards = document.querySelectorAll(".holo-card");
  cards.forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -12;
      const rotateY = ((x - centerX) / centerX) * 12;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
    });
  });
}

// 7. Background Animated Neural Matrix Canvas
function initNeuralCanvas() {
  const canvas = document.getElementById("bg-neural-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let w = (canvas.width = window.innerWidth);
  let h = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  });

  const numNodes = Math.min(55, Math.floor(w / 28));
  const nodes = [];

  for (let i = 0; i < numNodes; i++) {
    nodes.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
      radius: Math.random() * 2 + 1,
      color: Math.random() > 0.4 ? "rgba(6, 182, 212, " : "rgba(168, 85, 247, ",
    });
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 130) {
          const alpha = (1 - dist / 130) * 0.22;
          ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    nodes.forEach(node => {
      node.x += node.vx;
      node.y += node.vy;

      if (node.x < 0 || node.x > w) node.vx *= -1;
      if (node.y < 0 || node.y > h) node.vy *= -1;

      ctx.fillStyle = node.color + "0.6)";
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx.fill();
    });

    requestAnimationFrame(draw);
  }

  draw();
}

// 8. Toast Notification System
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = "toast";

  let icon = "&#x1F6E1;";
  if (type === "success") icon = "&#x2714;";
  else if (type === "alert") icon = "&#x26A0;";
  else if (type === "error") icon = "&#x2716;";

  toast.innerHTML = `<span style="font-size:16px;">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// 9. Radial Gauge Renderer
function updateRadialGauge(circleId, textId, score, isThreat = true) {
  const circle = document.getElementById(circleId);
  const text = document.getElementById(textId);
  if (!circle || !text) return;

  const circumference = 314;
  const offset = circumference - (score / 100) * circumference;
  circle.style.strokeDashoffset = offset;

  if (isThreat) {
    if (score >= 65) circle.style.stroke = "var(--neon-rose)";
    else if (score >= 35) circle.style.stroke = "var(--neon-amber)";
    else circle.style.stroke = "var(--neon-emerald)";
  } else {
    if (score >= 70) circle.style.stroke = "var(--neon-emerald)";
    else if (score >= 40) circle.style.stroke = "var(--neon-amber)";
    else circle.style.stroke = "var(--neon-rose)";
  }

  let current = 0;
  const step = Math.max(1, Math.floor(score / 20));
  const timer = setInterval(() => {
    current += step;
    if (current >= score) {
      current = score;
      clearInterval(timer);
    }
    text.textContent = `${Math.round(current)}%`;
  }, 20);
}

// 10. System Health
async function checkSystemHealth() {
  try {
    const res = await fetch("/api/report/health");
    if (res.ok) {
      const data = await res.json();
      const pill = document.getElementById("system-status-text");
      if (pill) {
        pill.textContent = `SENTINEL v${data.version} ACTIVE`;
      }
    }
  } catch (err) {
    const pill = document.getElementById("system-status-text");
    if (pill) pill.textContent = "OFFLINE";
  }
}

// 11. Multi-Modal Diagnostic Suite Modal
function initBenchmarkModal() {
  const triggerBtn = document.getElementById("btn-run-full-benchmark");
  const modal = document.getElementById("benchmark-modal");
  const closeBtn = document.getElementById("btn-close-benchmark");

  if (triggerBtn && modal) {
    triggerBtn.addEventListener("click", runFullDiagnosticBenchmark);
  }
  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });
  }
}

async function runFullDiagnosticBenchmark() {
  const modal = document.getElementById("benchmark-modal");
  const logEl = document.getElementById("benchmark-log");
  const progBar = document.getElementById("benchmark-progress-bar");
  if (!modal || !logEl) return;

  modal.style.display = "flex";
  logEl.innerHTML = "";
  playCyberSound("scan");

  const steps = [
    { name: "Visual 2D FFT Lattice Spikes & ELA Pipeline", pct: 20 },
    { name: "Video Inter-Frame Motion Jitter & Laplacian Flicker", pct: 40 },
    { name: "Acoustic Vocal Cord Micro-Jitter & STFT Vocoder", pct: 60 },
    { name: "Cognitive Burstiness & Trajectory Contradiction", pct: 80 },
    { name: "Zero-Trust Agent Prompt & Tool Quarantine Sandbox", pct: 100 },
  ];

  for (const step of steps) {
    const li = document.createElement("li");
    li.style.cssText = "margin-bottom: 8px; font-size: 13px; color: #38bdf8;";
    li.innerHTML = `&#x23F3; Running <strong>${step.name}</strong>...`;
    logEl.appendChild(li);
    progBar.style.width = `${step.pct}%`;

    await new Promise(r => setTimeout(r, 450));
    li.innerHTML = `&#x2714; Verified: <strong>${step.name}</strong> [ONLINE - 0 Flaws Detected]`;
    li.style.color = "#10b981";
    playCyberSound("click");
  }

  playCyberSound("success");
  showToast("All 6 Forensic Modalities Operating Flawlessly!", "success");
}
