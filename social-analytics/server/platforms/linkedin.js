import { config } from '../config.js';

const AUTH_URL = 'https://www.linkedin.com/oauth/v2/authorization';
const TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken';
const USERINFO_URL = 'https://api.linkedin.com/v2/userinfo';
const POSTS_URL = 'https://api.linkedin.com/rest/posts';
const LINKEDIN_API_VERSION = '202405';

// Self-serve scopes ("Sign In with LinkedIn using OpenID Connect" + "Share on LinkedIn").
// Diese zwei Produkte kann man im LinkedIn-App-Dashboard sofort ohne Pruefung aktivieren.
const SCOPES = ['openid', 'profile', 'email', 'w_member_social'];

export const platform = 'linkedin';

export function getAuthUrl(state) {
  const params = new URLSearchParams({
    response_type: 'code',
    client_id: config.linkedin.clientId,
    redirect_uri: `${config.baseUrl}/auth/linkedin/callback`,
    state,
    scope: SCOPES.join(' '),
  });
  return `${AUTH_URL}?${params.toString()}`;
}

export async function exchangeCode(code) {
  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: `${config.baseUrl}/auth/linkedin/callback`,
    client_id: config.linkedin.clientId,
    client_secret: config.linkedin.clientSecret,
  });

  const res = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
  if (!res.ok) {
    throw new Error(`LinkedIn Token-Austausch fehlgeschlagen: ${res.status} ${await res.text()}`);
  }
  const data = await res.json();

  const profileRes = await fetch(USERINFO_URL, {
    headers: { Authorization: `Bearer ${data.access_token}` },
  });
  const profile = profileRes.ok ? await profileRes.json() : {};

  return {
    accessToken: data.access_token,
    refreshToken: data.refresh_token ?? null,
    expiresAt: Date.now() + (data.expires_in ?? 0) * 1000,
    accountLabel: profile.name || profile.email || 'LinkedIn-Konto',
    meta: { sub: profile.sub, name: profile.name, email: profile.email },
  };
}

// LinkedIn erlaubt das Lesen eigener Post-Kennzahlen (Likes/Kommentare/Impressions)
// nur ueber die Community Management API bzw. Marketing Developer Platform, die
// LinkedIn erst nach manueller Pruefung deines Unternehmensprofils frei schaltet.
// Mit den self-serve Scopes oben bekommen wir nur die Liste der eigenen Beitraege,
// nicht deren Engagement-Zahlen. Wir versuchen den Aufruf trotzdem und liefern bei
// fehlender Berechtigung eine klare, verstaendliche Fehlermeldung statt eines Absturzes.
export async function fetchPosts(accessToken, meta) {
  if (!meta?.sub) {
    return { posts: [], warning: 'Kein LinkedIn-Profil verknuepft.' };
  }
  const author = `urn:li:person:${meta.sub}`;
  const params = new URLSearchParams({ q: 'author', author });

  const res = await fetch(`${POSTS_URL}?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'LinkedIn-Version': LINKEDIN_API_VERSION,
      'X-Restli-Protocol-Version': '2.0.0',
    },
  });

  if (res.status === 403 || res.status === 401) {
    return {
      posts: [],
      warning:
        'LinkedIn hat den Zugriff auf Post-Daten abgelehnt (fehlende Freigabe). ' +
        'Fuer Analytics zu eigenen Beitraegen musst du im LinkedIn Developer Portal ' +
        'das Produkt "Community Management API" beantragen - das prueft LinkedIn manuell. ' +
        'Siehe README.md, Abschnitt LinkedIn.',
    };
  }
  if (!res.ok) {
    return { posts: [], warning: `LinkedIn-API-Fehler: ${res.status} ${await res.text()}` };
  }

  const data = await res.json();
  const elements = data.elements ?? [];
  const posts = elements.map((el) => normalizePost(el));
  return { posts, warning: null };
}

function normalizePost(el) {
  const commentary = el.commentary || '';
  return {
    externalId: el.id,
    publishedAt: el.publishedAt ?? el.createdAt ?? null,
    content: commentary,
    mediaType: el.content?.media ? 'media' : 'text',
    permalink: el.id ? `https://www.linkedin.com/feed/update/${encodeURIComponent(el.id)}` : null,
    likes: 0,
    comments: 0,
    shares: 0,
    views: 0,
    saves: 0,
    hashtags: extractHashtags(commentary),
    raw: el,
  };
}

function extractHashtags(text) {
  return (text.match(/#[\p{L}0-9_]+/gu) || []).map((h) => h.toLowerCase());
}
