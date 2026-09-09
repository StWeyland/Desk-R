import { Router } from 'express';
import * as linkedin from '../platforms/linkedin.js';
import * as instagram from '../platforms/instagram.js';
import * as tiktok from '../platforms/tiktok.js';
import { getAccount, getAllAccounts, upsertPosts, getAllPosts } from '../db.js';
import { isPlatformConfigured } from '../config.js';

const router = Router();

const platformModules = { linkedin, instagram, tiktok };

router.get('/status', (req, res) => {
  const accounts = getAllAccounts();
  const byPlatform = Object.fromEntries(accounts.map((a) => [a.platform, a]));
  const status = ['linkedin', 'instagram', 'tiktok'].map((platform) => ({
    platform,
    configured: isPlatformConfigured(platform),
    connected: Boolean(byPlatform[platform]),
    accountLabel: byPlatform[platform]?.account_label ?? null,
    connectedAt: byPlatform[platform]?.connected_at ?? null,
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

router.get('/posts', (req, res) => {
  const { platform } = req.query;
  res.json({ posts: getAllPosts({ platform: platform || undefined }) });
});

router.get('/analytics/summary', (req, res) => {
  const posts = getAllPosts();
  res.json({ summary: buildSummary(posts) });
});

function buildSummary(posts) {
  const byPlatform = {};
  const hashtagCounts = new Map();
  const hourBuckets = Array.from({ length: 24 }, () => ({ count: 0, engagement: 0 }));
  const weekdayBuckets = Array.from({ length: 7 }, () => ({ count: 0, engagement: 0 }));

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
    }))
    .sort((a, b) => b.engagement - a.engagement)
    .slice(0, 10);

  const topHashtags = [...hashtagCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([tag, count]) => ({ tag, count }));

  return {
    totalPosts: posts.length,
    byPlatform,
    topPosts,
    topHashtags,
    byHour: hourBuckets,
    byWeekday: weekdayBuckets,
  };
}

export default router;
