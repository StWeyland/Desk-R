import { Router } from 'express';
import * as linkedin from '../platforms/linkedin.js';
import * as instagram from '../platforms/instagram.js';
import * as tiktok from '../platforms/tiktok.js';
import {
  getAccount,
  getAllAccounts,
  upsertPosts,
  getAllPosts,
  addCompetitor,
  getCompetitors,
  getCompetitor,
  removeCompetitor,
  addManualPost,
  getLastSyncLog,
} from '../db.js';
import { isPlatformConfigured } from '../config.js';
import { runAutomaticSync } from '../scheduler.js';

const router = Router();

const platformModules = { linkedin, instagram, tiktok };
// Nur Instagram bietet einen offiziellen, automatisierten Weg (Business Discovery),
// um oeffentliche Kennzahlen fremder Konten abzurufen. LinkedIn und TikTok stellen
// dafuer keine self-serve API bereit - automatisiertes Auslesen fremder Profile
// wuerde dort gegen die Nutzungsbedingungen verstossen. Deshalb laufen Wettbewerber
// auf diesen zwei Plattformen ausschliesslich als manuelles Tracking.
const COMPETITOR_TRACKING_MODE = { linkedin: 'manual', instagram: 'api', tiktok: 'manual' };

router.get('/status', (req, res) => {
  const accounts = getAllAccounts();
  const byPlatform = Object.fromEntries(accounts.map((a) => [a.platform, a]));
  const status = ['linkedin', 'instagram', 'tiktok'].map((platform) => ({
    platform,
    configured: isPlatformConfigured(platform),
    connected: Boolean(byPlatform[platform]),
    accountLabel: byPlatform[platform]?.account_label ?? null,
    connectedAt: byPlatform[platform]?.connected_at ?? null,
    competitorTrackingMode: COMPETITOR_TRACKING_MODE[platform],
  }));
  res.json({ status });
});

router.post('/sync/:platform', async (req, res) => {
  const { platform } = req.params;
  const mod = platformModules[platform];
  if (!mod) return res.status(400).json({ error: 'Unbekannte Plattform.' });

  const account = getAccount(platform);
  if (!account) return res.status(400).json({ error: `${platform} ist nicht verbunden.` });

  if (account.expires_at && account.expires_at < Date.now()) {
    return res.status(401).json({
      error: `Das ${platform}-Zugriffstoken ist abgelaufen. Bitte Konto erneut verbinden.`,
    });
  }

  try {
    const { posts, warning } = await mod.fetchPosts(account.access_token, account.meta);
    upsertPosts(platform, posts);
    res.json({ ok: true, count: posts.length, warning: warning ?? null });
  } catch (err) {
    res.status(502).json({ error: `Synchronisierung fehlgeschlagen: ${err.message}` });
  }
});

// Manueller Anstoss des gleichen Ablaufs, den der Zeitplan Mo/Mi/Fr automatisch
// ausfuehrt - praktisch zum Testen, ohne auf den naechsten Termin zu warten.
router.post('/sync-all', async (req, res) => {
  try {
    const results = await runAutomaticSync('manual');
    res.json({ ok: true, results });
  } catch (err) {
    res.status(500).json({ error: `Sync fehlgeschlagen: ${err.message}` });
  }
});

router.get('/sync-log', (req, res) => {
  res.json({ lastRun: getLastSyncLog() });
});

router.get('/posts', (req, res) => {
  const { platform, scope, owner } = req.query;
  res.json({ posts: getAllPosts({ platform: platform || undefined, scope: scope || undefined, ownerHandle: owner || undefined }) });
});

// --- Wettbewerber ---

router.get('/competitors', (req, res) => {
  res.json({ competitors: getCompetitors() });
});

router.post('/competitors', (req, res) => {
  const { platform, handle, label } = req.body || {};
  if (!platform || !handle) return res.status(400).json({ error: 'platform und handle sind Pflichtfelder.' });
  if (!platformModules[platform]) return res.status(400).json({ error: 'Unbekannte Plattform.' });

  const cleanHandle = String(handle).trim().replace(/^@/, '');
  const trackingMode = COMPETITOR_TRACKING_MODE[platform];
  const id = addCompetitor({ platform, handle: cleanHandle, label: label || cleanHandle, trackingMode });
  res.json({ ok: true, id, trackingMode });
});

router.delete('/competitors/:id', (req, res) => {
  const competitor = getCompetitor(req.params.id);
  if (!competitor) return res.status(404).json({ error: 'Wettbewerber nicht gefunden.' });
  removeCompetitor(req.params.id);
  res.json({ ok: true });
});

