const PLATFORM_LABELS = { linkedin: 'LinkedIn', instagram: 'Instagram', tiktok: 'TikTok' };
let charts = {};

async function loadStatus() {
  const res = await fetch('/api/status');
  const { status } = await res.json();
  renderAccountCards(status);
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
    const warningSlot = document.getElementById(`warning-${platform}`);
    if (data.warning) {
      warningSlot.innerHTML = `<div class="warning">${escapeHtml(data.warning)}</div>`;
    } else if (data.error) {
      warningSlot.innerHTML = `<div class="warning">${escapeHtml(data.error)}</div>`;
    } else {
      warningSlot.innerHTML = '';
    }
    await loadSummary();
  } catch (err) {
    alert(`Sync fehlgeschlagen: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Synchronisieren';
    document.getElementById('lastSync').textContent = `Letzte Synchronisierung: ${new Date().toLocaleString('de-DE')}`;
  }
}

async function disconnectPlatform(platform) {
  if (!confirm(`${PLATFORM_LABELS[platform]}-Konto wirklich trennen?`)) return;
  await fetch(`/auth/disconnect/${platform}`, { method: 'POST' });
  await loadStatus();
}

async function loadSummary() {
  const res = await fetch('/api/analytics/summary');
  const { summary } = await res.json();
  renderSummaryCards(summary);
  renderHourChart(summary.byHour);
  renderWeekdayChart(summary.byWeekday);
  renderPlatformChart(summary.byPlatform);
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
    { label: 'Plattformen aktiv', value: Object.keys(summary.byPlatform).length },
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
      return `<tr>
        <td><span class="pill ${post.platform}">${PLATFORM_LABELS[post.platform] ?? post.platform}</span></td>
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

function init() {
  const params = new URLSearchParams(window.location.search);
  if (params.get('connected')) {
    window.history.replaceState({}, '', '/');
  }
  loadStatus();
  loadSummary();
}

init();
