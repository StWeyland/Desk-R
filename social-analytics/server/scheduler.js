import cron from 'node-cron';
import * as linkedin from './platforms/linkedin.js';
import * as instagram from './platforms/instagram.js';
import * as tiktok from './platforms/tiktok.js';
import { getAllAccounts, getAccount, getCompetitors, upsertPosts, addSyncLog } from './db.js';

const platformModules = { linkedin, instagram, tiktok };

// Montag, Mittwoch, Freitag um 06:00 Uhr (Berlin-Zeit) - unabhaengig davon, in
// welcher Zeitzone der Server selbst laeuft.
const SCHEDULE = '0 6 * * 1,3,5';
const TIMEZONE = 'Europe/Berlin';

export async function runAutomaticSync(triggerType = 'scheduled') {
  const results = { accounts: {}, competitors: {} };

  for (const account of getAllAccounts()) {
    const mod = platformModules[account.platform];
    if (!mod) continue;

    if (account.expires_at && account.expires_at < Date.now()) {
      results.accounts[account.platform] = { error: 'Zugriffstoken abgelaufen - bitte im Dashboard erneut verbinden.' };
      continue;
    }

    try {
      const { posts, warning } = await mod.fetchPosts(account.access_token, account.meta);
      upsertPosts(account.platform, posts);
      results.accounts[account.platform] = { count: posts.length, warning: warning ?? null };
    } catch (err) {
      results.accounts[account.platform] = { error: err.message };
    }
  }

  const igAccount = getAccount('instagram');
  for (const competitor of getCompetitors().filter((c) => c.tracking_mode === 'api')) {
    if (competitor.platform !== 'instagram') continue; // aktuell einziger automatisierter Wettbewerber-Weg
    if (!igAccount) {
      results.competitors[competitor.id] = { error: 'Kein eigenes Instagram-Konto verbunden.' };
      continue;
    }
    try {
      const { posts, warning } = await instagram.fetchCompetitorPosts(
        igAccount.access_token,
        igAccount.meta.igUserId,
        competitor.handle,
      );
      upsertPosts('instagram', posts, { ownerHandle: competitor.handle, source: 'api' });
      results.competitors[competitor.id] = { count: posts.length, warning: warning ?? null };
    } catch (err) {
      results.competitors[competitor.id] = { error: err.message };
    }
  }

  addSyncLog(triggerType, results);
  return results;
}

export function startScheduler() {
  cron.schedule(
    SCHEDULE,
    () => {
      runAutomaticSync('scheduled').catch((err) => console.error('Automatischer Sync fehlgeschlagen:', err));
    },
    { timezone: TIMEZONE },
  );
  console.log(`Automatische Analyse geplant: Mo/Mi/Fr 06:00 Uhr (${TIMEZONE}).`);
}
