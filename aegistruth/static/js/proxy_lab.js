// AegisTruth Universal Agent Firewall Proxy Lab

document.addEventListener("DOMContentLoaded", () => {
  const sendReqBtn = document.getElementById("btn-send-proxy-req");
  const refreshLogsBtn = document.getElementById("btn-refresh-proxy-logs");

  if (sendReqBtn) {
    sendReqBtn.addEventListener("click", testAgentProxyRequest);
  }

  if (refreshLogsBtn) {
    refreshLogsBtn.addEventListener("click", fetchProxyLogs);
  }

  // Load audit logs automatically when tab opens
  const proxyTab = document.querySelector('[data-tab="tab-proxy"]');
  if (proxyTab) {
    proxyTab.addEventListener("click", fetchProxyLogs);
  }
});

async function testAgentProxyRequest() {
  const prompt = document.getElementById("proxy-prompt-input").value.trim();
  const toolCommand = document.getElementById("proxy-tool-cmd").value.trim();
  const statusBox = document.getElementById("proxy-response-box");

  statusBox.style.display = "block";
  statusBox.innerHTML = "<span style='color: #38bdf8;'>&#x23F3; Intercepting request through AegisTruth Zero-Trust Gateway...</span>";

  try {
    const payload = {
      model: "aegistruth-sentinel-v1",
      messages: [
        { role: "user", content: prompt }
      ]
    };

    if (toolCommand) {
      payload.messages.push({
        role: "assistant",
        content: "Proposing execution:",
        tool_calls: [{
          id: "call_01",
          type: "function",
          function: {
            name: "bash",
            arguments: { command: toolCommand }
          }
        }]
      });
    }

    const res = await fetch("/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    const isBlocked = data.security_manifest && data.security_manifest.verdict === "BLOCKED";

    if (isBlocked) {
      if (typeof playCyberSound === "function") playCyberSound("alert");
      if (typeof showToast === "function") showToast("Zero-Trust Gateway Intercepted Destructive Payload!", "alert");
    } else {
      if (typeof playCyberSound === "function") playCyberSound("success");
      if (typeof showToast === "function") showToast("Gateway Forwarded Safe Request", "success");
    }

    statusBox.style.borderColor = isBlocked ? "#f43f5e" : "#10b981";
    statusBox.style.background = isBlocked ? "rgba(244, 63, 94, 0.08)" : "rgba(16, 185, 129, 0.08)";

    statusBox.innerHTML = `
      <div style="font-weight: bold; color: ${isBlocked ? '#f43f5e' : '#10b981'}; font-size: 15px; margin-bottom: 8px;">
        ${isBlocked ? '&#x2716; GATEWAY INTERCEPTED: EXECUTION BLOCKED' : '&#x2714; GATEWAY PASSED: SAFE TO EXECUTE'}
      </div>
      <div style="font-size: 13px; color: #cbd5e1; margin-bottom: 10px;">
        Finish Reason: <strong>${data.choices[0].finish_reason}</strong> | Threat Score: <strong>${data.security_manifest ? data.security_manifest.threat_score || 0 : 0} / 100</strong>
      </div>
      <div style="background: #090d16; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; color: #38bdf8;">
        ${data.choices[0].message.content}
      </div>
    `;

    // Refresh audit table
    await fetchProxyLogs();
  } catch (err) {
    statusBox.innerHTML = `<span style='color: #f43f5e;'>Error: ${err.message}</span>`;
  }
}

async function fetchProxyLogs() {
  try {
    const res = await fetch("/api/proxy/audit-logs");
    if (!res.ok) return;
    const data = await res.json();
    const tableBody = document.getElementById("proxy-logs-table-body");
    if (!tableBody) return;

    tableBody.innerHTML = "";
    if (data.logs.length === 0) {
      tableBody.innerHTML = "<tr><td colspan='5' style='padding: 14px; text-align: center; color: #94a3b8;'>No intercepted requests logged yet.</td></tr>";
      return;
    }

    data.logs.forEach(log => {
      const tr = document.createElement("tr");
      tr.style.borderBottom = "1px solid rgba(255,255,255,0.06)";
      const isBlocked = (log.status || "").includes("BLOCK");
      const statusColor = isBlocked ? "#f43f5e" : "#10b981";

      let timeStr = "";
      if (typeof log.timestamp === "number") {
        timeStr = new Date(log.timestamp * 1000).toLocaleTimeString();
      } else if (typeof log.timestamp === "string") {
        const d = new Date(log.timestamp);
        timeStr = isNaN(d.getTime()) ? log.timestamp : d.toLocaleTimeString();
      } else {
        timeStr = new Date().toLocaleTimeString();
      }

      const reqId = log.request_id || log.id || "aegis-unknown";
      const threatScore = (log.prompt_threat_score !== undefined)
        ? log.prompt_threat_score
        : (log.threat_score !== undefined ? log.threat_score : 0);
      const violations = (log.violations && log.violations.length > 0)
        ? log.violations.join(", ")
        : (log.reason || "None (Clean)");

      tr.innerHTML = `
        <td style="padding: 10px; font-family: monospace; font-size: 12px; color: #38bdf8;">${reqId}</td>
        <td style="padding: 10px; font-size: 12px; color: #cbd5e1;">${timeStr}</td>
        <td style="padding: 10px; font-size: 12px; font-weight: bold; color: ${statusColor};">${log.status}</td>
        <td style="padding: 10px; font-size: 12px; text-align: center;">${threatScore}/100</td>
        <td style="padding: 10px; font-size: 12px; color: #94a3b8;">${violations}</td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    console.warn("Could not fetch proxy logs:", err);
  }
}

