const PLATFORM_LABELS = { linkedin: 'LinkedIn', instagram: 'Instagram', tiktok: 'TikTok' };
let charts = {};
let currentScope = '';

async function loadStatus() {
  const res = await fetch('/api/status');
  const { status } = await res.json();
  renderAccountCards(status);
  return status;
}

function renderAccountCards(status) {
  const container = document.getElementById('accountCards');
  container.innerHTML = '';
  for (const s of status) {
    const card = document.createElement('div');
    card.className = 'account-card';

    const title = document.createElement('div');
    title.className = 'platform-name';
    title.innerHTML = `<span class="dot ${s.connected ? 'connected' : ''}"></span>${PLATFORM_LABELS[s.platform]}`;
    card.appendChild(title);

    const statusText = document.createElement('div');
    statusText.className = 'status-text';
    if (!s.configured) {
      statusText.textContent = 'Nicht konfiguriert (.env pruefen)';
    } else if (s.connected) {
      statusText.textContent = `Verbunden als ${s.accountLabel ?? 'Konto'}`;
    } else {
      statusText.textContent = 'Nicht verbunden';
    }
    card.appendChild(statusText);

    const row = document.createElement('div');
    row.className = 'btn-row';

    if (s.connected) {
      const syncBtn = document.createElement('button');
      syncBtn.className = 'btn';
      syncBtn.textContent = 'Synchronisieren';
      syncBtn.onclick = () => syncPlatform(s.platform, syncBtn);
      row.appendChild(syncBtn);

      const disconnectBtn = document.createElement('button');
      disconnectBtn.className = 'btn danger';
      disconnectBtn.textContent = 'Trennen';
      disconnectBtn.onclick = () => disconnectPlatform(s.platform);
      row.appendChild(disconnectBtn);
    } else {
      const connectBtn = document.createElement('a');
      connectBtn.className = 'btn';
      connectBtn.href = `/auth/${s.platform}`;
      connectBtn.textContent = 'Verbinden';
      if (!s.configured) connectBtn.setAttribute('disabled', 'true');
      row.appendChild(connectBtn);
    }
    card.appendChild(row);

    const warningSlot = document.createElement('div');
    warningSlot.id = `warning-${s.platform}`;
    card.appendChild(warningSlot);

    container.appendChild(card);
  }
}

