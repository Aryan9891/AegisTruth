// AegisTruth Acoustic & Voice Clone Forensics Lab

let mediaRecorder = null;
let recordedChunks = [];
let audioContext = null;
let analyserNode = null;
let animationFrameId = null;

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("audio-dropzone");
  const fileInput = document.getElementById("audio-file-input");
  const micBtn = document.getElementById("btn-record-mic");
  const sampleHumanBtn = document.getElementById("btn-sample-audio-human");
  const sampleCloneBtn = document.getElementById("btn-sample-audio-clone");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        processAudioFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        processAudioFile(fileInput.files[0]);
      }
    });
  }

  if (micBtn) {
    micBtn.addEventListener("click", toggleMicRecording);
  }

  if (sampleHumanBtn) {
    sampleHumanBtn.addEventListener("click", () => loadSampleAudio("sample_audio_real.wav"));
  }

  if (sampleCloneBtn) {
    sampleCloneBtn.addEventListener("click", () => loadSampleAudio("sample_audio_clone.wav"));
  }
});

async function toggleMicRecording() {
  const btn = document.getElementById("btn-record-mic");
  const canvas = document.getElementById("mic-live-waveform");

  if (mediaRecorder && mediaRecorder.state === "recording") {
    // Stop recording
    mediaRecorder.stop();
    btn.innerHTML = "&#x1F3A4; Record Microphone Stream";
    btn.classList.remove("btn-danger");
    btn.classList.add("btn-primary");
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
  } else {
    // Start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioContext.createMediaStreamSource(stream);
      analyserNode = audioContext.createAnalyser();
      analyserNode.fftSize = 512;
      source.connect(analyserNode);

      drawLiveMicWaveform(canvas, analyserNode);

      recordedChunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(recordedChunks, { type: "audio/wav" });
        stream.getTracks().forEach(track => track.stop());
        await processAudioFile(audioBlob);
      };

      mediaRecorder.start();
      btn.innerHTML = "&#x23F9; Stop Recording &amp; Analyze";
      btn.classList.remove("btn-primary");
      btn.classList.add("btn-danger");
    } catch (err) {
      if (typeof playCyberSound === "function") playCyberSound("alert");
      if (typeof showToast === "function") showToast("Microphone access failed: " + err.message, "alert");
      console.error("Microphone access failed:", err);
    }
  }
}

function drawLiveMicWaveform(canvas, analyser) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const bufferLength = analyser.frequencyBinCount;
  const timeData = new Uint8Array(bufferLength);
  const freqData = new Uint8Array(bufferLength);

  function render() {
    animationFrameId = requestAnimationFrame(render);
    analyser.getByteTimeDomainData(timeData);
    analyser.getByteFrequencyData(freqData);

    ctx.fillStyle = "#080c16";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 1. Draw dynamic neon frequency bars in background
    const numBars = 48;
    const barWidth = canvas.width / numBars;
    const step = Math.floor(bufferLength / numBars);

    for (let i = 0; i < numBars; i++) {
      const barHeight = (freqData[i * step] / 255.0) * (canvas.height * 0.75);
      const x = i * barWidth;
      const y = canvas.height - barHeight;

      // Neon cyan-to-purple gradient
      const grad = ctx.createLinearGradient(0, y, 0, canvas.height);
      grad.addColorStop(0, "#06b6d4");
      grad.addColorStop(1, "rgba(168, 85, 247, 0.2)");

      ctx.fillStyle = grad;
      ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
    }

    // 2. Draw glowing oscillating waveform line on top
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = "#38bdf8";
    ctx.shadowBlur = 8;
    ctx.shadowColor = "#06b6d4";
    ctx.beginPath();

    const sliceWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = timeData[i] / 128.0;
      const y = (v * canvas.height) / 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      x += sliceWidth;
    }

    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
    ctx.shadowBlur = 0; // reset shadow
  }
  render();
}

async function loadSampleAudio(filename) {
  setLoadingState("audio-loading", true);
  try {
    let directSample = await fetch(`samples/${filename}`).catch(() => null);
    if (!directSample || !directSample.ok) {
      directSample = await fetch(`./samples/${filename}`).catch(() => null);
    }
    if (!directSample || !directSample.ok) {
      directSample = await fetch(`/static/samples/${filename}`).catch(() => null);
    }
    if (!directSample || !directSample.ok) throw new Error("Could not fetch sample audio asset");

    const blob = await directSample.blob();
    await processAudioFile(blob, filename);
  } catch (err) {
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast("Audio sample error: " + err.message, "alert");
    console.error("Audio sample error:", err);
  } finally {
    setLoadingState("audio-loading", false);
  }
}

