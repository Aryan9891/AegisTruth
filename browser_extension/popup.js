document.addEventListener("DOMContentLoaded", () => {
  const verifyBtn = document.getElementById("verify-btn");
  const textInput = document.getElementById("text-input");
  const resultDiv = document.getElementById("result");
  const badge = document.getElementById("verdict-badge");
  const details = document.getElementById("details");

  verifyBtn.addEventListener("click", async () => {
    const text = textInput.value.trim();
    if (!text) return;

    verifyBtn.textContent = "Analyzing...";
    try {
      const res = await fetch("http://127.0.0.1:8000/api/forensics/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      if (!res.ok) throw new Error("Could not connect to AegisTruth local server.");
      const data = await res.json();

      resultDiv.style.display = "block";
      const isSynthetic = data.synthetic_probability > 50;
      badge.className = "badge " + (isSynthetic ? "synthetic" : "authentic");
      badge.textContent = `${data.verdict} (${data.synthetic_probability}% AI)`;

      details.innerHTML = `
        <strong>Burstiness:</strong> ${data.metrics.burstiness_index} | <strong>Entropy:</strong> ${data.metrics.shannon_entropy} bits<br>
        <span style="color: #94a3b8;">${data.confidence_description}</span>
      `;
    } catch (err) {
      resultDiv.style.display = "block";
      badge.className = "badge synthetic";
      badge.textContent = "CONNECTION ERROR";
      details.textContent = "Make sure AegisTruth local server is running at http://127.0.0.1:8000 (run: python run_server.py)";
    } finally {
      verifyBtn.textContent = "Verify Content Authenticity";
    }
  });
});