async function syncPlatform(platform, btn) {
  btn.disabled = true;
  btn.textContent = 'Wird synchronisiert...';
  try {
    const res = await fetch(`/api/sync/${platform}`, { method: 'POST' });
    const data = await res.json();
    showAccountWarning(platform, data.warning || data.error);
    await loadSummary();
  } catch (err) {
    alert(`Sync fehlgeschlagen: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Synchronisieren';
    document.getElementById('lastSync').textContent = `Letzte Synchronisierung: ${new Date().toLocaleString('de-DE')}`;
  }
}

function showAccountWarning(platform, message) {
  const slot = document.getElementById(`warning-${platform}`);
  if (!slot) return;
  slot.innerHTML = message ? `<div class="warning">${escapeHtml(message)}</div>` : '';
}

async function disconnectPlatform(platform) {
  if (!confirm(`${PLATFORM_LABELS[platform]}-Konto wirklich trennen?`)) return;
  await fetch(`/auth/disconnect/${platform}`, { method: 'POST' });
  await loadStatus();
}

// --- Wettbewerber ---

let competitorTrackingModes = { linkedin: 'manual', instagram: 'api', tiktok: 'manual' };

async function loadCompetitors() {
  const res = await fetch('/api/competitors');
  const { competitors } = await res.json();
  renderCompetitors(competitors);
}

function renderCompetitors(competitors) {
  const container = document.getElementById('competitorList');
  if (!competitors.length) {
    container.innerHTML = '<div class="muted">Noch keine Wettbewerber hinterlegt.</div>';
    return;
  }
  container.innerHTML = '';
  for (const c of competitors) {
    const row = document.createElement('div');
    row.className = 'competitor-row';

    const info = document.createElement('div');
    info.className = 'info';
    info.innerHTML = `
      <span class="name">${escapeHtml(c.label)} <span class="mode-tag">${PLATFORM_LABELS[c.platform]}</span></span>
      <span class="muted">@${escapeHtml(c.handle)} - ${c.tracking_mode === 'api' ? 'automatischer Abruf' : 'manuelles Tracking'}</span>
    `;
    row.appendChild(info);

    const actions = document.createElement('div');
    actions.className = 'btn-row';

    if (c.tracking_mode === 'api') {
      const syncBtn = document.createElement('button');
      syncBtn.className = 'btn';
      syncBtn.textContent = 'Abrufen';
      syncBtn.onclick = async () => {
        syncBtn.disabled = true;
        syncBtn.textContent = 'Wird abgerufen...';
        const res = await fetch(`/api/competitors/${encodeURIComponent(c.id)}/sync`, { method: 'POST' });
        const data = await res.json();
        if (data.error) alert(data.error);
        else if (data.warning) alert(data.warning);
        syncBtn.disabled = false;
        syncBtn.textContent = 'Abrufen';
        await loadSummary();
      };
      actions.appendChild(syncBtn);
    } else {
      const addPostBtn = document.createElement('button');
      addPostBtn.className = 'btn secondary';
      addPostBtn.textContent = 'Beitrag manuell hinzufuegen';
      addPostBtn.onclick = () => {
        const form = row.querySelector('.manual-entry-form');
        form.classList.toggle('open');
      };
      actions.appendChild(addPostBtn);
    }

    const removeBtn = document.createElement('button');
    removeBtn.className = 'btn danger';
    removeBtn.textContent = 'Entfernen';
    removeBtn.onclick = async () => {
      if (!confirm(`${c.label} wirklich entfernen? Alle gespeicherten Beitraege dazu werden geloescht.`)) return;
      await fetch(`/api/competitors/${encodeURIComponent(c.id)}`, { method: 'DELETE' });
      await loadCompetitors();
      await loadSummary();
    };
    actions.appendChild(removeBtn);
    row.appendChild(actions);

    if (c.tracking_mode === 'manual') {
      const form = document.createElement('form');
      form.className = 'manual-entry-form';
      form.innerHTML = `
        <input type="text" name="content" placeholder="Beitragstext / Beschreibung" />
        <input type="url" name="permalink" placeholder="Link zum Beitrag" />
        <input type="date" name="publishedAt" />
        <input type="number" name="likes" placeholder="Likes" min="0" />
        <input type="number" name="comments" placeholder="Kommentare" min="0" />
        <input type="number" name="shares" placeholder="Shares" min="0" />
        <input type="number" name="views" placeholder="Views" min="0" />
        <button type="submit" class="btn">Speichern</button>
      `;
      form.onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const body = Object.fromEntries(fd.entries());
        const res = await fetch(`/api/competitors/${encodeURIComponent(c.id)}/posts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const data = await res.json();
        if (data.error) {
          alert(data.error);
          return;
        }
        form.reset();
        form.classList.remove('open');
        await loadSummary();
      };
      row.appendChild(form);
    }

    container.appendChild(row);
  }
}

function initCompetitorForm() {
  const form = document.getElementById('addCompetitorForm');
  form.onsubmit = async (e) => {
    e.preventDefault();
    const platform = document.getElementById('competitorPlatform').value;
    const handle = document.getElementById('competitorHandle').value.trim();
    const label = document.getElementById('competitorLabel').value.trim();
    if (!handle) return;
    const res = await fetch('/api/competitors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, handle, label }),
    });
    const data = await res.json();
    if (data.error) {
      alert(data.error);
      return;
    }
    form.reset();
    await loadCompetitors();
  };
}

// --- Analytics ---

async function loadSummary() {
  const res = await fetch(`/api/analytics/summary${currentScope ? `?scope=${currentScope}` : ''}`);
  const { summary } = await res.json();
  renderSummaryCards(summary);
  renderHourChart(summary.byHour);
  renderWeekdayChart(summary.byWeekday);
  renderPlatformChart(summary.byPlatform);
  renderComparisonChart(summary.comparison);
  renderHashtags(summary.topHashtags);
  renderTopPosts(summary.topPosts);
}

