import { Router } from 'express';
import crypto from 'node:crypto';
import * as linkedin from '../platforms/linkedin.js';
import * as instagram from '../platforms/instagram.js';
import * as tiktok from '../platforms/tiktok.js';
import { saveAccount, deleteAccount } from '../db.js';
import { isPlatformConfigured } from '../config.js';

const router = Router();

function requireConfigured(platform) {
  return (req, res, next) => {
    if (!isPlatformConfigured(platform)) {
      return res
        .status(400)
        .send(
          `${platform} ist noch nicht konfiguriert. Trage die Zugangsdaten in der .env-Datei ein (siehe .env.example) und starte den Server neu.`,
        );
    }
    next();
  };
}

// --- LinkedIn ---
router.get('/linkedin', requireConfigured('linkedin'), (req, res) => {
  const state = crypto.randomBytes(16).toString('hex');
  req.session.linkedinState = state;
  res.redirect(linkedin.getAuthUrl(state));
});

router.get('/linkedin/callback', requireConfigured('linkedin'), async (req, res) => {
  const { code, state, error, error_description: errorDescription } = req.query;
  if (error) return res.status(400).send(`LinkedIn-Fehler: ${error} - ${errorDescription ?? ''}`);
  if (!state || state !== req.session.linkedinState) return res.status(400).send('Ungueltiger State-Parameter.');
  try {
    const result = await linkedin.exchangeCode(code);
    saveAccount({ platform: 'linkedin', ...result });
    res.redirect('/?connected=linkedin');
  } catch (err) {
    res.status(500).send(`LinkedIn-Verbindung fehlgeschlagen: ${err.message}`);
  }
});

// --- Instagram ---
router.get('/instagram', requireConfigured('instagram'), (req, res) => {
  const state = crypto.randomBytes(16).toString('hex');
  req.session.instagramState = state;
  res.redirect(instagram.getAuthUrl(state));
});

router.get('/instagram/callback', requireConfigured('instagram'), async (req, res) => {
  const { code, state, error, error_description: errorDescription } = req.query;
  if (error) return res.status(400).send(`Instagram-Fehler: ${error} - ${errorDescription ?? ''}`);
  if (!state || state !== req.session.instagramState) return res.status(400).send('Ungueltiger State-Parameter.');
  try {
    const result = await instagram.exchangeCode(code);
    saveAccount({ platform: 'instagram', ...result });
    res.redirect('/?connected=instagram');
  } catch (err) {
    res.status(500).send(`Instagram-Verbindung fehlgeschlagen: ${err.message}`);
  }
});

// --- TikTok ---
router.get('/tiktok', requireConfigured('tiktok'), (req, res) => {
  const state = crypto.randomBytes(16).toString('hex');
  const { verifier, challenge } = tiktok.generatePkce();
  req.session.tiktokState = state;
  req.session.tiktokVerifier = verifier;
  res.redirect(tiktok.getAuthUrl(state, challenge));
});

router.get('/tiktok/callback', requireConfigured('tiktok'), async (req, res) => {
  const { code, state, error, error_description: errorDescription } = req.query;
  if (error) return res.status(400).send(`TikTok-Fehler: ${error} - ${errorDescription ?? ''}`);
  if (!state || state !== req.session.tiktokState) return res.status(400).send('Ungueltiger State-Parameter.');
  try {
    const result = await tiktok.exchangeCode(code, req.session.tiktokVerifier);
    saveAccount({ platform: 'tiktok', ...result });
    res.redirect('/?connected=tiktok');
  } catch (err) {
    res.status(500).send(`TikTok-Verbindung fehlgeschlagen: ${err.message}`);
  }
});

router.post('/disconnect/:platform', (req, res) => {
  const { platform } = req.params;
  if (!['linkedin', 'instagram', 'tiktok'].includes(platform)) {
    return res.status(400).json({ error: 'Unbekannte Plattform.' });
  }
  deleteAccount(platform);
  res.json({ ok: true });
});

export default router;
