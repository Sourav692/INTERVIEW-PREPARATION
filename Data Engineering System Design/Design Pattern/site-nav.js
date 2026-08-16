/**
 * Injects top bar + prev/next chapter footer into Design Pattern pages.
 * Drop <script src="site-nav.js" defer></script> before </body>.
 */
(function () {
  'use strict';

  var CHAPTERS = [
    { num: '02', file: 'ch02_data_ingestion_design_patterns.html', title: 'Data Ingestion' },
    { num: '03', file: 'ch03_error_management_design_patterns.html', title: 'Error Management' },
    { num: '04', file: 'ch04_idempotency_design_patterns.html', title: 'Idempotency' },
    { num: '05', file: 'ch05_data_value_design_patterns.html', title: 'Data Value' },
    { num: '06', file: 'ch06_data_flow_design_patterns.html', title: 'Data Flow' },
    { num: '07', file: 'ch07_data_security_design_patterns.html', title: 'Data Security' },
    { num: '08', file: 'ch08_data_storage_design_patterns.html', title: 'Data Storage' },
    { num: '09', file: 'ch09_data_quality_design_patterns.html', title: 'Data Quality' },
    { num: '10', file: 'ch10_data_observability_design_patterns.html', title: 'Data Observability' }
  ];

  var HOME = 'index.html';
  var HUB = '../index.html';
  var ACCENT = 'var(--brass,#B8823C)';
  var ACCENT_FALLBACK = '#B8823C';

  function currentFile() {
    var path = window.location.pathname || '';
    var parts = path.split('/');
    return decodeURIComponent(parts[parts.length - 1] || '').toLowerCase();
  }

  function findIndex() {
    var file = currentFile();
    for (var i = 0; i < CHAPTERS.length; i++) {
      if (CHAPTERS[i].file.toLowerCase() === file) return i;
    }
    return -1;
  }

  function injectStyles() {
    if (document.getElementById('site-nav-styles')) return;
    var css = document.createElement('style');
    css.id = 'site-nav-styles';
    css.textContent = [
      '.site-topnav{',
      '  position:sticky;top:0;z-index:100;',
      '  display:flex;align-items:center;justify-content:space-between;gap:16px;',
      '  padding:10px 24px;min-height:48px;',
      '  background:rgba(27,36,48,0.94);',
      '  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);',
      '  border-bottom:2px solid ' + ACCENT_FALLBACK + ';',
      '  font-family:var(--mono,"JetBrains Mono",Consolas,monospace);',
      '  font-size:12px;letter-spacing:0.06em;',
      '}',
      '.site-topnav a{color:#C9C0B0;text-decoration:none;}',
      '.site-topnav a:hover{color:' + ACCENT_FALLBACK + ';}',
      '.site-topnav a:focus-visible{outline:2px solid ' + ACCENT_FALLBACK + ';outline-offset:3px;}',
      '.site-topnav-brand{color:' + ACCENT_FALLBACK + ' !important;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;font-size:11px;}',
      '.site-topnav-right{display:flex;align-items:center;gap:18px;flex-wrap:wrap;justify-content:flex-end;}',
      '.site-topnav-pos{color:#8A8378;}',
      '.site-chapnav{',
      '  margin:72px auto 0;padding:28px 24px 40px;max-width:920px;',
      '  border-top:1px solid var(--rule,#DAD2BE);',
      '  display:grid;grid-template-columns:1fr 1fr;gap:16px;',
      '}',
      '.site-chapnav a{',
      '  display:block;padding:16px 18px;',
      '  background:var(--page-raised,#FFFFFF);',
      '  border:1px solid var(--rule,#DAD2BE);',
      '  border-radius:8px;',
      '  color:var(--ink,#1B2430);text-decoration:none;',
      '  transition:border-color 0.15s, background 0.15s;',
      '}',
      '.site-chapnav a:hover{border-color:' + ACCENT_FALLBACK + ';}',
      '.site-chapnav a:focus-visible{outline:2px solid ' + ACCENT_FALLBACK + ';outline-offset:3px;}',
      '.site-chapnav .dir{',
      '  font-family:var(--mono,"JetBrains Mono",Consolas,monospace);',
      '  font-size:11px;letter-spacing:0.12em;text-transform:uppercase;',
      '  color:' + ACCENT + ';margin-bottom:6px;',
      '}',
      '.site-chapnav .name{',
      '  font-family:var(--serif,"Source Serif 4",Georgia,serif);',
      '  font-size:17px;font-weight:600;color:var(--ink,#1B2430);',
      '}',
      '.site-chapnav .next{text-align:right;}',
      '.site-chapnav .spacer{visibility:hidden;pointer-events:none;}',
      '.site-chapnav-home{',
      '  grid-column:1 / -1;text-align:center;padding-top:8px;',
      '  font-family:var(--mono,"JetBrains Mono",Consolas,monospace);',
      '  font-size:12px;',
      '}',
      '.site-chapnav-home a{color:var(--ink-soft,#3A4556);text-decoration:none;margin:0 10px;}',
      '.site-chapnav-home a:hover{color:' + ACCENT_FALLBACK + ';}',
      '@media(max-width:640px){',
      '  .site-topnav{padding:10px 16px;flex-wrap:wrap;}',
      '  .site-chapnav{grid-template-columns:1fr;}',
      '  .site-chapnav .next{text-align:left;}',
      '}'
    ].join('');
    document.head.appendChild(css);
  }

  function buildTopNav(idx) {
    var nav = document.createElement('nav');
    nav.className = 'site-topnav';
    nav.setAttribute('aria-label', 'Site');

    var brand = document.createElement('a');
    brand.className = 'site-topnav-brand';
    brand.href = HOME;
    brand.textContent = 'Design Patterns';

    var right = document.createElement('div');
    right.className = 'site-topnav-right';

    var pos = document.createElement('span');
    pos.className = 'site-topnav-pos';
    pos.textContent = 'Ch.' + CHAPTERS[idx].num + ' · ' + (idx + 1) + '/' + CHAPTERS.length;

    var all = document.createElement('a');
    all.href = HOME + '#chapters';
    all.textContent = 'All chapters';

    var hub = document.createElement('a');
    hub.href = HUB;
    hub.textContent = 'Study Hub';

    right.appendChild(pos);
    right.appendChild(all);
    right.appendChild(hub);
    nav.appendChild(brand);
    nav.appendChild(right);
    return nav;
  }

  function buildChapNav(idx) {
    var wrap = document.createElement('nav');
    wrap.className = 'site-chapnav';
    wrap.setAttribute('aria-label', 'Chapter navigation');

    var prev = CHAPTERS[idx - 1];
    var next = CHAPTERS[idx + 1];

    if (prev) {
      var prevLink = document.createElement('a');
      prevLink.href = prev.file;
      prevLink.innerHTML =
        '<div class="dir">← Previous</div><div class="name">Ch.' +
        prev.num +
        ' — ' +
        prev.title +
        '</div>';
      wrap.appendChild(prevLink);
    } else {
      var spacer = document.createElement('div');
      spacer.className = 'spacer';
      spacer.setAttribute('aria-hidden', 'true');
      wrap.appendChild(spacer);
    }

    if (next) {
      var nextLink = document.createElement('a');
      nextLink.className = 'next';
      nextLink.href = next.file;
      nextLink.innerHTML =
        '<div class="dir">Next →</div><div class="name">Ch.' +
        next.num +
        ' — ' +
        next.title +
        '</div>';
      wrap.appendChild(nextLink);
    } else {
      var spacer2 = document.createElement('div');
      spacer2.className = 'spacer';
      spacer2.setAttribute('aria-hidden', 'true');
      wrap.appendChild(spacer2);
    }

    var home = document.createElement('div');
    home.className = 'site-chapnav-home';
    home.innerHTML =
      '<a href="' +
      HOME +
      '">← Pattern chapters</a>' +
      '<a href="' +
      HUB +
      '">Study Hub</a>';
    wrap.appendChild(home);

    return wrap;
  }

  function init() {
    var idx = findIndex();
    if (idx < 0) return;

    injectStyles();
    document.body.insertBefore(buildTopNav(idx), document.body.firstChild);

    var chapNav = buildChapNav(idx);
    var host =
      document.querySelector('.wrap') ||
      document.querySelector('main') ||
      document.body;
    host.appendChild(chapNav);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
