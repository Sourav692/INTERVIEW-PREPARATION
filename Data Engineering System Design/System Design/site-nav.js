/**
 * Injects top bar + prev/next chapter footer into every chapter page.
 * Drop <script src="site-nav.js" defer></script> before </body>.
 */
(function () {
  'use strict';

  var CHAPTERS = [
    {
      num: '03',
      file: 'ch03_fundamentals_of_scale.html',
      title: 'Fundamentals of Scale'
    },
    {
      num: '04',
      file: 'ch04_storage_engines.html',
      title: 'Storage Engines'
    },
    {
      num: '05',
      file: 'ch05_data_modeling_at_scale.html',
      title: 'Data Modeling at Scale'
    },
    {
      num: '06',
      file: 'ch06_batch_systems.html',
      title: 'Batch Systems'
    },
    {
      num: '07',
      file: 'ch07_streaming_systems.html',
      title: 'Streaming Systems'
    },
    {
      num: '08',
      file: 'ch08_cdc_and_replication.html',
      title: 'CDC & Replication'
    },
    {
      num: '09',
      file: 'ch09_lakehouse_and_table_formats.html',
      title: 'Lakehouse & Table Formats'
    },
    {
      num: '10',
      file: 'ch10_query_engines.html',
      title: 'Query Engines'
    },
    {
      num: '11',
      file: 'ch11_orchestration.html',
      title: 'Orchestration'
    },
    {
      num: '12',
      file: 'ch12_data_contracts_and_governance.html',
      title: 'Data Contracts & Governance'
    },
    {
      num: '13',
      file: 'ch13_reliability_and_operations.html',
      title: 'Reliability & Operations'
    },
    {
      num: '14',
      file: 'ch14_cost_at_scale.html',
      title: 'Cost at Scale'
    },
    {
      num: '15',
      file: 'ch15_de_interview_playbook.html',
      title: 'The DE Interview Playbook'
    },
    {
      num: '16',
      file: 'ch16_case_studies.html',
      title: 'Case Studies'
    },
    {
      num: '16.1',
      file: 'ch16_case_study_1_fraud_detection.html',
      title: 'Fraud Detection'
    },
    {
      num: '16.2',
      file: 'ch16_case_study_2_recommendation_serving.html',
      title: 'Recommendation Serving'
    },
    {
      num: '16.3',
      file: 'ch16_case_study_3_clickstream_analytics.html',
      title: 'Clickstream Analytics'
    },
    {
      num: '16.4',
      file: 'ch16_case_study_4_iot_telemetry.html',
      title: 'IoT Telemetry'
    }
  ];

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
      '  background:rgba(14,17,22,0.92);',
      '  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);',
      '  border-bottom:1px solid var(--rule,#262e3a);',
      '  font-family:var(--mono,"IBM Plex Mono",Consolas,monospace);',
      '  font-size:12px;letter-spacing:0.06em;',
      '}',
      '.site-topnav a{color:var(--ink-dim,#8b96a5);text-decoration:none;}',
      '.site-topnav a:hover{color:var(--amber,#e8a33d);}',
      '.site-topnav a:focus-visible{outline:2px solid var(--amber,#e8a33d);outline-offset:3px;}',
      '.site-topnav-brand{color:var(--amber,#e8a33d) !important;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;font-size:11px;}',
      '.site-topnav-right{display:flex;align-items:center;gap:18px;flex-wrap:wrap;justify-content:flex-end;}',
      '.site-topnav-pos{color:var(--ink-faint,#5a6472);}',
      '.site-chapnav{',
      '  margin:72px 0 0;padding:28px 0 8px;',
      '  border-top:1px solid var(--rule,#262e3a);',
      '  display:grid;grid-template-columns:1fr 1fr;gap:16px;',
      '}',
      '.site-chapnav a{',
      '  display:block;padding:16px 18px;',
      '  background:var(--bg-panel,#151a22);',
      '  border:1px solid var(--rule,#262e3a);',
      '  border-radius:8px;',
      '  color:var(--ink,#dfe6ee);text-decoration:none;',
      '  transition:border-color 0.15s, background 0.15s;',
      '}',
      '.site-chapnav a:hover{border-color:var(--amber,#e8a33d);background:var(--bg-panel-raised,#1b212b);}',
      '.site-chapnav a:focus-visible{outline:2px solid var(--amber,#e8a33d);outline-offset:3px;}',
      '.site-chapnav .dir{',
      '  font-family:var(--mono,"IBM Plex Mono",Consolas,monospace);',
      '  font-size:11px;letter-spacing:0.12em;text-transform:uppercase;',
      '  color:var(--amber,#e8a33d);margin-bottom:6px;',
      '}',
      '.site-chapnav .name{',
      '  font-family:var(--serif,"Source Serif 4",Georgia,serif);',
      '  font-size:17px;font-weight:600;color:#fff;',
      '}',
      '.site-chapnav .next{text-align:right;}',
      '.site-chapnav .spacer{visibility:hidden;pointer-events:none;}',
      '.site-chapnav-home{',
      '  grid-column:1 / -1;text-align:center;padding-top:8px;',
      '  font-family:var(--mono,"IBM Plex Mono",Consolas,monospace);',
      '  font-size:12px;',
      '}',
      '.site-chapnav-home a{color:var(--ink-dim,#8b96a5);text-decoration:none;}',
      '.site-chapnav-home a:hover{color:var(--amber,#e8a33d);}',
      '@media(max-width:640px){',
      '  .site-topnav{padding:10px 16px;flex-wrap:wrap;}',
      '  .site-chapnav{grid-template-columns:1fr;}',
      '  .site-chapnav .next{text-align:left;}',
      '}',
      '@media (prefers-reduced-motion: reduce){',
      '  .site-chapnav a{transition:none;}',
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
    brand.href = 'index.html';
    brand.textContent = 'System Design for DEs';

    var right = document.createElement('div');
    right.className = 'site-topnav-right';

    var pos = document.createElement('span');
    pos.className = 'site-topnav-pos';
    pos.textContent = 'Ch.' + CHAPTERS[idx].num + ' · ' + (idx + 1) + '/' + CHAPTERS.length;

    var all = document.createElement('a');
    all.href = 'index.html#chapters';
    all.textContent = 'All chapters';

    var hub = document.createElement('a');
    hub.href = '../index.html';
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
      '<a href="index.html">← Table of contents</a>' +
      '<a href="../index.html" style="margin-left:14px">Study Hub</a>';
    wrap.appendChild(home);

    return wrap;
  }

  function init() {
    var idx = findIndex();
    if (idx < 0) return;

    injectStyles();

    var top = buildTopNav(idx);
    document.body.insertBefore(top, document.body.firstChild);

    var chapNav = buildChapNav(idx);
    var wrap = document.querySelector('.wrap');
    if (wrap) {
      wrap.appendChild(chapNav);
    } else {
      document.body.appendChild(chapNav);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
