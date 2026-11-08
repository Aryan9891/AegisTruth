// AegisTruth Textual Forensics & Fact Verification Lab

document.addEventListener("DOMContentLoaded", () => {
  const analyzeTextBtn = document.getElementById("btn-analyze-text");
  const factCheckBtn = document.getElementById("btn-fact-check");
  const sampleHumanBtn = document.getElementById("btn-sample-text-human");
  const sampleAiBtn = document.getElementById("btn-sample-text-ai");
  const sampleContraBtn = document.getElementById("btn-sample-text-contra");
  const textarea = document.getElementById("text-input");

  if (sampleHumanBtn) {
    sampleHumanBtn.addEventListener("click", () => {
      textarea.value = "Honestly, we never expected the results to look like this. After three weeks of sleepless nights debugging the network stack, the latency finally plummeted. It wasn't clean code by any stretch—more like a duct-tape miracle. But tomorrow morning, we ship it anyway, whatever happens.";
    });
  }

  if (sampleAiBtn) {
    sampleAiBtn.addEventListener("click", () => {
      textarea.value = "In today's fast-paced digital world, it is crucial to remember that technology serves as a beacon of progress. Furthermore, it is worth noting that modern artificial intelligence plays a pivotal role across industries. By navigating the complexities of computational innovation, we can seamlessly integrate these multifaceted solutions. In summary, this groundbreaking paradigm stands as a testament to human ingenuity and continuous evolution.";
    });
  }

  if (sampleContraBtn) {
    sampleContraBtn.addEventListener("click", () => {
      textarea.value = "During the fiscal year 2024, renewable energy investments increased by 45% nationwide. The expansion created thousands of regional jobs. However, nationwide renewable energy investments decreased significantly over the same fiscal period, declining to record lows. Abraham Lincoln celebrated these technological developments by sending an email to the governors.";
    });
  }

  if (analyzeTextBtn) {
    analyzeTextBtn.addEventListener("click", runTextForensics);
  }

  if (factCheckBtn) {
    factCheckBtn.addEventListener("click", runFactChecking);
  }
});

async function runTextForensics() {
  const text = document.getElementById("text-input").value.trim();
  if (text.length < 20) {
    alert("Please enter at least 20 characters of text to evaluate.");
    return;
  }

  setLoadingState("text-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
  try {
    const res = await fetch("/api/forensics/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analysis request failed");
    }

    const data = await res.json();
    renderTextResults(data);
  } catch (err) {
    alert("Text analysis error: " + err.message);
  } finally {
    setLoadingState("text-loading", false);
  }
}

async function runFactChecking() {
  const text = document.getElementById("text-input").value.trim();
  if (text.length < 20) {
    alert("Please enter at least 20 characters of text to evaluate.");
    return;
  }

  setLoadingState("text-loading", true);
  if (typeof playCyberSound === "function") playCyberSound("scan");
  try {
    const res = await fetch("/api/forensics/text/fact-check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Fact checking failed");
    }

    const data = await res.json();
    renderFactResults(data);
  } catch (err) {
    alert("Fact check error: " + err.message);
  } finally {
    setLoadingState("text-loading", false);
  }
}

function renderTextResults(data) {
  document.getElementById("text-results-panel").style.display = "block";
  document.getElementById("fact-results-panel").style.display = "none";

  if (data.verdict === "LIKELY_HUMAN") {
    if (typeof playCyberSound === "function") playCyberSound("success");
    if (typeof showToast === "function") showToast("Text evaluated: Natural Human Prose", "success");
  } else {
    if (typeof playCyberSound === "function") playCyberSound("alert");
    if (typeof showToast === "function") showToast(`Synthetic Text Detected: ${data.verdict}`, "alert");
  }

  // Score & Verdict
  const verdictEl = document.getElementById("text-verdict-badge");
  verdictEl.className = "badge-verdict";
  if (data.verdict === "LIKELY_HUMAN") {
    verdictEl.classList.add("badge-authentic");
    verdictEl.innerHTML = `&#x2714; ${data.verdict} (${data.synthetic_probability}% AI)`;
  } else if (data.verdict === "MIXED_OR_EDITED") {
    verdictEl.classList.add("badge-suspicious");
    verdictEl.innerHTML = `&#x26A0; ${data.verdict} (${data.synthetic_probability}% AI)`;
  } else {
    verdictEl.classList.add("badge-synthetic");
    verdictEl.innerHTML = `&#x2716; ${data.verdict} (${data.synthetic_probability}% AI)`;
  }

  document.getElementById("text-verdict-desc").textContent = data.confidence_description;

  // Metrics
  document.getElementById("metric-text-burstiness").textContent = data.metrics.burstiness_index;
  document.getElementById("metric-text-entropy").textContent = data.metrics.shannon_entropy + " bits";
  document.getElementById("metric-text-ttr").textContent = data.metrics.lexical_ttr;
  document.getElementById("metric-text-cliches").textContent = data.metrics.cliche_count;

  // Evidentiary Reasons
  const reasonsList = document.getElementById("text-reasons-list");
  reasonsList.innerHTML = "";
  if (data.forensic_reasons && data.forensic_reasons.length > 0) {
    data.forensic_reasons.forEach(r => {
      const li = document.createElement("li");
      li.textContent = r;
      reasonsList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "Text possesses natural human sentence cadence, irregular punctuation, and diverse vocabulary.";
    reasonsList.appendChild(li);
  }

  // Sentence Heatmap
  const heatContainer = document.getElementById("sentence-heatmap-container");
  heatContainer.innerHTML = "";
  data.sentence_breakdown.forEach(s => {
    const div = document.createElement("div");
    div.className = `sentence-item tag-${s.tag}`;
    div.innerHTML = `<strong>[${s.tag}]</strong> ${s.text} <span style="font-size:11px;color:#94a3b8;margin-left:8px;">(${s.word_count} words | Suspicion: ${s.suspicion_score}%)</span>`;
    heatContainer.appendChild(div);
  });

  window.currentTextManifest = data.provenance_manifest;
}

function renderFactResults(data) {
  document.getElementById("text-results-panel").style.display = "none";
  document.getElementById("fact-results-panel").style.display = "block";

  document.getElementById("fact-score-val").textContent = `${data.overall_factuality_score} / 100`;
  document.getElementById("fact-claims-count").textContent = data.total_claims_extracted;
  document.getElementById("fact-verified-count").textContent = data.verified_grounded_count;

  // Render Claims Matrix
  const tableBody = document.getElementById("fact-claims-table-body");
  tableBody.innerHTML = "";

  data.claims.forEach(c => {
    const tr = document.createElement("tr");
    tr.style.borderBottom = "1px solid rgba(255,255,255,0.06)";
    
    let color = "#94a3b8";
    if (c.status === "GROUNDED_VERIFIED") color = "#10b981";
    else if (c.status === "HIGH_RISK_HALLUCINATION") color = "#f43f5e";
    else if (c.status === "POTENTIAL_OVERSTATEMENT") color = "#f59e0b";

    tr.innerHTML = `
      <td style="padding: 10px; color: #fff; font-size: 13px;">${c.claim}</td>
      <td style="padding: 10px; font-size: 12px; color: ${color}; font-weight: bold;">${c.status}</td>
      <td style="padding: 10px; font-size: 12px; color: #cbd5e1;">${c.evidence}</td>
      <td style="padding: 10px; font-size: 12px; text-align: center;">${c.credibility_score}%</td>
    `;
    tableBody.appendChild(tr);
  });
}

