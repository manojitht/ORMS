// Auto-dismiss flash messages after a few seconds using Bootstrap's own Alert API (no jQuery needed).
document.addEventListener('DOMContentLoaded', function () {
  var alertEl = document.getElementById('message-alerts');
  if (alertEl && window.bootstrap) {
    setTimeout(function () {
      var alert = bootstrap.Alert.getOrCreateInstance(alertEl);
      if (alert) alert.close();
    }, 4000);
  }
});

// Legacy popup-panel toggles, still used by a handful of not-yet-converted
// pages (a #blur overlay + a specific panel id). Harmless no-ops if the
// referenced elements aren't present on the current page.
function toggle_blur() {
  var blur = document.getElementById('blur');
  if (blur) blur.classList.toggle('active');
  var request_popup = document.getElementById('request_popup');
  if (request_popup) request_popup.classList.toggle('active');
}

function toggle_accessories_blur() {
  var blur = document.getElementById('blur');
  if (blur) blur.classList.toggle('active');
  var other_popup = document.getElementById('other_accessories');
  if (other_popup) other_popup.classList.toggle('active');
}

function toggle_warning_blur() {
  var blur = document.getElementById('blur');
  if (blur) blur.classList.toggle('active');
  var warning_popup = document.getElementById('warning_popup');
  if (warning_popup) warning_popup.classList.toggle('active');
}
