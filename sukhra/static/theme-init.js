// Sets data-bs-theme on <html> before the page paints, so a saved dark-mode
// preference never flashes light-then-dark on load. Must run synchronously,
// early in <head> -- not deferred, not in script.js (which loads at the end
// of <body>, long after first paint).
(function () {
  var saved = localStorage.getItem('sukhraTheme');
  var theme = saved || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-bs-theme', theme);
})();
