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
// topbar. Measuring it here instead of hardcoding a px value keeps the two
// in sync even as the topbar's real height changes (e.g. it wraps on narrow screens).
function syncTopbarHeightVar() {
  var topbar = document.querySelector('.app-topbar') || document.querySelector('.site-navbar');
  if (!topbar) return;
  document.documentElement.style.setProperty('--topbar-height', topbar.getBoundingClientRect().height + 'px');
}
document.addEventListener('DOMContentLoaded', syncTopbarHeightVar);
window.addEventListener('resize', syncTopbarHeightVar);

// Lets dashboard Chart.js configs read design-system.css's color tokens
// instead of hardcoding hex values that would drift from the palette.
window.chartColor = function (varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
};

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

// Top-of-page loading bar (see .page-progress in design-system.css) for
// full-page navigations and form submits. Every page here is a real
// server round trip rather than an SPA route change, so the bar just
// trickles toward 90% and is abandoned when the browser unloads the page
// for the next one — there is no "request finished" event to hook for a
// normal navigation, the incoming page's own fresh bar starts at 0% instead.
(function () {
  var bar = document.createElement('div');
  bar.className = 'page-progress';
  document.addEventListener('DOMContentLoaded', function () {
    document.body.appendChild(bar);
  });

  var trickleTimer = null;

  function startProgress() {
    clearInterval(trickleTimer);
    bar.classList.add('is-active');
    bar.style.width = '20%';
    var width = 20;
    trickleTimer = setInterval(function () {
      width += (90 - width) * 0.1;
      bar.style.width = width + '%';
    }, 300);
  }

  // Only reached if the page is restored from bfcache (e.g. the back
  // button) instead of a fresh load — resets a bar that may have been
  // left mid-trickle from before the user navigated away.
  function resetProgress() {
    clearInterval(trickleTimer);
    bar.classList.remove('is-active');
    bar.style.width = '0%';
  }

  function isPlainLeftClick(e) {
    return e.button === 0 && !e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey;
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link || !isPlainLeftClick(e)) return;
    if (link.target && link.target !== '_self') return;
    if (link.hasAttribute('download') || link.dataset.noProgress !== undefined) return;
    var href = link.getAttribute('href');
    if (!href || /^(#|javascript:|mailto:|tel:)/.test(href)) return;
    if (link.origin !== window.location.origin || link.href === window.location.href) return;
    startProgress();
  });

  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement) || form.dataset.noProgress !== undefined) return;
    startProgress();
  });

  window.addEventListener('pageshow', function (e) {
    if (e.persisted) resetProgress();
  });
})();