// Automatischer Sync - aktuell nur fuer Instagram (Business Discovery) verfuegbar.
router.post('/competitors/:id/sync', async (req, res) => {
  const competitor = getCompetitor(req.params.id);
  if (!competitor) return res.status(404).json({ error: 'Wettbewerber nicht gefunden.' });

  if (competitor.tracking_mode !== 'api') {
    return res.status(400).json({
      error: `${competitor.platform} hat keine offizielle API fuer fremde Konten. Traeg neue Zahlen fuer @${competitor.handle} manuell ein.`,
    });
  }
  if (competitor.platform !== 'instagram') {
    return res.status(400).json({ error: 'Automatischer Sync ist aktuell nur fuer Instagram implementiert.' });
  }

  const account = getAccount('instagram');
  if (!account) return res.status(400).json({ error: 'Verbinde zuerst dein eigenes Instagram-Konto - darueber laeuft die Wettbewerberabfrage.' });

  try {
    const { posts, warning, accountMeta } = await instagram.fetchCompetitorPosts(
      account.access_token,
      account.meta.igUserId,
      competitor.handle,
    );
    upsertPosts('instagram', posts, { ownerHandle: competitor.handle, source: 'api' });
    res.json({ ok: true, count: posts.length, warning: warning ?? null, accountMeta: accountMeta ?? null });
  } catch (err) {
    res.status(502).json({ error: `Synchronisierung fehlgeschlagen: ${err.message}` });
  }
});

// Manuelle Eintraege - fuer LinkedIn/TikTok-Wettbewerber (und optional als Ergaenzung
// bei Instagram), weil dort kein automatischer Fremdkonten-Abruf moeglich ist.
router.post('/competitors/:id/posts', (req, res) => {
  const competitor = getCompetitor(req.params.id);
  if (!competitor) return res.status(404).json({ error: 'Wettbewerber nicht gefunden.' });

  const { content, publishedAt, permalink, likes, comments, shares, views } = req.body || {};
  if (!content && !permalink) return res.status(400).json({ error: 'Bitte mindestens Inhalt oder Link angeben.' });

  addManualPost(competitor.platform, competitor.handle, {
    content,
    publishedAt: publishedAt ? new Date(publishedAt).getTime() : Date.now(),
    permalink,
    likes: Number(likes) || 0,
    comments: Number(comments) || 0,
    shares: Number(shares) || 0,
    views: Number(views) || 0,
  });
  res.json({ ok: true });
});

router.get('/analytics/summary', (req, res) => {
  const { scope } = req.query;
  const posts = getAllPosts({ scope: scope || undefined });
  const competitors = getCompetitors();
  res.json({ summary: buildSummary(posts, competitors) });
});

function buildSummary(posts, competitors) {
  const byPlatform = {};
  const hashtagCounts = new Map();
  const hourBuckets = Array.from({ length: 24 }, () => ({ count: 0, engagement: 0 }));
  const weekdayBuckets = Array.from({ length: 7 }, () => ({ count: 0, engagement: 0 }));
  const byOwnerKey = new Map();

  const labelFor = (platform, ownerHandle) => {
    if (!ownerHandle) return 'Du';
    const match = competitors.find((c) => c.platform === platform && c.handle === ownerHandle);
    return match?.label || `@${ownerHandle}`;
  };

  for (const post of posts) {
    const engagement = (post.likes || 0) + (post.comments || 0) + (post.shares || 0) + (post.saves || 0);

    if (!byPlatform[post.platform]) {
      byPlatform[post.platform] = { posts: 0, likes: 0, comments: 0, shares: 0, views: 0, saves: 0 };
    }
    const p = byPlatform[post.platform];
    p.posts += 1;
    p.likes += post.likes || 0;
    p.comments += post.comments || 0;
    p.shares += post.shares || 0;
    p.views += post.views || 0;
    p.saves += post.saves || 0;

    const ownerKey = `${post.platform}:${post.owner_handle || 'self'}`;
    if (!byOwnerKey.has(ownerKey)) {
      byOwnerKey.set(ownerKey, {
        platform: post.platform,
        ownerHandle: post.owner_handle || null,
        isOwn: !post.owner_handle,
        label: labelFor(post.platform, post.owner_handle),
        posts: 0,
        totalEngagement: 0,
      });
    }
    const ownerStats = byOwnerKey.get(ownerKey);
    ownerStats.posts += 1;
    ownerStats.totalEngagement += engagement;

    for (const tag of post.hashtags || []) {
      hashtagCounts.set(tag, (hashtagCounts.get(tag) || 0) + 1);
    }

    if (post.published_at) {
      const date = new Date(post.published_at);
      const hour = date.getHours();
      const weekday = date.getDay();
      hourBuckets[hour].count += 1;
      hourBuckets[hour].engagement += engagement;
      weekdayBuckets[weekday].count += 1;
      weekdayBuckets[weekday].engagement += engagement;
    }
  }

  const topPosts = [...posts]
    .map((post) => ({
      ...post,
      engagement: (post.likes || 0) + (post.comments || 0) + (post.shares || 0) + (post.saves || 0),
      ownerLabel: labelFor(post.platform, post.owner_handle),
    }))
    .sort((a, b) => b.engagement - a.engagement)
    .slice(0, 10);

  const topHashtags = [...hashtagCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([tag, count]) => ({ tag, count }));

  const comparison = [...byOwnerKey.values()]
    .map((o) => ({ ...o, avgEngagement: o.posts ? Math.round(o.totalEngagement / o.posts) : 0 }))
    .sort((a, b) => b.avgEngagement - a.avgEngagement);

  return {
    totalPosts: posts.length,
    byPlatform,
    topPosts,
    topHashtags,
    byHour: hourBuckets,
    byWeekday: weekdayBuckets,
    comparison,
  };
}

export default router;
