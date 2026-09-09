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

  CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
  CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at);
`);

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

export function upsertPosts(platform, posts) {
  const stmt = db.prepare(`
    INSERT INTO posts (id, platform, published_at, content, media_type, permalink, likes, comments, shares, views, saves, hashtags, raw, synced_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
      synced_at = excluded.synced_at
  `);
  const now = Date.now();
  for (const post of posts) {
    stmt.run(
      `${platform}:${post.externalId}`,
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
    );
  }
}

export function getAllPosts({ platform } = {}) {
  const rows = platform
    ? db.prepare('SELECT * FROM posts WHERE platform = ? ORDER BY published_at DESC').all(platform)
    : db.prepare('SELECT * FROM posts ORDER BY published_at DESC').all();
  return rows.map((row) => ({
    ...row,
    hashtags: row.hashtags ? JSON.parse(row.hashtags) : [],
    raw: row.raw ? JSON.parse(row.raw) : {},
  }));
}

export default db;
