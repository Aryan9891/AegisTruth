// AegisTruth Video Deepfake & Temporal Forensics Lab

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("video-dropzone");
  const fileInput = document.getElementById("video-file-input");
  const sampleRealBtn = document.getElementById("btn-sample-video-real");
  const sampleFakeBtn = document.getElementById("btn-sample-video-fake");

  if (dropzone && fileInput) {
    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files.length > 0) {
        processVideoFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        processVideoFile(fileInput.files[0]);
      }
    });
  }

  if (sampleRealBtn) {
    sampleRealBtn.addEventListener("click", () => loadSampleVideo("sample_video_real.gif"));
  }

  if (sampleFakeBtn) {
    sampleFakeBtn.addEventListener("click", () => loadSampleVideo("sample_video_deepfake.gif"));
  }
});

async function loadSampleVideo(filename) {
  setLoadingState("video-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
  try {
    const directSample = await fetch(`/static/samples/${filename}`);
    if (!directSample.ok) throw new Error("Could not fetch sample video asset");
    
    const blob = await directSample.blob();
    const fData = new FormData();
    fData.append("file", blob, filename);

    const res = await fetch("/api/forensics/video", {
      method: "POST",
      body: fData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Video analysis failed");
    }

    const data = await res.json();
    renderVideoResults(data);
  } catch (err) {
    alert("Video sample error: " + err.message);
  } finally {
    setLoadingState("video-loading", false);
  }
}

function createDummyVideoBlob(frames) {
  const fData = new FormData();
  // Simple binary payload
  const blob = new Blob(["GIF89a..."], { type: "image/gif" });
  fData.append("file", blob, "sample.gif");
  return fData;
}

async function processVideoFile(file) {
  setLoadingState("video-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/api/forensics/video", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Video analysis failed");
    }

    const data = await res.json();
    renderVideoResults(data);
  } catch (err) {
    alert("Video analysis error: " + err.message);
  } finally {
    setLoadingState("video-loading", false);
  }
}

function renderVideoResults(data) {
  document.getElementById("video-results-panel").style.display = "block";

  // Play audio and toast feedback
  if (data.verdict === "AUTHENTIC_RECORDING") {
    if (typeof playCyberSound === "function") playCyberSound("success");
    if (typeof showToast === "function") showToast("Video verified: Continuous Optical Capture", "success");
  } else {
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast(`Temporal Deepfake Risk Detected: ${data.verdict}`, "alert");
  }

  // Update dynamic radar state
  if (window.radarScores) {
    window.radarScores.video = Math.max(5, Math.round(100 - data.synthetic_probability));
  }

  // Score & Verdict
  const verdictEl = document.getElementById("video-verdict-badge");
  verdictEl.className = "badge-verdict";
  if (data.verdict === "AUTHENTIC_RECORDING") {
    verdictEl.classList.add("badge-authentic");
    verdictEl.innerHTML = `&#x2714; ${data.verdict} (${data.synthetic_probability}% DEEPFAKE RISK)`;
  } else if (data.verdict === "SUSPICIOUS_TEMPORAL_ANOMALY") {
    verdictEl.classList.add("badge-suspicious");
    verdictEl.innerHTML = `&#x26A0; ${data.verdict} (${data.synthetic_probability}% DEEPFAKE RISK)`;
  } else {
    verdictEl.classList.add("badge-synthetic");
    verdictEl.innerHTML = `&#x2716; ${data.verdict} (${data.synthetic_probability}% DEEPFAKE RISK)`;
  }

  document.getElementById("video-verdict-desc").textContent = data.confidence_description;

  // Keyframe
  if (data.visualizations.keyframe_thumbnail) {
    document.getElementById("video-keyframe-img").src = data.visualizations.keyframe_thumbnail;
  }

  // Metrics
  document.getElementById("metric-video-frames").textContent = data.metrics.frames_analyzed;
  document.getElementById("metric-video-flicker").textContent = data.metrics.temporal_flicker_score;
  document.getElementById("metric-video-spikes").textContent = data.metrics.discontinuity_spikes_count;
  document.getElementById("metric-video-grid").textContent = data.metrics.keyframe_grid_spike_ratio;

  // Render Frame-by-Frame Optical Difference Chart
  drawTimelineChart(data.visualizations.timeline_diffs);

  // Evidentiary Reasons
  const reasonsList = document.getElementById("video-reasons-list");
  reasonsList.innerHTML = "";
  if (data.forensic_reasons && data.forensic_reasons.length > 0) {
    data.forensic_reasons.forEach(r => {
      const li = document.createElement("li");
      li.textContent = r;
      reasonsList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "Inter-frame motion flow and edge sharpness remain continuous with zero generative flicker.";
    reasonsList.appendChild(li);
  }

  window.currentVideoManifest = data.provenance_manifest;
}

function drawTimelineChart(diffs) {
  const canvas = document.getElementById("video-timeline-canvas");
  if (!canvas || !diffs || diffs.length === 0) return;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#090d16";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const maxVal = Math.max(...diffs, 10);
  const step = canvas.width / (diffs.length + 1);

  // Draw grid lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  for (let y = 20; y < canvas.height; y += 25) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(canvas.width, y);
    ctx.stroke();
  }

  // Draw timeline bars
  diffs.forEach((val, i) => {
    const barHeight = (val / maxVal) * (canvas.height - 20);
    const x = i * step + 10;
    const y = canvas.height - barHeight - 5;

    ctx.fillStyle = val > 400 ? "#f43f5e" : "#38bdf8";
    ctx.fillRect(x, y, Math.max(step - 4, 3), barHeight);
  });
}

