// Render every <i data-lucide="..."> placeholder into a real inline SVG.
// Runs first (before the navbar-height measurement and toast-show below)
// since swapping icon elements can change layout height slightly, and
// everything after this assumes icons are already real SVGs.
document.addEventListener('DOMContentLoaded', function () {
  if (window.lucide) lucide.createIcons();
});

// Show every queued Django message as its own Bootstrap Toast. Toasts don't
// self-show — each needs an explicit .show() — and unlike the old single
// getElementById('message-alerts') lookup, this finds and shows *every*
// one, so a page with 2+ messages doesn't leave the extras stuck on screen.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.toast').forEach(function (el) {
    bootstrap.Toast.getOrCreateInstance(el).show();
  });
});

// The sticky table header (see design-system.css) needs to sit just below the sticky
// navbar. Measuring it here instead of hardcoding a px value keeps the two
// in sync even as the navbar's real height changes (e.g. it wraps to two
// lines on narrow screens).
function syncNavbarHeightVar() {
  var nav = document.querySelector('.site-navbar');
  if (!nav) return;
  document.documentElement.style.setProperty('--navbar-height', nav.getBoundingClientRect().height + 'px');
}
document.addEventListener('DOMContentLoaded', syncNavbarHeightVar);
window.addEventListener('resize', syncNavbarHeightVar);

// Disable the submit button and show a spinner on every form submission —
// stops accidental double-submits (e.g. double-clicking "Create User") as
// much as it looks better.
//
// The disable is deferred with setTimeout(0) rather than done inline: Safari
// cancels the pending form submission if the submit button becomes disabled
// synchronously inside its own 'submit' handler (the browser re-checks the
// button's disabled state before running the default action). Deferring by
// a tick lets the real submission proceed first in every browser, and still
// disables well before the page navigates away.
document.addEventListener('submit', function (e) {
  var form = e.target;
  if (!(form instanceof HTMLFormElement)) return;
  var btn = form.querySelector('button[type="submit"]');
  if (!btn || btn.disabled) return;
  setTimeout(function () {
    btn.dataset.originalHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Please wait…';
  }, 0);
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
