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

// Notification bell: unread-count polling + fetch-the-panel-on-open + mark-
// read UX. window.NOTIF_URLS is only set (see base.html) when logged in.
// The interval poll is the one genuinely new client-side idiom here --
// the panel fetch reuses the same fetch-a-rendered-partial pattern already
// used for the cascading-dropdown fields elsewhere in this app, and every
// notification row is a plain full-page-nav <a>, not a JS click handler.
if (window.NOTIF_URLS) {
  (function () {
    var badge = document.querySelector('[data-notif-badge]');
    var toggle = document.querySelector('[data-notif-toggle]');
    var panel = document.querySelector('[data-notif-panel]');
    if (!badge || !toggle || !panel) return;

    function getCookie(name) {
      var match = document.cookie.match('(^|;\\s*)' + name + '=([^;]*)');
      return match ? decodeURIComponent(match[2]) : null;
    }

    function setBadge(count) {
      if (count > 0) {
        badge.textContent = count > 99 ? '99+' : String(count);
        badge.classList.remove('d-none');
      } else {
        badge.classList.add('d-none');
      }
    }

    function refreshCount() {
      fetch(window.NOTIF_URLS.unreadCount)
        .then(function (r) { return r.json(); })
        .then(function (data) { setBadge(data.count); })
        .catch(function () {});
    }

    function loadPanel() {
      panel.innerHTML = '<div class="app-notif-panel__loading">Loading...</div>';
      fetch(window.NOTIF_URLS.panel)
        .then(function (r) { return r.text(); })
        .then(function (html) {
          panel.innerHTML = html;
          if (window.lucide) lucide.createIcons();
        })
        .catch(function () {
          panel.innerHTML = '<div class="app-notif-panel__loading">Couldn\'t load notifications.</div>';
        });
    }

    var dropdownParent = toggle.closest('.dropdown');
    if (dropdownParent) dropdownParent.addEventListener('show.bs.dropdown', loadPanel);

    // "Mark all read" and the notification rows only exist after loadPanel()
    // has injected them, so both are delegated from the static panel element.
    panel.addEventListener('click', function (e) {
      var markAllBtn = e.target.closest('[data-mark-all-read-url]');
      if (markAllBtn) {
        e.preventDefault();
        fetch(markAllBtn.dataset.markAllReadUrl, {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') },
        }).then(function () {
          setBadge(0);
          panel.querySelectorAll('.app-notif-row--unread').forEach(function (row) {
            row.classList.remove('app-notif-row--unread');
          });
          markAllBtn.remove();
        }).catch(function () {});
        return;
      }

      // Optimistic decrement before the row's own full-page navigation fires.
      var row = e.target.closest('.app-notif-row--unread');
      if (row) {
        var current = parseInt(badge.textContent, 10);
        if (!isNaN(current) && current > 0) setBadge(current - 1);
      }
    });

    refreshCount();
    setInterval(function () {
      if (document.visibilityState === 'visible') refreshCount();
    }, 45000);
  })();
}

// Dark mode toggle. A full reload after flipping the attribute is
// deliberate, not an oversight: this app has no live-rerender path, and it's
// the only way the dashboards' Chart.js canvases (which read colors via
// getComputedStyle once, at draw time) repaint with the new theme's colors.
// Every other element updates instantly via CSS and would be fine without
// it, but the charts wouldn't -- so every toggle reloads, for consistency.
document.addEventListener('click', function (e) {
  var toggle = e.target.closest('[data-theme-toggle]');
  if (!toggle) return;
  var current = document.documentElement.getAttribute('data-bs-theme');
  var next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem('sukhraTheme', next);
  document.documentElement.setAttribute('data-bs-theme', next);
  location.reload();
});
