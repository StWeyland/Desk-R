import crypto from 'node:crypto';
import { config } from '../config.js';

const AUTH_URL = 'https://www.tiktok.com/v2/auth/authorize/';
const TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/';
const VIDEO_LIST_URL = 'https://open.tiktokapis.com/v2/video/list/';

// Self-serve fuer das eigene Konto: App im TikTok-Developer-Portal anlegen, Produkte
// "Login Kit" und "Display API" hinzufuegen und dein eigenes Konto unter
// "Sandbox -> Target Users" als Tester eintragen. Dann funktioniert dieser Flow
// ohne separate Business-Freigabe.
const SCOPES = ['user.info.basic', 'video.list'];

export const platform = 'tiktok';

export function generatePkce() {
  const verifier = crypto.randomBytes(32).toString('hex');
  const challenge = crypto.createHash('sha256').update(verifier).digest('hex');
  return { verifier, challenge };
}

export function getAuthUrl(state, codeChallenge) {
  const params = new URLSearchParams({
    client_key: config.tiktok.clientKey,
    response_type: 'code',
    scope: SCOPES.join(','),
    redirect_uri: `${config.baseUrl}/auth/tiktok/callback`,
    state,
    code_challenge: codeChallenge,
    code_challenge_method: 'S256',
  });
  return `${AUTH_URL}?${params.toString()}`;
}

export async function exchangeCode(code, codeVerifier) {
  const params = new URLSearchParams({
    client_key: config.tiktok.clientKey,
    client_secret: config.tiktok.clientSecret,
    code,
    grant_type: 'authorization_code',
    redirect_uri: `${config.baseUrl}/auth/tiktok/callback`,
    code_verifier: codeVerifier,
  });

  const res = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'Cache-Control': 'no-cache' },
    body: params.toString(),
  });
  if (!res.ok) {
    throw new Error(`TikTok Token-Austausch fehlgeschlagen: ${res.status} ${await res.text()}`);
  }
  const data = await res.json();

  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token ?? null,
    expiresAt: Date.now() + (data.expires_in ?? 0) * 1000,
    accountLabel: `TikTok-Konto (${data.open_id ?? 'unbekannt'})`,
    meta: { openId: data.open_id },
  };
}

export async function fetchPosts(accessToken) {
  const fields = [
    'id',
    'video_description',
    'create_time',
    'share_url',
    'view_count',
    'like_count',
    'comment_count',
    'share_count',
  ].join(',');

  const res = await fetch(`${VIDEO_LIST_URL}?fields=${fields}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ max_count: 20 }),
  });

  if (!res.ok) {
    return { posts: [], warning: `TikTok-API-Fehler: ${res.status} ${await res.text()}` };
  }
  const data = await res.json();
  if (data.error && data.error.code !== 'ok') {
    return { posts: [], warning: `TikTok-API-Fehler: ${data.error.code} - ${data.error.message}` };
  }
  const videos = data.data?.videos ?? [];
  const posts = videos.map(normalizePost);
  return { posts, warning: null };
}

function normalizePost(video) {
  const description = video.video_description || '';
  return {
    externalId: video.id,
    publishedAt: video.create_time ? video.create_time * 1000 : null,
    content: description,
    mediaType: 'video',
    permalink: video.share_url,
    likes: video.like_count ?? 0,
    comments: video.comment_count ?? 0,
    shares: video.share_count ?? 0,
    views: video.view_count ?? 0,
    saves: 0,
    hashtags: extractHashtags(description),
    raw: video,
  };
}

function extractHashtags(text) {
  return (text.match(/#[\p{L}0-9_]+/gu) || []).map((h) => h.toLowerCase());
}
