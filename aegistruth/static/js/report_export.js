// AegisTruth Cryptographic Provenance & Audit Report Export

document.addEventListener("DOMContentLoaded", () => {
  const exportBtn = document.getElementById("btn-export-certificate");
  const viewManifestBtn = document.getElementById("btn-view-manifest");

  if (exportBtn) {
    exportBtn.addEventListener("click", downloadHtmlCertificate);
  }

  if (viewManifestBtn) {
    viewManifestBtn.addEventListener("click", displayActiveManifest);
  }
});

function getActiveManifest() {
  return window.currentImageManifest || window.currentAudioManifest || window.currentTextManifest || null;
}

function displayActiveManifest() {
  const manifest = getActiveManifest();
  const pre = document.getElementById("manifest-json-display");
  if (!manifest) {
    pre.textContent = "No analysis has been run yet. Analyze an image, audio file, or text to generate a cryptographic manifest.";
    return;
  }
  pre.textContent = JSON.stringify(manifest, null, 2);
}

async function downloadHtmlCertificate() {
  const manifest = getActiveManifest();
  if (!manifest) {
    alert("Please perform an analysis first before generating an audit certificate.");
    return;
  }

  try {
    const res = await fetch("/api/report/export-html", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ manifest }),
    });

    if (!res.ok) throw new Error("Could not generate certificate");
    const htmlText = await res.text();

    // Open in new tab or download
    const blob = new Blob([htmlText], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const win = window.open(url, "_blank");
    if (!win) {
      // If popup blocker intervened, trigger download
      const a = document.createElement("a");
      a.href = url;
      a.download = `AegisTruth-Certificate-${manifest.manifest_signature.substring(0, 8)}.html`;
      a.click();
    }
  } catch (err) {
    alert("Failed to export certificate: " + err.message);
  }
}
