import 'dotenv/config';

const required = (value, name) => value ?? '';

export const config = {
  baseUrl: process.env.APP_BASE_URL || 'http://localhost:3000',
  port: Number(process.env.PORT) || 3000,
  sessionSecret: process.env.SESSION_SECRET || 'dev-only-insecure-secret-change-me',
  linkedin: {
    clientId: required(process.env.LINKEDIN_CLIENT_ID, 'LINKEDIN_CLIENT_ID'),
    clientSecret: required(process.env.LINKEDIN_CLIENT_SECRET, 'LINKEDIN_CLIENT_SECRET'),
  },
  instagram: {
    appId: required(process.env.INSTAGRAM_APP_ID, 'INSTAGRAM_APP_ID'),
    appSecret: required(process.env.INSTAGRAM_APP_SECRET, 'INSTAGRAM_APP_SECRET'),
  },
  tiktok: {
    clientKey: required(process.env.TIKTOK_CLIENT_KEY, 'TIKTOK_CLIENT_KEY'),
    clientSecret: required(process.env.TIKTOK_CLIENT_SECRET, 'TIKTOK_CLIENT_SECRET'),
  },
};

export function isPlatformConfigured(platform) {
  switch (platform) {
    case 'linkedin':
      return Boolean(config.linkedin.clientId && config.linkedin.clientSecret);
    case 'instagram':
      return Boolean(config.instagram.appId && config.instagram.appSecret);
    case 'tiktok':
      return Boolean(config.tiktok.clientKey && config.tiktok.clientSecret);
    default:
      return false;
  }
}
