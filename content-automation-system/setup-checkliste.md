# Setup-Checkliste

In dieser Reihenfolge abarbeiten — jeder Punkt baut auf dem vorherigen auf. Rechne für die komplette Einrichtung realistisch 1-2 Nachmittage ein, plus etwas Geduld beim ersten Testlauf.

## 1. n8n — die Werkstatt

n8n ist das Werkzeug, das alle anderen Dienste verbindet und steuert.
- **Einfachster Einstieg:** n8n Cloud (n8n.io), Starter-Plan reicht für den Anfang. Kein eigener Server nötig.
- Alternative, wenn du technisch versierter werden willst: selbst gehostet (z. B. auf einem kleinen Server) — spart laufende Kosten, braucht aber Wartung. Für den Start würde ich dir zur Cloud-Variante raten.
- Nach der Anmeldung: importiere `n8n-workflow.json` aus diesem Ordner über „Import from File".

## 2. Notion — das Gedächtnis

Ist bereits eingerichtet (Research-Pool, Content-Pipeline, Performance). Was noch fehlt, damit n8n dort schreiben/lesen darf:
1. In Notion: Einstellungen → „Connections" → eine neue Integration erstellen (z. B. „n8n-Automation"), Integrationstoken kopieren.
2. Diese Integration bei allen drei Datenbanken über „..." → „Connections" freigeben.
3. Den Integrationstoken in n8n als Notion-Credential hinterlegen.

## 3. Claude (Anthropic API)

Für Ideengenerierung, Post-Texte, Bildprompts und Lern-Analyse — das kreative Herzstück.
- Account auf console.anthropic.com, API-Key erstellen.
- In n8n als Credential („Header Auth" oder das native Anthropic-Node-Credential) hinterlegen.
- Kosten: nutzungsbasiert, bei dem hier geplanten Volumen (wenige Posts/Woche) im niedrigen zweistelligen Euro-Bereich pro Monat.

## 4. Apify — die Recherche

Für automatisiertes Sammeln von Trends/Konkurrenz-Content.
- Account auf apify.com, API-Token unter „Settings" → „Integrations".
- Du brauchst mindestens einen passenden Actor aus dem Apify Store (z. B. für LinkedIn-Hashtag- oder Google-Trends-Scraping) — den suchst du dir am besten gemeinsam mit mir aus, sobald der Rest steht, damit er wirklich zu deinen Themen passt.
- Kosten: nutzungsbasiert, meist wenige Euro pro Lauf.

## 5. GPT Image 2 (OpenAI)

Für die Bilder im DeskR-Look.
- Account auf platform.openai.com, API-Key erstellen.
- **Wichtig:** Der genaue Modellname für die Bildgenerierung ändert sich bei OpenAI gelegentlich (aktuell z. B. „gpt-image-1" o. Ä.). Prüfe vor dem ersten Lauf in der OpenAI-Doku, wie das aktuelle Bildmodell genau heißt, und trag es im entsprechenden n8n-Node ein.

## 6. ElevenLabs — die Stimme

Nur relevant für Video-Content.
- Account auf elevenlabs.io, API-Key unter „Profile" → „API Keys".
- Falls du mit einer eigenen, wiedererkennbaren Stimme arbeiten willst: „Voice Cloning" einrichten (braucht eine kurze Sprachaufnahme von dir) — sonst reicht eine der Standard-Stimmen zum Start.

## 7. Seedance 2.5 — das Video

Auch nur für Video-Content.
- Seedance ist ein Video-Modell von ByteDance; der Zugriff läuft aktuell meist über eine Plattform wie fal.ai oder die Volcengine-API — beides braucht einen eigenen Account und API-Key.
- **Ehrliche Einschätzung:** das ist der technisch aufwendigste und teuerste Baustein. Mein Vorschlag: **starte ohne Video** — Text- und Bild-Posts zuerst zuverlässig zum Laufen bringen, Video als zweite Ausbaustufe.

## 8. LinkedIn — das Posten

Das ist der Punkt, bei dem ich ehrlich sein muss: **Direktes automatisches Posten auf ein persönliches LinkedIn-Profil ist von LinkedIn selbst stark eingeschränkt** — die offizielle API erlaubt das für normale Profile praktisch nicht, nur für Company Pages mit Freigabe.

Zwei realistische Wege:
- **Über eine Zwischenplattform** wie z. B. Unipile, Ayrshare oder Metricool, die den LinkedIn-Zugriff für dich verwaltet und eine einfache API für n8n bereitstellt. Das ist der Weg, den der Workflow in diesem Ordner vorbereitet (HTTP-Node, leicht auf den Anbieter deiner Wahl umstellbar).
- **Manuell mit Vorbereitung:** das System erstellt und bewertet den Content vollautomatisch, aber der letzte Klick „Posten" bleibst du. Kein zusätzlicher Account nötig, dafür ein täglicher manueller Schritt.

Meine Empfehlung: mit der manuellen Variante starten (kostet dich nichts, keine Abhängigkeit von einem weiteren Tool), und auf eine Zwischenplattform wechseln, sobald der Rhythmus steht und sich Vollautomatisierung lohnt.

## 9. Reihenfolge des ersten Testlaufs

1. Nur Schritte 1-3 verbinden (n8n, Notion, Claude) und den Workflow bis „Idee in Content-Pipeline" einmal manuell auslösen.
2. Prüfen, ob die Idee sinnvoll und in deiner Stimme klingt — bei Bedarf den Prompt in `prompts/01-ideengenerierung.md` nachschärfen.
3. Erst wenn das passt: Apify, Bildgenerierung, und zuletzt Posting dazuschalten.

Kein Grund, alles am ersten Tag scharf zu schalten — jeder Baustein einzeln getestet spart dir später Fehlersuche im ganzen System.
