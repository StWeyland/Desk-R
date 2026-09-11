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
| Video, Reel | Hochkant-Video, 30 bis 50 Sekunden: Szenen aus dem Assistenzalltag (Stock-Clips), deine Stimme aus dem Off, große Untertitel, Abspann |
| Carousel | 7 Slides im Marken-Look als PNG und als PDF für LinkedIn |
| Bild | Statement-Bild 4:5 mit Headline, optional mit Foto |
| Story | Statement-Bild 9:16 |
| Post, Poll | nur der Beitragstext |

## Was du einmalig brauchst

Carousel, Bild und Story funktionieren sofort. Für **Videos mit deiner Stimme** braucht die Routine zwei Zugänge:

| Zugang | Wofür | Kosten |
|---|---|---|
| **ElevenLabs** (elevenlabs.io): Stimme klonen, dann Profil → API Keys | deine Stimme aus dem Off | gratis bis ca. 10 Minuten Sprache im Monat, sonst ab ca. 5 € |
| **Pexels** (pexels.com/api): kostenlosen API-Key holen | Stock-Clips und Fotos | kostenlos |

Diese Werte hinterlegst du in Claude unter *Umgebung → Umgebungsvariablen* (nicht im Code):

```
ELEVENLABS_API_KEY=…
ELEVENLABS_VOICE_ID=…      (die ID deiner geklonten Stimme)
PEXELS_API_KEY=…
```

Außerdem muss die Claude-Umgebung ins Internet dürfen, mindestens zu `api.elevenlabs.io`, `api.pexels.com`, `videos.pexels.com`, `images.pexels.com` (Einstellung *Netzwerk* der Umgebung).

Optional, wenn du statt Stock-Clips KI-generierte Szenen willst (kostet pro Clip): `FAL_KEY` von fal.ai und in `config.yaml` `footage.provider: fal`.

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

Der Ablauf: Briefing (JSON) → ElevenLabs-Stimme mit Wort-Zeitstempeln → Clip je Block (Pexels oder fal) → ffmpeg-Schnitt mit ASS-Untertiteln in League Spartan, Einblendungen in Playfair, Abspann → `final.mp4`. Carousels und Bilder rendert Pillow direkt.
