# Soul Studio

Dein Produktionsstudio für Desk Revolution. Du planst Beiträge in Notion. Soul Studio macht daraus fertige Videos, Carousels und Bilder im Marken-Look und legt sie in Notion und Metricool ab.

## So läuft es im Alltag

1. Du schreibst einen Beitrag im Notion-Redaktionsplan („Desk Revolution – Redaktionsplan“): Text ins Feld **Entwurfstext** oder in die Seite, **Format** wählen (Video, Reel, Carousel, Bild, Story, Post), **Plattform** wählen, **Geplantes Datum** setzen.
2. Du stellst den **Status auf „Produzieren“**.
3. Jeden Morgen um 8 Uhr läuft die Routine „Soul Studio“ in Claude. Sie liest die Einträge, schreibt das Skript oder die Slides in deiner Sprache, produziert das Asset und
   - hängt die Dateien an die Notion-Seite (Feld **Asset**), schreibt eine **Produktions-Notiz** und setzt den Status auf **„Zur Freigabe“**,
   - stellt den Beitrag in Metricool zur Freigabe ein und trägt die **Metricool-Post-ID** ein, Status **„Geplant“**.
4. Du gibst in Metricool frei. Fertig.

Was pro Format entsteht:

| Format in Notion | Ergebnis |
|---|---|
| Video, Reel | Hochkant-Video, 30 bis 50 Sekunden: du sprichst in die Kamera (aus deinem Foto und deiner Stimme erzeugt), dazwischen Szenen aus dem Assistenzalltag mit deiner Stimme aus dem Off, große Untertitel, Abspann |
| Carousel | 7 Slides im Marken-Look als PNG und als PDF für LinkedIn |
| Bild | entweder ein museumsreifes Konzept-Plakat (abstrakte/institutionelle Aussagen) oder eine neu komponierte Szene mit dir (persönliche Beiträge, Wachstumsreihe) — deine Referenzfotos werden dabei nie unverändert übernommen |
| Story | dieselbe Postkarte im Hochformat 9:16 |
| Post, Poll | nur der Beitragstext |

## Was du einmalig brauchst

Carousel, Bild und Story funktionieren sofort. Für **Videos mit deinem Gesicht und deiner Stimme** braucht die Routine drei Zugänge und ein Foto:

| Zugang | Wofür | Kosten |
|---|---|---|
| **OpenAI** (platform.openai.com → API Keys) | Bild-Postings: das Konzept-Plakat (`gpt-image-1`) und, bei persönlichen Beiträgen, eine neue Szene mit dir (Bildbearbeitung mit deinem Referenzfoto) | Bezahlung pro Bild, kein Abo. Ca. 0,17–0,20 $ pro Bild. |
| **fal.ai** (fal.ai → Keys, optional) | dieselben zwei Bildarten über Nano Banana Pro, außerdem Videos: Foto + Stimme → sprechendes Video (OmniHuman 1.5) | Bezahlung pro Einheit, kein Abo. Bild ca. 0,15 $, Video ca. 0,16 $/Sekunde. |
| **ElevenLabs** (elevenlabs.io): Stimme klonen, dann Profil → API Keys | deine Stimme | gratis bis ca. 10 Minuten Sprache im Monat, sonst ab ca. 5 € |
| **Pexels** (pexels.com/api) | Stock-Clips für die Szenen ohne Gesicht, Fotos für Bild-Postings | kostenlos |
| **Dein Foto** | Notion-Seite „Soul Studio – Dein Foto“: ein bis drei Fotos hochladen, Hinweise stehen auf der Seite | kostenlos |

Die Schlüssel hinterlegst du in Claude unter *Umgebung → Umgebungsvariablen* (nicht im Code):

```
FAL_KEY=…
ELEVENLABS_API_KEY=…
ELEVENLABS_VOICE_ID=…      (die ID deiner geklonten Stimme)
PEXELS_API_KEY=…
```

Außerdem muss die Claude-Umgebung ins Internet dürfen, mindestens zu `fal.run`, `queue.fal.run`, `fal.media`, `api.elevenlabs.io`, `api.pexels.com`, `videos.pexels.com`, `images.pexels.com` und den Notion-Dateiservern (Einstellung *Netzwerk* der Umgebung).

Videomodus in `config.yaml` → `video.mode`: `mixed` (Standard: Hook und Schluss mit Gesicht, dazwischen Szenen), `talking_head` (nur Gesicht, teurer), `broll_only` (ohne Gesicht, fast kostenlos).

## Wo was liegt

- `prompts/brief_system.md`: die Sprach- und Formatregeln. Hier änderst du Tonalität oder Aufbau.
- `prompts/routine.md`: die Arbeitsanweisung für die Routine.
- `config.yaml`: Farben, Schriften, Längen, Notion- und Metricool-Einstellungen.
- `output/`: fertige Assets, je Auftrag ein Ordner.

## Für Technik-Interessierte

```bash
cd soul-studio
pip install -r requirements.txt
python -m soul_studio check                    # was ist eingerichtet
python -m soul_studio schema                   # JSON-Schema des Briefings
python -m soul_studio render brief.json --out output/test --mock   # ganze Strecke mit Platzhaltern
python -m soul_studio produce beitrag.md       # mit ANTHROPIC_API_KEY: Briefing per API + Produktion
python -m pytest tests -q
```

Der Ablauf: Briefing (JSON) → ElevenLabs-Stimme mit Wort-Zeitstempeln → Clip je Block (talking: Foto + Stimme über fal.ai OmniHuman; broll: Pexels oder fal Text-zu-Video) → ffmpeg-Schnitt mit ASS-Untertiteln in League Spartan, Einblendungen in Playfair, Abspann → `final.mp4`. Carousels und Bilder rendert Pillow direkt.
