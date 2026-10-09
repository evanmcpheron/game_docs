'use strict';
(function () {
  const edition = document.body.dataset.edition;
  const themeButton = document.getElementById('theme-toggle');
  let storedTheme = null;
  try { storedTheme = localStorage.getItem('rpg-manual-theme'); } catch (_) { /* Reading still works without storage. */ }
  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    if (themeButton) {
      themeButton.setAttribute('aria-pressed', String(theme === 'dark'));
      themeButton.textContent = theme === 'dark' ? 'Light theme' : 'Dark theme';
    }
  }
  applyTheme(storedTheme === 'dark' ? 'dark' : 'light');
  if (themeButton) themeButton.addEventListener('click', function () {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    applyTheme(theme);
    try { localStorage.setItem('rpg-manual-theme', theme); } catch (_) { /* Theme remains active in this page. */ }
  });

  const assetTable = document.getElementById('asset-table');
  if (assetTable) {
    const filter = document.getElementById('asset-filter');
    const category = document.getElementById('asset-category');
    const count = document.getElementById('asset-count');
    const tbody = assetTable.tBodies[0];
    let sortKey = 'phase';
    let ascending = true;
    function refreshAssets() {
      const query = filter.value.trim().toLowerCase();
      const rows = Array.from(tbody.rows);
      rows.sort(function (first, second) {
        const left = sortKey === 'phase' ? Number(first.dataset.phase) : first.dataset[sortKey];
        const right = sortKey === 'phase' ? Number(second.dataset.phase) : second.dataset[sortKey];
        const result = typeof left === 'number' ? left - right : left.localeCompare(right);
        return (ascending ? result : -result) || first.dataset.id.localeCompare(second.dataset.id);
      });
      let visible = 0;
      rows.forEach(function (row) {
        row.hidden = !(row.textContent.toLowerCase().includes(query) && (!category.value || row.dataset.category === category.value));
        if (!row.hidden) visible += 1;
        tbody.appendChild(row);
      });
      count.textContent = visible + ' of ' + rows.length + ' planned assets shown.';
    }
    filter.addEventListener('input', refreshAssets);
    category.addEventListener('change', refreshAssets);
    assetTable.querySelectorAll('[data-sort]').forEach(function (button) {
      button.addEventListener('click', function () {
        ascending = sortKey === button.dataset.sort ? !ascending : true;
        sortKey = button.dataset.sort;
        assetTable.querySelectorAll('th').forEach(function (header) { header.removeAttribute('aria-sort'); });
        button.parentElement.setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
        refreshAssets();
      });
    });
    refreshAssets();
  }

  const searchForm = document.getElementById('search-form');
  if (searchForm) {
    const queryInput = document.getElementById('search-query');
    const resultsElement = document.getElementById('search-results');
    const status = document.getElementById('search-status');
    function search() {
      const query = queryInput.value.trim().toLowerCase();
      resultsElement.replaceChildren();
      if (!query) { status.textContent = 'Enter a term. All search data is local.'; return; }
      const terms = query.split(/\s+/).filter(Boolean);
      const matches = (window.RPG_SEARCH_DATA || []).map(function (record) {
        const combined = (record.title + ' ' + record.text).toLowerCase();
        if (!terms.every(function (term) { return combined.includes(term); })) return null;
        return { record: record, score: terms.reduce(function (score, term) { return score + (record.title.toLowerCase().includes(term) ? 10 : 1); }, 0) };
      }).filter(Boolean).sort(function (first, second) { return second.score - first.score || first.record.title.localeCompare(second.record.title); });
      status.textContent = matches.length + ' matching pages. Showing ' + Math.min(matches.length, 100) + '.';
      matches.slice(0, 100).forEach(function (match) {
        const record = match.record;
        const article = document.createElement('article'); article.className = 'search-result';
        const heading = document.createElement('h2');
        const link = document.createElement('a'); link.href = record.path; link.textContent = record.title;
        heading.appendChild(link); article.appendChild(heading);
        const group = document.createElement('small'); group.textContent = record.group + ' · ' + record.path; article.appendChild(group);
        const position = record.text.toLowerCase().indexOf(terms[0]);
        const start = Math.max(0, position - 80);
        const excerpt = document.createElement('p'); excerpt.textContent = (start ? '… ' : '') + record.text.slice(start, start + 280) + ' …';
        article.appendChild(excerpt); resultsElement.appendChild(article);
      });
    }
    searchForm.addEventListener('submit', function (event) { event.preventDefault(); search(); });
    queryInput.addEventListener('input', search);
    const initialQuery = new URLSearchParams(location.search).get('q');
    if (initialQuery) { queryInput.value = initialQuery; search(); }
  }

  const progressControls = Array.from(document.querySelectorAll('[data-progress-id]'));
  if (progressControls.length) {
    const storageKey = 'rpg-mmo-manual-progress-v1';
    const status = document.getElementById('progress-status');
    const validIds = new Set(progressControls.map(function (control) { return control.dataset.progressId; }));
    let progress = {};
    function validateProgress(value) {
      if (!value || value.schemaVersion !== 1 || typeof value.progress !== 'object' || value.progress === null || Array.isArray(value.progress)) throw new Error('Unsupported progress file. Expected schemaVersion 1 and a progress object.');
      const cleaned = {};
      Object.entries(value.progress).forEach(function (entry) {
        if (!validIds.has(entry[0]) || typeof entry[1] !== 'boolean') throw new Error('Unknown checklist ID or non-boolean completion value.');
        cleaned[entry[0]] = entry[1];
      });
      return cleaned;
    }
    function snapshot() { return { schemaVersion: 1, edition: edition, exportedAt: new Date().toISOString(), progress: progress }; }
    function display(message) {
      progressControls.forEach(function (control) { control.checked = progress[control.dataset.progressId] === true; });
      const completed = progressControls.filter(function (control) { return control.checked; }).length;
      status.textContent = (message ? message + ' ' : '') + completed + ' of ' + progressControls.length + ' steps checked. These are your records, not engine test evidence.';
    }
    function persist() {
      try { localStorage.setItem(storageKey, JSON.stringify(snapshot())); display(); }
      catch (_) { display('Local storage is unavailable; export before closing this page.'); }
    }
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) progress = validateProgress(JSON.parse(stored));
      display();
    } catch (_) { display('Saved progress could not be read. Import a valid export or start a new local record.'); }
    progressControls.forEach(function (control) {
      control.addEventListener('change', function () { progress[control.dataset.progressId] = control.checked; persist(); });
    });
    document.getElementById('progress-export').addEventListener('click', function () {
      const blob = new Blob([JSON.stringify(snapshot(), null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob); const link = document.createElement('a');
      link.href = url; link.download = 'RPG_MMO_Progress.json'; document.body.appendChild(link); link.click(); link.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      display('Progress export created.');
    });
    document.getElementById('progress-import').addEventListener('change', async function (event) {
      const file = event.target.files[0]; if (!file) return;
      try {
        if (file.size > 1024 * 1024) throw new Error('Progress file exceeds the 1MB safety limit.');
        const imported = validateProgress(JSON.parse(await file.text()));
        progress = imported; persist(); display('Progress imported.');
      } catch (error) { display('Import rejected: ' + error.message); }
      event.target.value = '';
    });
    document.getElementById('progress-reset').addEventListener('click', function () {
      if (!window.confirm('Reset all local progress? Export a copy first to preserve it.')) return;
      progress = {}; persist(); display('Local progress reset.');
    });
  }
})();
