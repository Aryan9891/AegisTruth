// AegisTruth Studio Main Application Controller

document.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  checkSystemHealth();
});

function initNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetId = tab.getAttribute("data-tab");

      tabs.forEach(t => t.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));

      tab.classList.add("active");
      const targetContent = document.getElementById(targetId);
      if (targetContent) {
        targetContent.classList.add("active");
      }
    });
  });
}

async function checkSystemHealth() {
  try {
    const res = await fetch("/api/report/health");
    if (res.ok) {
      const data = await res.json();
      console.log("[*] AegisTruth Engine Status:", data);
      const pill = document.getElementById("system-status-text");
      if (pill) {
        pill.textContent = `SYSTEM ONLINE v${data.version}`;
      }
    }
  } catch (err) {
    console.warn("Could not connect to health endpoint:", err);
  }
}

