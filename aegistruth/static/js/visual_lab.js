// AegisTruth Visual Forensics Lab (Image & Deepfake Analysis) - Interactive Slider Edition

let isDraggingSlider = false;

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

  initComparisonSlider();
});

function initComparisonSlider() {
  const container = document.getElementById("comparison-container");
  const handle = document.getElementById("comparison-handle");
  const overlay = document.getElementById("comparison-overlay");

  if (!container || !handle || !overlay) return;

  function setSliderPos(x) {
    const rect = container.getBoundingClientRect();
    let pos = (x - rect.left) / rect.width;
    pos = Math.max(0.02, Math.min(0.98, pos));
    handle.style.left = `${pos * 100}%`;
    overlay.style.width = `${pos * 100}%`;
  }

  handle.addEventListener("mousedown", () => { isDraggingSlider = true; });
  window.addEventListener("mouseup", () => { isDraggingSlider = false; });
  window.addEventListener("mousemove", (e) => {
    if (isDraggingSlider) setSliderPos(e.clientX);
  });

  // Touch support for mobile/tablet
  handle.addEventListener("touchstart", () => { isDraggingSlider = true; });
  window.addEventListener("touchend", () => { isDraggingSlider = false; });
  window.addEventListener("touchmove", (e) => {
    if (isDraggingSlider && e.touches.length > 0) {
      setSliderPos(e.touches[0].clientX);
    }
  });
}

async function loadSampleImage(filename) {
  setLoadingState("image-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
  try {
    const directSample = await fetch(`/static/samples/${filename}`);
    if (!directSample.ok) throw new Error("Could not fetch sample image asset");

    const blob = await directSample.blob();
    const formData = new FormData();
    formData.append("file", blob, filename);

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
    alert("Error analyzing sample: " + err.message);
  } finally {
    setLoadingState("image-loading", false);
  }
}

async function processImageFile(file) {
  setLoadingState("image-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
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

  // Play sound according to result
  if (data.verdict === "AUTHENTIC") {
    if (typeof playCyberSound === "function") playCyberSound("success");
    if (typeof showToast === "function") showToast("Image verified as Authentic Camera Capture", "success");
  } else {
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast(`Visual Deepfake Detected: ${data.verdict}`, "alert");
  }

  // Update Radial Threat Gauge
  if (typeof updateRadialGauge === "function") {
    updateRadialGauge("image-gauge-circle", "image-gauge-score", data.synthetic_probability, true);
  }

  // Update dynamic radar state
  if (window.radarScores) {
    window.radarScores.visual = Math.max(5, Math.round(100 - data.synthetic_probability));
  }

  // Verdict Badge
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

  // Split slider images
  const sliderOrig = document.getElementById("slider-img-orig");
  const sliderEla = document.getElementById("slider-img-ela");
  if (sliderOrig && sliderEla) {
    sliderOrig.src = data.visualizations.original;
    sliderEla.src = data.visualizations.ela;
  }

  // Visuals in 3-way split
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
    li.textContent = "All visual indicators match organic camera sensor capture.";
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