function renderSummaryCards(summary) {
  const totalEngagement = Object.values(summary.byPlatform).reduce(
    (sum, p) => sum + p.likes + p.comments + p.shares + p.saves,
    0,
  );
  const cards = [
    { label: 'Beitraege gesamt', value: summary.totalPosts },
    { label: 'Engagement gesamt', value: totalEngagement },
    { label: 'Getrackte Konten', value: summary.comparison.length },
  ];
  const container = document.getElementById('summaryCards');
  container.innerHTML = cards
    .map((c) => `<div class="card"><div class="value">${c.value}</div><div class="label">${c.label}</div></div>`)
    .join('');
}

function renderHourChart(byHour) {
  const ctx = document.getElementById('hourChart');
  charts.hour?.destroy();
  charts.hour = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: byHour.map((_, h) => `${h}:00`),
      datasets: [{ label: 'Engagement', data: byHour.map((b) => b.engagement), backgroundColor: '#a8743a' }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderWeekdayChart(byWeekday) {
  const labels = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  const ctx = document.getElementById('weekdayChart');
  charts.weekday?.destroy();
  charts.weekday = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ label: 'Engagement', data: byWeekday.map((b) => b.engagement), backgroundColor: '#c1387e' }],
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
  });
}

function renderPlatformChart(byPlatform) {
  const platforms = Object.keys(byPlatform);
  const ctx = document.getElementById('platformChart');
  charts.platform?.destroy();
  charts.platform = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: platforms.map((p) => PLATFORM_LABELS[p] ?? p),
      datasets: [
        { label: 'Likes', data: platforms.map((p) => byPlatform[p].likes), backgroundColor: '#a8743a' },
        { label: 'Kommentare', data: platforms.map((p) => byPlatform[p].comments), backgroundColor: '#0a66c2' },
        { label: 'Shares', data: platforms.map((p) => byPlatform[p].shares), backgroundColor: '#c1387e' },
      ],
    },
    options: { scales: { y: { beginAtZero: true } } },
  });
}

function renderComparisonChart(comparison) {
  const ctx = document.getElementById('comparisonChart');
  charts.comparison?.destroy();
  if (!comparison.length) {
    charts.comparison = null;
    return;
  }
  charts.comparison = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: comparison.map((c) => `${c.label} (${PLATFORM_LABELS[c.platform] ?? c.platform})`),
      datasets: [
        {
          label: 'Durchschnittliches Engagement / Beitrag',
          data: comparison.map((c) => c.avgEngagement),
          backgroundColor: comparison.map((c) => (c.isOwn ? '#a8743a' : '#6b6b6b')),
        },
      ],
    },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true } },
    },
  });
}

function renderHashtags(topHashtags) {
  const container = document.getElementById('hashtagList');
  if (!topHashtags.length) {
    container.innerHTML = '<div class="muted">Noch keine Hashtag-Daten vorhanden.</div>';
    return;
  }
  container.innerHTML = topHashtags
    .map((h) => `<span class="tag">${escapeHtml(h.tag)}<span class="count">${h.count}</span></span>`)
    .join('');
}

function renderTopPosts(topPosts) {
  const tbody = document.querySelector('#topPostsTable tbody');
  tbody.innerHTML = topPosts
    .map((post) => {
      const date = post.published_at ? new Date(post.published_at).toLocaleDateString('de-DE') : '-';
      const content = (post.content || '').slice(0, 80);
      const link = post.permalink
        ? `<a href="${escapeHtml(post.permalink)}" target="_blank" rel="noopener">${escapeHtml(content)}</a>`
        : escapeHtml(content);
      const ownerPillClass = post.owner_handle ? 'competitor' : 'own';
      return `<tr>
        <td><span class="pill ${post.platform}">${PLATFORM_LABELS[post.platform] ?? post.platform}</span></td>
        <td><span class="pill ${ownerPillClass}">${escapeHtml(post.ownerLabel || 'Du')}</span></td>
        <td class="content">${link}</td>
        <td>${date}</td>
        <td>${post.likes}</td>
        <td>${post.comments}</td>
        <td>${post.shares}</td>
        <td>${post.views}</td>
        <td><strong>${post.engagement}</strong></td>
      </tr>`;
    })
    .join('');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

function initScopeFilter() {
  const select = document.getElementById('scopeFilter');
  select.onchange = () => {
    currentScope = select.value;
    loadSummary();
  };
}

function init() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('connected')) {
    window.history.replaceState({}, '', '/');
  }
  initCompetitorForm();
  initScopeFilter();
  loadStatus();
  loadCompetitors();
  loadSummary();
}

init();
