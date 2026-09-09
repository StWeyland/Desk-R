# Desk-R Social Analytics

Analysetool, das sich per Live-API direkt mit deinen eigenen LinkedIn-, Instagram-
und TikTok-Konten verbindet, deine Beitraege abruft und daraus ein Dashboard baut:
Engagement pro Plattform, beste Uhrzeit/Wochentag zum Posten, meistgenutzte
Hashtags und deine Top-Beitraege. Zusaetzlich kannst du Wettbewerber-Konten
tracken und dich direkt mit ihnen vergleichen.

Wichtig: Keine der drei Plattformen erlaubt das automatisierte Auslesen fremder
Accounts per Scraping - das verstoesst gegen ihre Nutzungsbedingungen. Dieses
Tool nutzt ausschliesslich offizielle, autorisierte Wege:

- Fuer dein **eigenes** Konto auf allen drei Plattformen: OAuth-Login, den du
  selbst bestaetigst.
- Fuer **Wettbewerber auf Instagram**: die offizielle "Business Discovery"-API,
  die Meta genau fuer diesen Zweck bereitstellt - oeffentliche Kennzahlen
  anderer Business-/Creator-Konten, abgerufen ueber deinen eigenen Zugang.
- Fuer **Wettbewerber auf LinkedIn und TikTok**: Es gibt dort keine offizielle
  Schnittstelle fuer fremde Konten. Das Tool bietet dafuer ein manuelles
  Tracking - du traegst Zahlen ein, die du selbst beim Ansehen des oeffentlichen
  Profils siehst, und das Tool uebernimmt Speicherung, Trends und Vergleich.

## Setup

```bash
cd social-analytics
npm install
cp .env.example .env
```

`.env` mit deinen eigenen App-Zugangsdaten fuellen (Details je Plattform unten),
dann:

```bash
npm start
```

Das Dashboard laeuft danach unter `http://localhost:3000`.

## Pro Plattform eine eigene App registrieren

Jede Plattform verlangt, dass du selbst eine kleine "App" in ihrem
Entwickler-Portal anlegst - das ist der offizielle Weg, um eine Anwendung mit
deinem eigenen Konto zu verbinden. Es fallen dabei keine Kosten an.

### LinkedIn

1. App anlegen unter https://www.linkedin.com/developers/apps
2. Unter "Products" das Produkt **"Sign In with LinkedIn using OpenID Connect"**
   hinzufuegen (sofort verfuegbar, keine Pruefung noetig).
3. Unter "Auth" die Redirect-URL eintragen: `http://localhost:3000/auth/linkedin/callback`
4. Client ID / Client Secret aus "Auth" in die `.env` kopieren.
5. **Grenze:** Mit den self-serve Produkten bekommst du dein Profil und die
   Liste deiner eigenen Beitraege, aber keine Kennzahlen (Likes/Kommentare/
   Impressions) zu diesen Beitraegen. Dafuer muss LinkedIn zusaetzlich das
   Produkt **"Community Management API"** freischalten - das beantragst du im
   selben App-Dashboard, LinkedIn prueft das manuell (dauert typischerweise
   einige Tage und setzt meist eine Unternehmensseite voraus). Das Tool zeigt
   dir beim Sync eine klare Meldung, falls dieser Zugriff fehlt.

### Instagram (ueber Meta/Facebook)

1. App anlegen unter https://developers.facebook.com/apps (Typ "Business")
2. Produkt **"Instagram Graph API"** hinzufuegen.
3. Dein Instagram-Konto muss ein **Business- oder Creator-Konto** sein und mit
   einer Facebook-Seite verknuepft sein (Instagram-App -> Einstellungen ->
   Konto -> Konto-Center, dort mit einer Facebook-Seite verbinden).
4. Unter "App-Rollen -> Tester" dich selbst (dein Facebook-Konto) als Tester
   hinzufuegen und die Einladung in deinem Facebook-Konto annehmen. Damit
   funktionieren `instagram_basic` und `instagram_manage_insights` sofort,
   ohne App-Review durch Meta.
