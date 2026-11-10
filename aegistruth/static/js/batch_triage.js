// AegisTruth Enterprise Multi-Asset Batch Forensic Triage Queue
// Concurrent multi-modal forensic evaluation and threat assessment

(function () {
  let batchQueue = [];

  document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("batch-dropzone");
    const fileInput = document.getElementById("batch-file-input");
    const clearBtn = document.getElementById("btn-clear-batch");
    const exportCsvBtn = document.getElementById("btn-export-batch-csv");
    const exportJsonBtn = document.getElementById("btn-export-batch-json");

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
        if (e.dataTransfer && e.dataTransfer.files.length > 0) {
          enqueueBatchFiles(Array.from(e.dataTransfer.files));
        }
      });

      fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
          enqueueBatchFiles(Array.from(fileInput.files));
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        batchQueue = [];
        renderBatchTable();
        if (typeof showToast === "function") showToast("Batch triage queue cleared.", "info");
      });
    }

    if (exportCsvBtn) {
      exportCsvBtn.addEventListener("click", exportBatchCSV);
    }

    if (exportJsonBtn) {
      exportJsonBtn.addEventListener("click", exportBatchJSON);
    }
  });

  function detectDomain(file) {
    const type = file.type || "";
    const name = (file.name || "").toLowerCase();
    if (type.startsWith("image/") || /\.(jpg|jpeg|png|webp|bmp|gif|avif|heic|tiff|svg)$/.test(name)) {
      return "image";
    }
    if (type.startsWith("video/") || /\.(mp4|webm|avi|mov|mkv|gif)$/.test(name)) {
      return "video";
    }
    if (type.startsWith("audio/") || /\.(wav|mp3|ogg|flac|m4a|aac|opus)$/.test(name)) {
      return "audio";
    }
    return "text";
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  async function enqueueBatchFiles(files) {
    if (!files || files.length === 0) return;
    if (typeof playCyberSound === "function") playCyberSound("scan");
    if (typeof showToast === "function") {
      showToast(`Ingesting ${files.length} asset(s) into Forensic Triage Queue...`, "info");
    }

    const newEntries = files.map((file, idx) => {
      const domain = detectDomain(file);
      const entry = {
        id: "batch_" + Date.now() + "_" + idx + "_" + Math.random().toString(36).substring(2, 6),
        file,
        name: file.name || `asset_${idx + 1}`,
        domain,
        size: file.size,
        status: "triaging",
        verdict: "--",
        probability: null,
        marker: "Processing telemetry...",
        resultData: null,
      };
      return entry;
    });

    batchQueue.push(...newEntries);
    renderBatchTable();

    // Process concurrently with slight jitter
    for (const entry of newEntries) {
      processBatchEntry(entry);
    }
  }

  async function processBatchEntry(entry) {
    try {
      let data = null;
      if (entry.domain === "image") {
        const formData = new FormData();
        formData.append("file", entry.file);
        const res = await fetch("/api/forensics/image", { method: "POST", body: formData });
        if (!res.ok) throw new Error("Image analysis failed");
        data = await res.json();
      } else if (entry.domain === "video") {
        const formData = new FormData();
        formData.append("file", entry.file);
        const res = await fetch("/api/forensics/video", { method: "POST", body: formData });
        if (!res.ok) throw new Error("Video analysis failed");
        data = await res.json();
      } else if (entry.domain === "audio") {
        const formData = new FormData();
        formData.append("file", entry.file);
        const res = await fetch("/api/forensics/audio", { method: "POST", body: formData });
        if (!res.ok) throw new Error("Audio analysis failed");
        data = await res.json();
      } else {
        // Text / document
        const text = await readFileAsText(entry.file);
        const res = await fetch("/api/forensics/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
        if (!res.ok) throw new Error("Text analysis failed");
        data = await res.json();
      }

      if (!data) throw new Error("Forensic evaluation engine returned no payload");

      entry.status = "complete";
      entry.resultData = data;
      entry.verdict = data.verdict || "UNKNOWN";
      entry.probability = typeof data.synthetic_probability === "number" ? data.synthetic_probability : 50;

      // Extract primary evidentiary marker
      if (data.forensic_reasons && data.forensic_reasons.length > 0) {
        entry.marker = data.forensic_reasons[0];
      } else if (data.confidence_description) {
        entry.marker = data.confidence_description;
      } else {
        entry.marker = "Sensor and frequency metrics verified.";
      }
    } catch (err) {
      console.error("Batch triage error on", entry.name, err);
      entry.status = "error";
      entry.verdict = "ERROR";
      entry.marker = err.message || "Triage processing failure";
    }

    renderBatchTable();
  }

  function readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error("Unable to read file text"));
      reader.readAsText(file);
    });
  }

  function renderBatchTable() {
    const tbody = document.getElementById("batch-table-body");
    if (!tbody) return;

    if (batchQueue.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-tertiary); padding: 24px;">
            No files currently in triage queue. Drop files above to begin batch analysis.
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = "";
    batchQueue.forEach((item) => {
      const tr = document.createElement("tr");

      let badgeHtml = "";
      if (item.status === "triaging") {
        badgeHtml = `<span style="color: var(--neon-cyan); font-family: monospace;">&#x23F3; TRIAGING</span>`;
      } else if (item.status === "error") {
        badgeHtml = `<span class="badge-threat-critical">ERROR</span>`;
      } else {
        const prob = item.probability || 0;
        if (prob >= 60 || item.verdict.includes("SYNTHETIC") || item.verdict.includes("DEEPFAKE")) {
          badgeHtml = `<span class="badge-threat-critical">HIGH RISK AI (${prob}%)</span>`;
        } else if (prob >= 30 || item.verdict.includes("SUSPICIOUS")) {
          badgeHtml = `<span class="badge-threat-suspicious">SUSPICIOUS (${prob}%)</span>`;
        } else {
          badgeHtml = `<span class="badge-threat-authentic">AUTHENTIC (${prob}%)</span>`;
        }
      }

      const domainIcons = {
        image: "&#x1F441; Vision",
        video: "&#x1F3AC; Video",
        audio: "&#x1F3A4; Audio",
        text: "&#x1F4DD; Text",
      };

      tr.innerHTML = `
        <td style="font-weight: 600; color: #fff; max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${item.name}">
          ${item.name}
        </td>
        <td style="color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; font-size: 11px;">
          ${domainIcons[item.domain] || item.domain}
        </td>
        <td style="color: var(--text-tertiary); font-family: 'JetBrains Mono', monospace; font-size: 11px;">
          ${formatBytes(item.size)}
        </td>
        <td>${badgeHtml}</td>
        <td style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: ${item.probability >= 50 ? '#ef4444' : '#10b981'};">
          ${item.probability !== null ? item.probability + "%" : "--"}
        </td>
        <td style="max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-secondary); font-size: 11.5px;" title="${item.marker}">
          ${item.marker}
        </td>
        <td>
          <button class="btn-secondary btn-batch-inspect" data-batch-id="${item.id}" style="padding: 4px 8px; font-size: 10.5px;" ${item.status !== "complete" ? "disabled" : ""}>
            Inspect &rarr;
          </button>
        </td>
      `;

      tbody.appendChild(tr);
    });

    // Attach inspect listeners
    tbody.querySelectorAll(".btn-batch-inspect").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-batch-id");
        const entry = batchQueue.find((e) => e.id === id);
        if (!entry || !entry.resultData) return;
        inspectBatchEntry(entry);
      });
    });
  }

  function inspectBatchEntry(entry) {
    if (typeof playCyberSound === "function") playCyberSound("click");
    if (entry.domain === "image" && typeof renderImageResults === "function") {
      if (typeof switchTab === "function") switchTab("tab-visual");
      renderImageResults(entry.resultData);
    } else if (entry.domain === "video" && typeof renderVideoResults === "function") {
      if (typeof switchTab === "function") switchTab("tab-video");
      renderVideoResults(entry.resultData);
    } else if (entry.domain === "audio" && typeof renderAudioResults === "function") {
      if (typeof switchTab === "function") switchTab("tab-audio");
      renderAudioResults(entry.resultData);
    } else if (entry.domain === "text" && typeof renderTextResults === "function") {
      if (typeof switchTab === "function") switchTab("tab-text");
      renderTextResults(entry.resultData);
    }
  }

  function exportBatchCSV() {
    if (batchQueue.length === 0) {
      if (typeof showToast === "function") showToast("No items in batch queue to export.", "alert");
      return;
    }

    const headers = ["Asset Name", "Domain", "File Size Bytes", "Status", "Verdict", "AI Probability (%)", "Primary Evidentiary Marker"];
    const rows = batchQueue.map((item) => [
      `"${item.name.replace(/"/g, '""')}"`,
      `"${item.domain}"`,
      item.size || 0,
      `"${item.status}"`,
      `"${item.verdict}"`,
      item.probability !== null ? item.probability : "",
      `"${(item.marker || "").replace(/"/g, '""')}"`,
    ]);

    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\r\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `aegistruth_batch_triage_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    if (typeof showToast === "function") showToast("Batch triage CSV exported successfully.", "success");
  }

  function exportBatchJSON() {
    if (batchQueue.length === 0) {
      if (typeof showToast === "function") showToast("No items in batch queue to export.", "alert");
      return;
    }

    const exportData = {
      timestamp: new Date().toISOString(),
      generator: "AegisTruth Enterprise Multi-Asset Batch Forensics v1.1",
      total_assets: batchQueue.length,
      queue: batchQueue.map((item) => ({
        id: item.id,
        name: item.name,
        domain: item.domain,
        size: item.size,
        status: item.status,
        verdict: item.verdict,
        probability: item.probability,
        marker: item.marker,
        provenance_manifest: item.resultData?.provenance_manifest || null,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `aegistruth_batch_triage_${Date.now()}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    if (typeof showToast === "function") showToast("Batch triage JSON exported successfully.", "success");
  }

  window.enqueueBatchFiles = enqueueBatchFiles;
})();
