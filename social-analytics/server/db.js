import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.join(__dirname, '..', 'data');
fs.mkdirSync(dataDir, { recursive: true });

const db = new DatabaseSync(path.join(dataDir, 'social-analytics.sqlite'));

db.exec(`
  CREATE TABLE IF NOT EXISTS accounts (
    platform TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at INTEGER,
    account_label TEXT,
    meta TEXT,
    connected_at INTEGER NOT NULL
  );

  CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    published_at INTEGER,
    content TEXT,
    media_type TEXT,
    permalink TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    hashtags TEXT,
    raw TEXT,
    synced_at INTEGER NOT NULL
  );

  CREATE TABLE IF NOT EXISTS competitors (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    handle TEXT NOT NULL,
    label TEXT,
    tracking_mode TEXT NOT NULL,
    added_at INTEGER NOT NULL
  );

  CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at INTEGER NOT NULL,
    trigger_type TEXT NOT NULL,
    results TEXT NOT NULL
  );

  CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
  CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at);
`);

// Migration: aeltere Datenbanken hatten "posts" noch ohne diese Spalten.
const postColumns = db.prepare('PRAGMA table_info(posts)').all().map((c) => c.name);
if (!postColumns.includes('owner_handle')) {
  db.exec('ALTER TABLE posts ADD COLUMN owner_handle TEXT');
}
if (!postColumns.includes('source')) {
  db.exec("ALTER TABLE posts ADD COLUMN source TEXT DEFAULT 'api'");
}
db.exec('CREATE INDEX IF NOT EXISTS idx_posts_owner ON posts(platform, owner_handle)');

export function saveAccount({ platform, accessToken, refreshToken, expiresAt, accountLabel, meta }) {
  db.prepare(`
    INSERT INTO accounts (platform, access_token, refresh_token, expires_at, account_label, meta, connected_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(platform) DO UPDATE SET
      access_token = excluded.access_token,
      refresh_token = excluded.refresh_token,
      expires_at = excluded.expires_at,
      account_label = excluded.account_label,
      meta = excluded.meta,
      connected_at = excluded.connected_at
  `).run(platform, accessToken, refreshToken ?? null, expiresAt ?? null, accountLabel ?? null, JSON.stringify(meta ?? {}), Date.now());
}

export function getAccount(platform) {
  const row = db.prepare('SELECT * FROM accounts WHERE platform = ?').get(platform);
  if (!row) return null;
  return { ...row, meta: row.meta ? JSON.parse(row.meta) : {} };
}

export function getAllAccounts() {
  return db.prepare('SELECT * FROM accounts').all().map((row) => ({ ...row, meta: row.meta ? JSON.parse(row.meta) : {} }));
}

export function deleteAccount(platform) {
  db.prepare('DELETE FROM accounts WHERE platform = ?').run(platform);
}

// ownerHandle: null/undefined = eigener verbundener Account. Gesetzt = Wettbewerber-Handle.
// source: 'api' (automatisch abgerufen) oder 'manual' (von Hand eingetragen, z.B. LinkedIn/TikTok-Wettbewerber).
export function upsertPosts(platform, posts, { ownerHandle = null, source = 'api' } = {}) {
  const stmt = db.prepare(`
    INSERT INTO posts (id, platform, published_at, content, media_type, permalink, likes, comments, shares, views, saves, hashtags, raw, synced_at, owner_handle, source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      published_at = excluded.published_at,
      content = excluded.content,
      media_type = excluded.media_type,
      permalink = excluded.permalink,
      likes = excluded.likes,
      comments = excluded.comments,
      shares = excluded.shares,
      views = excluded.views,
      saves = excluded.saves,
      hashtags = excluded.hashtags,
      raw = excluded.raw,
      synced_at = excluded.synced_at,
      owner_handle = excluded.owner_handle,
      source = excluded.source
  `);
  const now = Date.now();
  const ownerKey = ownerHandle || 'self';
  for (const post of posts) {
    stmt.run(
      `${platform}:${ownerKey}:${post.externalId}`,
      platform,
      post.publishedAt ?? null,
      post.content ?? '',
      post.mediaType ?? null,
      post.permalink ?? null,
      post.likes ?? 0,
      post.comments ?? 0,
      post.shares ?? 0,
      post.views ?? 0,
      post.saves ?? 0,
      JSON.stringify(post.hashtags ?? []),
      JSON.stringify(post.raw ?? {}),
      now,
      ownerHandle ?? null,
      source,
    );
  }
}

