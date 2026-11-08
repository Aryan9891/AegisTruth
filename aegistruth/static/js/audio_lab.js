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