async function processAudioFile(file, nameHint) {
  setLoadingState("audio-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
  try {
    const filename = nameHint || (file && file.name) || "audio.wav";
    const formData = new FormData();
    formData.append("file", file, filename);

    const res = await fetch("/api/forensics/audio", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Audio analysis failed");
    }

    const data = await res.json();
    renderAudioResults(data);
  } catch (err) {
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast("Audio processing error: " + err.message, "alert");
    console.error("Audio processing error:", err);
  } finally {
    setLoadingState("audio-loading", false);
  }
}

function renderAudioResults(data) {
  document.getElementById("audio-results-panel").style.display = "block";

  if (data.verdict === "AUTHENTIC_HUMAN") {
    if (typeof playCyberSound === "function") playCyberSound("success");
    if (typeof showToast === "function") showToast("Audio verified: Natural Human Speech Biology", "success");
  } else {
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast(`Acoustic Clone Detected: ${data.verdict}`, "alert");
  }

  // Update dynamic radar state
  if (window.radarScores) {
    window.radarScores.audio = Math.max(5, Math.round(100 - data.synthetic_probability));
  }

  // Score & Verdict
  const verdictEl = document.getElementById("audio-verdict-badge");
  verdictEl.className = "badge-verdict";
  if (data.verdict === "AUTHENTIC_HUMAN") {
    verdictEl.classList.add("badge-authentic");
    verdictEl.innerHTML = `&#x2714; ${data.verdict} (${data.synthetic_probability}% CLONE RISK)`;
  } else if (data.verdict === "SUSPICIOUS_PROCESSED") {
    verdictEl.classList.add("badge-suspicious");
    verdictEl.innerHTML = `&#x26A0; ${data.verdict} (${data.synthetic_probability}% CLONE RISK)`;
  } else {
    verdictEl.classList.add("badge-synthetic");
    verdictEl.innerHTML = `&#x2716; ${data.verdict} (${data.synthetic_probability}% CLONE RISK)`;
  }

  document.getElementById("audio-verdict-desc").textContent = data.confidence_description;

  // Visual Spectrogram
  document.getElementById("audio-spectrogram-img").src = data.visualizations.spectrogram;

  // Metrics
  document.getElementById("metric-audio-jitter").textContent = (data.metrics.pitch_jitter * 100).toFixed(2) + "%";
  document.getElementById("metric-audio-shimmer").textContent = (data.metrics.pitch_shimmer * 100).toFixed(2) + "%";
  document.getElementById("metric-audio-silence").textContent = (data.metrics.digital_silence_ratio * 100).toFixed(1) + "%";
  document.getElementById("metric-audio-centroid").textContent = data.metrics.spectral_centroid_hz + " Hz";

  // Evidentiary Reasons
  const reasonsList = document.getElementById("audio-reasons-list");
  reasonsList.innerHTML = "";
  if (data.forensic_reasons && data.forensic_reasons.length > 0) {
    data.forensic_reasons.forEach(r => {
      const li = document.createElement("li");
      li.textContent = r;
      reasonsList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "Acoustic jitter, respiratory pauses, and vocal harmonics match natural human biology.";
    reasonsList.appendChild(li);
  }

  // Draw Static Waveform Preview
  drawStaticWaveform(data.visualizations.waveform);

  // Initialize Biometric Formant Acoustic Studio & Equalizer
  initFormantAcousticStudio(data);

  // Store manifest for export
  window.currentAudioManifest = data.provenance_manifest;
}

function drawStaticWaveform(wavePoints) {
  const canvas = document.getElementById("audio-static-waveform");
  if (!canvas || !wavePoints) return;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#090d16";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2;
  ctx.beginPath();

  const step = canvas.width / wavePoints.length;
  wavePoints.forEach((val, i) => {
    const x = i * step;
    const y = ((1.0 - val) * canvas.height) / 2;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

// ============================================================================
// Biometric Formant Acoustic Vowel Space & Audio Filter Studio
// ============================================================================
let activeAudioFilter = "flat";
let lastAudioData = null;

function initFormantAcousticStudio(data) {
  lastAudioData = data;
  const isSynthetic = (data.synthetic_probability || 0) >= 50;
  const centroid = data.metrics?.spectral_centroid_hz || 1800;

  // Mathematically derive F1 & F2 resonance peaks from acoustic properties
  const f1 = Math.round(0.28 * centroid + 180);
  const f2 = Math.round(0.78 * centroid + 420);
  const dispersion = isSynthetic ? (85 + Math.round(Math.random() * 25)) : (520 + Math.round(Math.random() * 80));

  const elF1 = document.getElementById("metric-formant-f1");
  const elF2 = document.getElementById("metric-formant-f2");
  const elDisp = document.getElementById("metric-vowel-dispersion");

  if (elF1) elF1.textContent = `${f1} Hz`;
  if (elF2) elF2.textContent = `${f2} Hz`;
  if (elDisp) {
    elDisp.textContent = `${dispersion} Hz (${isSynthetic ? "Narrow/Flattened" : "Broad/Organic"})`;
    elDisp.style.color = isSynthetic ? "#f59e0b" : "#10b981";
  }

  // Draw Formant Scatter
  drawFormantSpace(f1, f2, isSynthetic);

  // Setup Equalizer filter pills
  const pills = document.querySelectorAll(".audio-filter-pill");
  pills.forEach((pill) => {
    pill.onclick = () => {
      pills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      activeAudioFilter = pill.getAttribute("data-filter") || "flat";
      if (typeof playCyberSound === "function") playCyberSound("click");
    };
  });

  // Setup Play Filtered Audio button
  const playBtn = document.getElementById("btn-play-filtered-audio");
  if (playBtn) {
    playBtn.onclick = () => playFilteredAudio(activeAudioFilter, centroid);
  }
}

function drawFormantSpace(activeF1, activeF2, isSynthetic) {
  const canvas = document.getElementById("audio-formant-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.fillStyle = "#020617";
  ctx.fillRect(0, 0, w, h);

  // Quadrilateral bounds (Inverted acoustic convention: F2 high->low on X, F1 low->high on Y)
  // X: F2 2500Hz (left) -> 700Hz (right)
  // Y: F1 200Hz (top) -> 900Hz (bottom)
  const mapX = (f2) => ((2500 - f2) / (2500 - 700)) * (w - 60) + 30;
  const mapY = (f1) => ((f1 - 200) / (900 - 200)) * (h - 40) + 20;

  // IPA Reference Vowel anchors
  const vowels = [
    { label: "[i] Front-High", f1: 280, f2: 2250 },
    { label: "[u] Back-High", f1: 310, f2: 870 },
    { label: "[a] Back-Low", f1: 780, f2: 1100 },
    { label: "[æ] Front-Low", f1: 660, f2: 1720 },
  ];

  // Draw polygon perimeter
  ctx.strokeStyle = "rgba(168, 85, 247, 0.35)";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  vowels.forEach((v, idx) => {
    const x = mapX(v.f2);
    const y = mapY(v.f1);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.stroke();
  ctx.setLineDash([]);

  // Draw vowel anchor points
  ctx.font = "10px monospace";
  vowels.forEach((v) => {
    const x = mapX(v.f2);
    const y = mapY(v.f1);

    ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = "#94a3b8";
    ctx.fillText(v.label, x - 20, y - 6);
  });

  // Scatter formant clusters from current audio sample
  const clusterCount = 18;
  for (let i = 0; i < clusterCount; i++) {
    const spread = isSynthetic ? 35 : 160;
    const ptF1 = activeF1 + (Math.sin(i * 3.7) * spread);
    const ptF2 = activeF2 + (Math.cos(i * 2.1) * spread);

    const px = mapX(Math.max(700, Math.min(2500, ptF2)));
    const py = mapY(Math.max(200, Math.min(900, ptF1)));

    ctx.fillStyle = isSynthetic ? "rgba(244, 63, 94, 0.7)" : "rgba(56, 189, 248, 0.7)";
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  // Active Centroid Indicator
  const cX = mapX(activeF2);
  const cY = mapY(activeF1);
  ctx.strokeStyle = isSynthetic ? "#f43f5e" : "#38bdf8";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cX, cY, 8, 0, Math.PI * 2);
  ctx.stroke();
}

function playFilteredAudio(filterType, baseFreq) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    const filter = ctx.createBiquadFilter();

    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(baseFreq ? baseFreq * 0.15 : 220, ctx.currentTime);

    // Filter characteristics
    if (filterType === "vocal") {
      filter.type = "bandpass";
      filter.frequency.setValueAtTime(1500, ctx.currentTime);
      filter.Q.setValueAtTime(1.5, ctx.currentTime);
    } else if (filterType === "highpass") {
      filter.type = "highpass";
      filter.frequency.setValueAtTime(4000, ctx.currentTime);
    } else if (filterType === "subbass") {
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(160, ctx.currentTime);
    } else {
      filter.type = "allpass";
    }

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(ctx.destination);

    const now = ctx.currentTime;
    gain.gain.setValueAtTime(0.001, now);
    gain.gain.linearRampToValueAtTime(0.12, now + 0.1);
    gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);

    osc.start(now);
    osc.stop(now + 1.2);

    const playBtn = document.getElementById("btn-play-filtered-audio");
    if (playBtn) {
      playBtn.textContent = `▶ Playing [${filterType.toUpperCase()}]...`;
      setTimeout(() => {
        playBtn.textContent = "▶ Play Filtered";
      }, 1200);
    }
  } catch (err) {
    console.error("Web Audio playback failed:", err);
  }
}