export function addManualPost(platform, ownerHandle, post) {
  upsertPosts(
    platform,
    [
      {
        externalId: post.externalId || `manual-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        publishedAt: post.publishedAt ?? null,
        content: post.content ?? '',
        mediaType: post.mediaType ?? null,
        permalink: post.permalink ?? null,
        likes: post.likes ?? 0,
        comments: post.comments ?? 0,
        shares: post.shares ?? 0,
        views: post.views ?? 0,
        saves: post.saves ?? 0,
        hashtags: extractHashtags(post.content ?? ''),
        raw: {},
      },
    ],
    { ownerHandle, source: 'manual' },
  );
}

function extractHashtags(text) {
  return (text.match(/#[\p{L}0-9_]+/gu) || []).map((h) => h.toLowerCase());
}

export function deletePost(id) {
  db.prepare('DELETE FROM posts WHERE id = ?').run(id);
}

export function getAllPosts({ platform, ownerHandle, scope } = {}) {
  const clauses = [];
  const params = [];
  if (platform) {
    clauses.push('platform = ?');
    params.push(platform);
  }
  if (ownerHandle) {
    clauses.push('owner_handle = ?');
    params.push(ownerHandle);
  }
  if (scope === 'own') clauses.push('owner_handle IS NULL');
  if (scope === 'competitors') clauses.push('owner_handle IS NOT NULL');

  const where = clauses.length ? `WHERE ${clauses.join(' AND ')}` : '';
  const rows = db.prepare(`SELECT * FROM posts ${where} ORDER BY published_at DESC`).all(...params);
  return rows.map((row) => ({
    ...row,
    hashtags: row.hashtags ? JSON.parse(row.hashtags) : [],
    raw: row.raw ? JSON.parse(row.raw) : {},
  }));
}

// --- Wettbewerber ---
// trackingMode: 'api' (automatisch, aktuell nur Instagram Business Discovery)
//               oder 'manual' (LinkedIn/TikTok - Zahlen werden von Hand gepflegt).
export function addCompetitor({ platform, handle, label, trackingMode }) {
  const id = `${platform}:${handle}`;
  db.prepare(`
    INSERT INTO competitors (id, platform, handle, label, tracking_mode, added_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET label = excluded.label, tracking_mode = excluded.tracking_mode
  `).run(id, platform, handle, label ?? handle, trackingMode, Date.now());
  return id;
}

export function getCompetitors(platform) {
  const rows = platform
    ? db.prepare('SELECT * FROM competitors WHERE platform = ? ORDER BY added_at ASC').all(platform)
    : db.prepare('SELECT * FROM competitors ORDER BY added_at ASC').all();
  return rows;
}

export function getCompetitor(id) {
  return db.prepare('SELECT * FROM competitors WHERE id = ?').get(id) ?? null;
}

export function removeCompetitor(id) {
  const competitor = getCompetitor(id);
  db.prepare('DELETE FROM competitors WHERE id = ?').run(id);
  if (competitor) {
    db.prepare('DELETE FROM posts WHERE platform = ? AND owner_handle = ?').run(competitor.platform, competitor.handle);
  }
}

// --- Sync-Protokoll (fuer die automatischen Laeufe) ---

export function addSyncLog(triggerType, results) {
  db.prepare('INSERT INTO sync_log (run_at, trigger_type, results) VALUES (?, ?, ?)').run(
    Date.now(),
    triggerType,
    JSON.stringify(results),
  );
}

export function getLastSyncLog() {
  const row = db.prepare('SELECT * FROM sync_log ORDER BY run_at DESC LIMIT 1').get();
  if (!row) return null;
  return { ...row, results: JSON.parse(row.results) };
}

export default db;
