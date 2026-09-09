import { config } from '../config.js';

const GRAPH_VERSION = 'v21.0';
const AUTH_URL = `https://www.facebook.com/${GRAPH_VERSION}/dialog/oauth`;
const TOKEN_URL = `https://graph.facebook.com/${GRAPH_VERSION}/oauth/access_token`;
const GRAPH_URL = `https://graph.facebook.com/${GRAPH_VERSION}`;

// Self-serve fuer eigene Konten: Instagram-Business/Creator-Konto muss mit einer
// Facebook-Seite verknuepft sein, und du musst dich selbst im App-Dashboard unter
// "App-Rollen -> Tester" hinzufuegen. Dann funktionieren diese Scopes ohne App-Review.
const SCOPES = ['instagram_basic', 'instagram_manage_insights', 'pages_show_list', 'pages_read_engagement'];

export const platform = 'instagram';

export function getAuthUrl(state) {
  const params = new URLSearchParams({
    client_id: config.instagram.appId,
    redirect_uri: `${config.baseUrl}/auth/instagram/callback`,
    state,
    scope: SCOPES.join(','),
    response_type: 'code',
  });
  return `${AUTH_URL}?${params.toString()}`;
}

export async function exchangeCode(code) {
  const params = new URLSearchParams({
    client_id: config.instagram.appId,
    client_secret: config.instagram.appSecret,
    redirect_uri: `${config.baseUrl}/auth/instagram/callback`,
    code,
  });
  const res = await fetch(`${TOKEN_URL}?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`Instagram Token-Austausch fehlgeschlagen: ${res.status} ${await res.text()}`);
  }
  const shortLived = await res.json();

  const longLivedParams = new URLSearchParams({
    grant_type: 'fb_exchange_token',
    client_id: config.instagram.appId,
    client_secret: config.instagram.appSecret,
    fb_exchange_token: shortLived.access_token,
  });
  const longLivedRes = await fetch(`${TOKEN_URL}?${longLivedParams.toString()}`);
  const longLived = longLivedRes.ok ? await longLivedRes.json() : shortLived;

  const igAccount = await findInstagramBusinessAccount(longLived.access_token);

  return {
    accessToken: longLived.access_token,
    refreshToken: null,
    expiresAt: Date.now() + (longLived.expires_in ?? 60 * 24 * 3600) * 1000,
    accountLabel: igAccount?.username ? `@${igAccount.username}` : 'Instagram-Konto',
    meta: { igUserId: igAccount?.id ?? null, username: igAccount?.username ?? null },
  };
}

async function findInstagramBusinessAccount(accessToken) {
  const pagesRes = await fetch(
    `${GRAPH_URL}/me/accounts?fields=id,name,instagram_business_account{id,username}&access_token=${accessToken}`,
  );
  if (!pagesRes.ok) return null;
  const pagesData = await pagesRes.json();
  const pageWithIg = (pagesData.data ?? []).find((p) => p.instagram_business_account);
  return pageWithIg?.instagram_business_account ?? null;
}

export async function fetchPosts(accessToken, meta) {
  if (!meta?.igUserId) {
    return {
      posts: [],
      warning:
        'Kein Instagram-Business/Creator-Konto gefunden. Verknuepfe dein Instagram-Konto ' +
        'im Facebook-Business-Manager mit einer Facebook-Seite und stelle es auf ' +
        '"Business" oder "Creator" um - siehe README.md, Abschnitt Instagram.',
    };
  }

  const fields = 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count';
  const res = await fetch(`${GRAPH_URL}/${meta.igUserId}/media?fields=${fields}&access_token=${accessToken}&limit=50`);
  if (!res.ok) {
    return { posts: [], warning: `Instagram-API-Fehler: ${res.status} ${await res.text()}` };
  }
  const data = await res.json();
  const items = data.data ?? [];

  const posts = await Promise.all(items.map((item) => normalizePost(item, accessToken)));
  return { posts, warning: null };
}

async function normalizePost(item, accessToken) {
  const insights = await fetchInsights(item.id, item.media_type, accessToken);
  const caption = item.caption || '';
  return {
    externalId: item.id,
    publishedAt: item.timestamp ? new Date(item.timestamp).getTime() : null,
    content: caption,
    mediaType: item.media_type,
    permalink: item.permalink,
    likes: item.like_count ?? 0,
    comments: item.comments_count ?? 0,
    shares: insights.shares ?? 0,
    views: insights.views ?? 0,
    saves: insights.saved ?? 0,
    hashtags: extractHashtags(caption),
    raw: item,
  };
}

async function fetchInsights(mediaId, mediaType, accessToken) {
  const metricsByType = {
    IMAGE: 'impressions,reach,saved',
    CAROUSEL_ALBUM: 'impressions,reach,saved',
    VIDEO: 'impressions,reach,saved,video_views',
    REELS: 'plays,reach,saved,shares,comments,likes',
  };
  const metric = metricsByType[mediaType] || 'impressions,reach';
  try {
    const res = await fetch(`${GRAPH_URL}/${mediaId}/insights?metric=${metric}&access_token=${accessToken}`);
    if (!res.ok) return {};
    const data = await res.json();
    const out = {};
    for (const entry of data.data ?? []) {
      const value = entry.values?.[0]?.value ?? 0;
      if (entry.name === 'saved') out.saved = value;
      if (entry.name === 'shares') out.shares = value;
      if (entry.name === 'video_views' || entry.name === 'plays') out.views = value;
      if (entry.name === 'reach' && out.views === undefined) out.views = value;
    }
    return out;
  } catch {
    return {};
  }
}

function extractHashtags(text) {
  return (text.match(/#[\p{L}0-9_]+/gu) || []).map((h) => h.toLowerCase());
}
