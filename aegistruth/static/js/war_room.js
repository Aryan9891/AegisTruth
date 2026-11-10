// AegisTruth Cyber SOC Tactical War Room Mode
// DEFCON-1 Red HUD with real-time heuristic radar pulses

(function () {
  let isWarRoomActive = false;

  document.addEventListener("DOMContentLoaded", () => {
    const warRoomBtn = document.getElementById("btn-header-war-room");
    const banner = document.getElementById("war-room-banner");

    if (warRoomBtn) {
      warRoomBtn.addEventListener("click", () => {
        isWarRoomActive = !isWarRoomActive;

        if (isWarRoomActive) {
          document.body.classList.add("war-room-mode");
          if (banner) banner.style.display = "block";
          warRoomBtn.innerHTML = "&#x26A0;&#xFE0F; Exit SOC";
          warRoomBtn.style.color = "#ff003c";
          warRoomBtn.style.borderColor = "#ff003c";

          if (typeof playCyberSound === "function") playCyberSound("alert");
          if (typeof showToast === "function") {
            showToast("DEFCON-1 Cyber SOC War Room Engaged. Maximum Sensitivity Mode Active.", "alert");
          }
        } else {
          document.body.classList.remove("war-room-mode");
          if (banner) banner.style.display = "none";
          warRoomBtn.innerHTML = "&#x1F6A8; SOC Mode";
          warRoomBtn.style.color = "";
          warRoomBtn.style.borderColor = "";

          if (typeof playCyberSound === "function") playCyberSound("click");
          if (typeof showToast === "function") {
            showToast("Exited SOC War Room mode. Standard Sentinel posture resumed.", "info");
          }
        }
      });
    }
  });

  window.toggleWarRoomMode = function (enable) {
    const btn = document.getElementById("btn-header-war-room");
    if (btn) btn.click();
  };
})();

