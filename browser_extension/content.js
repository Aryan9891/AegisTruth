// AegisTruth Browser Content Script
// Adds quick verification tooltips to selected text

document.addEventListener("mouseup", () => {
  const selection = window.getSelection().toString().trim();
  if (selection.length > 30 && selection.length < 1000) {
    // Show a small subtle AegisTruth badge if not already shown
    let icon = document.getElementById("aegistruth-floating-icon");
    if (!icon) {
      icon = document.createElement("div");
      icon.id = "aegistruth-floating-icon";
      icon.innerHTML = "&#x1F6E1;";
      icon.title = "Verify selected text with AegisTruth";
      icon.style.cssText = "position: absolute; z-index: 999999; cursor: pointer; background: #0f172a; border: 1px solid #38bdf8; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.5);";
      document.body.appendChild(icon);

      icon.addEventListener("click", async (e) => {
        e.stopPropagation();
        icon.innerHTML = "&#x23F3;";
        try {
          const res = await fetch("http://127.0.0.1:8000/api/forensics/text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: selection })
          });
          const data = await res.json();
          alert(`[AegisTruth Sentinel]\nVerdict: ${data.verdict}\nAI Probability: ${data.synthetic_probability}%\nBurstiness: ${data.metrics.burstiness_index}\nDescription: ${data.confidence_description}`);
        } catch (err) {
          alert("AegisTruth server not detected at http://127.0.0.1:8000. Start it via 'python run_server.py'");
        } finally {
          icon.innerHTML = "&#x1F6E1;";
        }
      });
    }

    const oRect = window.getSelection().getRangeAt(0).getBoundingClientRect();
    icon.style.top = `${window.scrollY + oRect.top - 34}px`;
    icon.style.left = `${window.scrollX + oRect.right - 10}px`;
    icon.style.display = "flex";
  } else {
    const icon = document.getElementById("aegistruth-floating-icon");
    if (icon) icon.style.display = "none";
  }
});