5. Redirect-URI in den Facebook-Login-Einstellungen eintragen:
   `http://localhost:3000/auth/instagram/callback`
6. App-ID / App-Secret in die `.env` kopieren.

### TikTok

1. App anlegen unter https://developers.tiktok.com/apps
2. Produkte **"Login Kit"** und **"Display API"** hinzufuegen.
3. Redirect-URI eintragen: `http://localhost:3000/auth/tiktok/callback`
4. Unter "Sandbox -> Target Users" dein eigenes TikTok-Konto als Testnutzer
   eintragen - damit funktioniert der Login mit deinem echten Konto, ohne dass
   TikTok die App vorher fuer alle Nutzer freigeben muss.
5. Client Key / Client Secret in die `.env` kopieren.

## Wettbewerber tracken

Im Bereich "Wettbewerber" im Dashboard ein Konto hinzufuegen (Plattform +
Handle/Profilname):

- **Instagram**: Klick auf "Abrufen" holt automatisch die neuesten oeffentlichen
  Beitraege des Wettbewerbers samt Likes/Kommentaren - vorausgesetzt, das Konto
  ist oeffentlich und auf Business oder Creator umgestellt (bei privaten Konten
  liefert Meta bewusst keine Daten, das ist so gewollt).
- **LinkedIn/TikTok**: Klick auf "Beitrag manuell hinzufuegen" oeffnet ein
  kleines Formular - Text/Link plus die Zahlen, die auf dem Profil sichtbar
  sind, eintragen und speichern. So laesst sich auch ohne API ein Verlauf
  aufbauen, den du selbst periodisch pflegst.

Der Vergleich "Du im Vergleich zu Wettbewerbern" zeigt das durchschnittliche
Engagement pro Beitrag nebeneinander; ueber den Filter bei "Top-Beitraege"
lassen sich eigene und fremde Beitraege ein- und ausblenden.

## Funktionsweise

- Beim Klick auf "Verbinden" leitet dich das Tool zum offiziellen Login der
  jeweiligen Plattform weiter. Du bestaetigst dort selbst, welche Daten das
  Tool sehen darf. Zugriffstoken werden lokal in `data/social-analytics.sqlite`
  gespeichert (per `.gitignore` von Git ausgeschlossen).
- "Synchronisieren" ruft deine neuesten Beitraege plus Kennzahlen ab und
  speichert sie lokal.
- Das Dashboard aggregiert alle gespeicherten Beitraege plattformuebergreifend.

## Grenzen, die die Plattformen selbst setzen

- **LinkedIn:** Post-Kennzahlen brauchen eine manuelle API-Freigabe (siehe
  oben) - ohne sie zeigt das Tool nur Beitragstexte, keine Likes/Kommentare.
- **Instagram:** Insights (Reichweite, Impressions, gespeichert) sind nur fuer
  Business/Creator-Konten verfuegbar, nicht fuer private Konten.
- **TikTok:** Die Display API liefert oeffentliche Kennzahlen zu deinen
  eigenen Videos; sehr neue Videos liefern Zaehler teils erst nach kurzer
  Verzoegerung.
- Zugriffstoken laufen ab (LinkedIn/TikTok i. d. R. 60 Tage, Instagram lang-
  lebige Token ebenfalls ca. 60 Tage). Laeuft ein Token ab, einfach das Konto
  im Dashboard erneut verbinden.
- **Wettbewerber auf Instagram**: Business Discovery liefert nur oeffentlich
  sichtbare Zahlen (Likes, Kommentare) - keine Insights wie Reichweite oder
  Impressions, die Meta nur dem Kontoinhaber selbst zeigt.
- **Wettbewerber auf LinkedIn/TikTok**: bewusst manuell, weil es dafuer keine
  autorisierte API gibt. Das ist kein technisches Provisorium, sondern die
  Grenze, die die Plattformen selbst ziehen.

## Tech-Stack

Node.js (Express) + eingebautes `node:sqlite` fuer die lokale Speicherung,
keine externe Datenbank noetig. Frontend ist reines HTML/CSS/JS mit Chart.js.
