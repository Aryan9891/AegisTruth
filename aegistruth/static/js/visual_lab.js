// AegisTruth Visual Forensics Lab (Image & Deepfake Analysis)

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("image-dropzone");
  const fileInput = document.getElementById("image-file-input");
  const sampleRealBtn = document.getElementById("btn-sample-image-real");
  const sampleSynthBtn = document.getElementById("btn-sample-image-synth");

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
        processImageFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        processImageFile(fileInput.files[0]);
      }
    });
  }

  if (sampleRealBtn) {
    sampleRealBtn.addEventListener("click", () => loadSampleImage("sample_real.jpg"));
  }

  if (sampleSynthBtn) {
    sampleSynthBtn.addEventListener("click", () => loadSampleImage("sample_synthetic.jpg"));
  }
});

async function loadSampleImage(filename) {
  setLoadingState("image-loading", true);
  try {
    // Generate synthetic on canvas or fetch sample
    const canvas = document.createElement("canvas");
    canvas.width = 400;
    canvas.height = 400;
    const ctx = canvas.getContext("2d");

    if (filename.includes("real")) {
      // Draw organic gradient landscape
      const grad = ctx.createLinearGradient(0, 0, 0, 400);
      grad.addColorStop(0, "#38bdf8");
      grad.addColorStop(0.6, "#bae6fd");
      grad.addColorStop(1, "#15803d");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 400, 400);
      ctx.fillStyle = "#eab308";
      ctx.beginPath();
      ctx.arc(80, 80, 40, 0, Math.PI * 2);
      ctx.fill();
    } else {
      // Draw synthetic with repetitive grid patterns & sharp inpainting
      ctx.fillStyle = "#64748b";
      ctx.fillRect(0, 0, 400, 400);
      // Periodic checkerboard lines
      ctx.strokeStyle = "#94a3b8";
      for (let i = 0; i < 400; i += 8) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, 400);
        ctx.stroke();
      }
      ctx.fillStyle = "#ef4444";
      ctx.fillRect(140, 140, 120, 120);
    }

    const b64 = canvas.toDataURL("image/jpeg", 0.9);
    const res = await fetch("/api/forensics/image/base64", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_base64: b64 }),
    });

    if (!res.ok) throw new Error("Analysis failed");
    const data = await res.json();
    renderImageResults(data);
  } catch (err) {
    alert("Error analyzing sample: " + err.message);
  } finally {
    setLoadingState("image-loading", false);
  }
}

async function processImageFile(file) {
  setLoadingState("image-loading", true);
  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/api/forensics/image", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis request failed");
    }

    const data = await res.json();
    renderImageResults(data);
  } catch (err) {
    alert("Image analysis error: " + err.message);
  } finally {
    setLoadingState("image-loading", false);
  }
}

function renderImageResults(data) {
  document.getElementById("image-results-panel").style.display = "block";

  // Score & Verdict
  const verdictEl = document.getElementById("image-verdict-badge");
  verdictEl.className = "badge-verdict";
  if (data.verdict === "AUTHENTIC") {
    verdictEl.classList.add("badge-authentic");
    verdictEl.innerHTML = `&#x2714; ${data.verdict} (${data.synthetic_probability}% AI PROBABILITY)`;
  } else if (data.verdict === "SUSPICIOUS_TAMPERED") {
    verdictEl.classList.add("badge-suspicious");
    verdictEl.innerHTML = `&#x26A0; ${data.verdict} (${data.synthetic_probability}% AI PROBABILITY)`;
  } else {
    verdictEl.classList.add("badge-synthetic");
    verdictEl.innerHTML = `&#x2716; ${data.verdict} (${data.synthetic_probability}% AI PROBABILITY)`;
  }

  document.getElementById("image-verdict-desc").textContent = data.confidence_description;

  // Visuals
  document.getElementById("img-view-original").src = data.visualizations.original;
  document.getElementById("img-view-ela").src = data.visualizations.ela;
  document.getElementById("img-view-fft").src = data.visualizations.fft_spectrum;

  // Metrics
  document.getElementById("metric-grid-ratio").textContent = data.metrics.frequency_domain.grid_spike_ratio;
  document.getElementById("metric-high-freq").textContent = data.metrics.frequency_domain.high_freq_ratio;
  document.getElementById("metric-ela-var").textContent = data.metrics.ela.error_variance;
  document.getElementById("metric-noise-discrepancy").textContent = data.metrics.noise_residuals.quadrant_discrepancy;

  // Evidentiary Reasons
  const reasonsList = document.getElementById("image-reasons-list");
  reasonsList.innerHTML = "";
  if (data.forensic_reasons && data.forensic_reasons.length > 0) {
    data.forensic_reasons.forEach(r => {
      const li = document.createElement("li");
      li.textContent = r;
      reasonsList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "All visual indicators match organic sensor capture.";
    reasonsList.appendChild(li);
  }

  // Store manifest for export
  window.currentImageManifest = data.provenance_manifest;
}

function setLoadingState(elId, isLoading) {
  const el = document.getElementById(elId);
  if (el) {
    el.style.display = isLoading ? "block" : "none";
  }
}

