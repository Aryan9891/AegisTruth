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
      alert("Microphone access failed: " + err.message);
    }
  }
}

function drawLiveMicWaveform(canvas, analyser) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  function render() {
    animationFrameId = requestAnimationFrame(render);
    analyser.getByteTimeDomainData(dataArray);

    ctx.fillStyle = "#090d16";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#06b6d4";
    ctx.beginPath();

    const sliceWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * canvas.height) / 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      x += sliceWidth;
    }

    ctx.lineTo(canvas.width, canvas.height / 2);
    ctx.stroke();
  }
  render();
}

async function loadSampleAudio(filename) {
  // Generate synthetic audio wave in memory
  const sampleRate = 22050;
  const duration = 2.0;
  const numSamples = sampleRate * duration;
  const buffer = new ArrayBuffer(44 + numSamples * 2);
  const view = new DataView(buffer);

  // Write simple WAV Header
  function writeString(offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + numSamples * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, numSamples * 2, true);

  // Generate PCM data
  let offset = 44;
  const isClone = filename.includes("clone");
  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    let sample = 0;
    if (isClone) {
      // Hyper-flat constant pitch 140Hz with dead silence interval
      if (t > 0.4 && t < 1.6) {
        sample = Math.sin(2 * Math.PI * 140.0 * t);
      }
    } else {
      // Natural human wave with micro-jitter tremor
      const jitter = 1.0 + 0.015 * Math.sin(2 * Math.PI * 7.0 * t);
      sample = 0.6 * Math.sin(2 * Math.PI * 140.0 * t * jitter) + 0.02 * (Math.random() - 0.5);
    }
    view.setInt16(offset, Math.max(-1, Math.min(1, sample)) * 32767, true);
    offset += 2;
  }

  const blob = new Blob([buffer], { type: "audio/wav" });
  await processAudioFile(blob);
}

async function processAudioFile(file) {
  setLoadingState("audio-loading", true);
  try {
    const formData = new FormData();
    formData.append("file", file, "audio.wav");

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
    alert("Audio processing error: " + err.message);
  } finally {
    setLoadingState("audio-loading", false);
  }
}

function renderAudioResults(data) {
  document.getElementById("audio-results-panel").style.display = "block";

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

