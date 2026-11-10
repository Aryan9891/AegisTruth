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

  // Clicking anywhere on container snaps slider
  container.addEventListener("click", (e) => {
    setSliderPos(e.clientX);
  });

  // Enhanced touch support for mobile & tablet screens
  function handleTouch(e) {
    if (e.touches && e.touches.length > 0) {
      setSliderPos(e.touches[0].clientX);
    }
  }

  handle.addEventListener("touchstart", (e) => {
    isDraggingSlider = true;
    handleTouch(e);
  }, { passive: true });

  container.addEventListener("touchstart", (e) => {
    isDraggingSlider = true;
    handleTouch(e);
  }, { passive: true });

  window.addEventListener("touchend", () => { isDraggingSlider = false; });
  window.addEventListener("touchcancel", () => { isDraggingSlider = false; });

  window.addEventListener("touchmove", (e) => {
    if (isDraggingSlider) {
      handleTouch(e);
    }
  }, { passive: true });
}

async function loadSampleImage(filename) {
  setLoadingState("image-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
  try {
    let directSample = await fetch(`samples/${filename}`).catch(() => null);
    if (!directSample || !directSample.ok) {
      directSample = await fetch(`./samples/${filename}`).catch(() => null);
    }
    if (!directSample || !directSample.ok) {
      directSample = await fetch(`/static/samples/${filename}`).catch(() => null);
    }
    if (!directSample || !directSample.ok) throw new Error("Could not fetch sample image asset");

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
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast("Error analyzing sample: " + err.message, "alert");
    console.error("Error analyzing sample:", err);
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
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast("Image analysis error: " + err.message, "alert");
    console.error("Image analysis error:", err);
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

  // Store visualizations globally for lens switching
  window.activeVisualizations = data.visualizations;

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
  document.getElementById("metric-grid-ratio").textContent = data.metrics?.frequency_domain?.grid_spike_ratio ?? "--";
  document.getElementById("metric-high-freq").textContent = data.metrics?.frequency_domain?.high_freq_ratio ?? "--";
  document.getElementById("metric-ela-var").textContent = data.metrics?.ela?.error_variance ?? "--";
  document.getElementById("metric-noise-discrepancy").textContent = data.metrics?.noise_residuals?.quadrant_discrepancy ?? "--";

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

  // Initialize Multi-Spectral Microscope & Bit-Plane Slicer
  if (data.visualizations && data.visualizations.original) {
    initMicroscope(data.visualizations.original);
  }
}

function setLoadingState(elId, isLoading) {
  const el = document.getElementById(elId);
  if (el) {
    el.style.display = isLoading ? "block" : "none";
  }
}

window.switchComparisonLens = function(lensType) {
  const sliderEla = document.getElementById("slider-img-ela");
  const title = document.getElementById("slider-lens-title");
  if (!sliderEla || !window.activeVisualizations) return;

  if (lensType === "ela") {
    sliderEla.src = window.activeVisualizations.ela;
    if (title) title.textContent = "Original vs ELA Compression Heatmap";
  } else if (lensType === "fft") {
    sliderEla.src = window.activeVisualizations.fft_spectrum;
    if (title) title.textContent = "Original vs 2D Fourier (FFT) Spatial Spectrum";
  }

  // Update button active state
  document.querySelectorAll(".lens-mode-pill").forEach(p => p.classList.remove("active"));
  const activeBtn = document.getElementById(`btn-lens-${lensType}`);
  if (activeBtn) activeBtn.classList.add("active");

  if (typeof playCyberSound === "function") playCyberSound("click");
};

// ============================================================================
// Multi-Spectral Microscope & Bit-Plane Slicing Architecture
// ============================================================================
let microscopeImg = null;
let microscopeActiveLens = "original";
let isLoupeActive = false;

function initMicroscope(src) {
  const canvas = document.getElementById("microscope-canvas");
  if (!canvas) return;

  microscopeImg = new Image();
  microscopeImg.crossOrigin = "anonymous";
  microscopeImg.onload = () => {
    // Set internal canvas resolution
    canvas.width = microscopeImg.naturalWidth || microscopeImg.width || 600;
    canvas.height = microscopeImg.naturalHeight || microscopeImg.height || 400;
    renderMicroscopeMode(microscopeActiveLens);
    setupMicroscopeEvents();
  };
  microscopeImg.src = src;
}

function renderMicroscopeMode(mode) {
  const canvas = document.getElementById("microscope-canvas");
  if (!canvas || !microscopeImg) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  // Draw master base image
  ctx.drawImage(microscopeImg, 0, 0, w, h);
  if (mode === "original") return;

  const imgData = ctx.getImageData(0, 0, w, h);
  const data = imgData.data;
  const len = data.length;

  if (mode.startsWith("bit")) {
    const bitIndex = parseInt(mode.replace("bit", ""), 10);
    const mask = 1 << bitIndex;
    for (let i = 0; i < len; i += 4) {
      // Extract binary bit value and amplify to full [0, 255] contrast
      const bR = (data[i] & mask) ? 255 : 0;
      const bG = (data[i + 1] & mask) ? 255 : 0;
      const bB = (data[i + 2] & mask) ? 255 : 0;
      const avg = Math.round((bR + bG + bB) / 3);
      data[i] = avg;
      data[i + 1] = avg;
      data[i + 2] = avg;
    }
  } else if (mode === "red") {
    for (let i = 0; i < len; i += 4) {
      data[i + 1] = 0;
      data[i + 2] = 0;
    }
  } else if (mode === "green") {
    for (let i = 0; i < len; i += 4) {
      data[i] = 0;
      data[i + 2] = 0;
    }
  } else if (mode === "blue") {
    for (let i = 0; i < len; i += 4) {
      data[i] = 0;
      data[i + 1] = 0;
    }
  } else if (mode === "ycbcr") {
    for (let i = 0; i < len; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      // Chrominance Blue Cb & Chrominance Red Cr
      const cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b;
      const cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b;
      data[i] = Math.min(255, Math.max(0, cr));
      data[i + 1] = Math.min(255, Math.max(0, (cb + cr) / 2));
      data[i + 2] = Math.min(255, Math.max(0, cb));
    }
  } else if (mode === "sobel") {
    // 3x3 Sobel high-pass gradient kernel on luminance
    const copy = new Uint8ClampedArray(data);
    for (let y = 1; y < h - 1; y++) {
      for (let x = 1; x < w - 1; x++) {
        const idx = (y * w + x) * 4;

        // Grayscale sampling for 3x3
        const getGray = (ox, oy) => {
          const p = ((y + oy) * w + (x + ox)) * 4;
          return 0.299 * copy[p] + 0.587 * copy[p + 1] + 0.114 * copy[p + 2];
        };

        const gx =
          -1 * getGray(-1, -1) + 1 * getGray(1, -1) +
          -2 * getGray(-1,  0) + 2 * getGray(1,  0) +
          -1 * getGray(-1,  1) + 1 * getGray(1,  1);

        const gy =
          -1 * getGray(-1, -1) - 2 * getGray(0, -1) - 1 * getGray(1, -1) +
           1 * getGray(-1,  1) + 2 * getGray(0,  1) + 1 * getGray(1,  1);

        const mag = Math.min(255, Math.sqrt(gx * gx + gy * gy) * 1.5);
        data[idx] = mag;
        data[idx + 1] = mag;
        data[idx + 2] = mag;
      }
    }
  }

  ctx.putImageData(imgData, 0, 0);
}

function setupMicroscopeEvents() {
  // Lens selector buttons
  const pills = document.querySelectorAll(".microscope-nav .lens-mode-pill");
  pills.forEach((pill) => {
    pill.onclick = () => {
      pills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      microscopeActiveLens = pill.getAttribute("data-lens") || "original";
      renderMicroscopeMode(microscopeActiveLens);
      if (typeof playCyberSound === "function") playCyberSound("click");
    };
  });

  // Loupe button
  const loupeBtn = document.getElementById("btn-toggle-loupe");
  const reticle = document.getElementById("loupe-reticle");
  if (loupeBtn && reticle) {
    loupeBtn.onclick = () => {
      isLoupeActive = !isLoupeActive;
      if (isLoupeActive) {
        loupeBtn.innerHTML = "&#x1F50D; 4x Precision Loupe: ON";
        loupeBtn.classList.add("active");
        reticle.style.display = "block";
      } else {
        loupeBtn.innerHTML = "&#x1F50D; 4x Precision Loupe: OFF";
        loupeBtn.classList.remove("active");
        reticle.style.display = "none";
      }
      if (typeof playCyberSound === "function") playCyberSound("click");
    };
  }

  // Canvas mouse / touch tracking for Loupe
  const canvas = document.getElementById("microscope-canvas");
  const loupeCanvas = document.getElementById("loupe-canvas");
  const loupeInfo = document.getElementById("loupe-info");

  if (!canvas || !loupeCanvas || !reticle) return;

  function updateLoupe(clientX, clientY) {
    if (!isLoupeActive) return;
    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;

    if (x < 0 || y < 0 || x > rect.width || y > rect.height) {
      reticle.style.display = "none";
      return;
    }
    reticle.style.display = "block";

    // Position reticle relative to canvas parent
    const reticleSize = 120;
    const posX = x - reticleSize / 2;
    const posY = y - reticleSize / 2;
    reticle.style.left = `${posX}px`;
    reticle.style.top = `${posY}px`;

    // Map screen x, y to internal canvas coordinates
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const imgX = Math.round(x * scaleX);
    const imgY = Math.round(y * scaleY);

    // 4x zoom crop (30x30 region)
    const cropSize = 30;
    const lCtx = loupeCanvas.getContext("2d");
    lCtx.imageSmoothingEnabled = false;
    lCtx.clearRect(0, 0, reticleSize, reticleSize);
    lCtx.drawImage(
      canvas,
      Math.max(0, imgX - cropSize / 2),
      Math.max(0, imgY - cropSize / 2),
      cropSize,
      cropSize,
      0,
      0,
      reticleSize,
      reticleSize
    );

    // Crosshairs
    lCtx.strokeStyle = "rgba(0, 243, 255, 0.7)";
    lCtx.lineWidth = 1;
    lCtx.beginPath();
    lCtx.moveTo(reticleSize / 2, 0);
    lCtx.lineTo(reticleSize / 2, reticleSize);
    lCtx.moveTo(0, reticleSize / 2);
    lCtx.lineTo(reticleSize, reticleSize / 2);
    lCtx.stroke();

    // Sample single center pixel for RGB readout
    try {
      const p = canvas.getContext("2d").getImageData(imgX, imgY, 1, 1).data;
      if (loupeInfo) {
        loupeInfo.textContent = `RGB(${p[0]}, ${p[1]}, ${p[2]}) | [${imgX}, ${imgY}]`;
      }
    } catch (_) {}
  }

  canvas.addEventListener("mousemove", (e) => updateLoupe(e.clientX, e.clientY));
  canvas.addEventListener("touchmove", (e) => {
    if (e.touches && e.touches[0]) {
      updateLoupe(e.touches[0].clientX, e.touches[0].clientY);
    }
  }, { passive: true });
}

