# Soul Studio

Dein eigenes Produktionsstudio für Kurzvideos und Bild-Postings.
Du schreibst den Beitrag. Der Rest passiert automatisch.

**So funktioniert es**

1. Ein neuer Beitrag landet in `content/posts/` (oder in einer Notion-Datenbank).
2. Claude liest den Beitrag und schreibt ein Briefing: Hook, Sprechskript in Blöcken, Szenen, Beitragstext, Hashtags. Es entscheidet auch, ob ein Video oder ein Bild besser passt.
3. Für jeden Block entsteht ein Bild mit deiner **Soul ID** (Higgsfield Soul V2), also mit deinem Gesicht, konsistent über alle Szenen.
4. Deine Stimme kommt aus **ElevenLabs** (eigene geklonte Stimme, Modell Eleven v3) mit Wort-Zeitstempeln für die Untertitel.
5. Aus Bild und Tonspur wird ein sprechendes Video (Seedance 2.5, Lippen synchron zum Ton). Szenen ohne Sprecherin entstehen mit Kling 3.0.
6. ffmpeg schneidet alles zusammen: wortweise Untertitel im Marken-Look, Einblendungen, Abspann mit Wortmarke.
7. Ergebnis: `final.mp4` oder `final.jpg` plus `caption.txt` mit Beitragstext und Hashtags. Optional wird alles direkt im Metricool-Planer angelegt.

Das Video-Format orientiert sich an erfolgreichen deutschen Kurzvideo-Creatorn (Hook in zwei Sekunden, schnelle Schnitte, große Untertitel), bleibt aber in der Sprache und Haltung von Desk Revolution.

---

## Einmalige Einrichtung

### 1. Werkzeuge

```bash
cd soul-studio
pip install -r requirements.txt
npm install -g @higgsfield/cli        # oder: curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh
higgsfield auth login                 # öffnet den Browser, einmalig
higgsfield workspace list             # falls du mehrere Workspaces hast: higgsfield workspace set <id>
```

ffmpeg wird automatisch mitinstalliert (`imageio-ffmpeg`). Ein systemweites ffmpeg wird bevorzugt, falls vorhanden.

### 2. Schlüssel

```bash
cp .env.example .env
```

Trage ein:

| Schlüssel | Woher |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `ELEVENLABS_API_KEY` | elevenlabs.io → Profil → API Keys |
| `ELEVENLABS_VOICE_ID` | deine geklonte Stimme, siehe `python -m soul_studio voices` |
| `SOUL_ID` | entsteht in Schritt 3 |

### 3. Deine Soul ID trainieren

Lege 5 bis 20 Fotos von dir in `character/photos/` (Hinweise dort in der README). Dann:

```bash
python -m soul_studio soul create --name steffi
```

Das Training dauert ein paar Minuten. Die ausgegebene ID trägst du als `SOUL_ID` in `.env` ein (oder in `config.yaml` unter `character.soul_id`). Soul-Training braucht bei Higgsfield mindestens den Basic-Plan.

Passe außerdem in `config.yaml` die Felder `character.look` und `character.setting` an: So sieht die Figur in jeder Szene aus, so sieht ihre Umgebung aus.

### 4. Prüfen

```bash
python -m soul_studio check
```

---

## Täglich

**Ein Beitrag, ein Video**

```bash
python -m soul_studio produce content/posts/mein-beitrag.md
python -m soul_studio produce --text "Montagmorgen, 64 Mails …" --title "Posteingang"
```

**Nur das Briefing ansehen, bevor Credits fließen**

```bash
python -m soul_studio brief content/posts/mein-beitrag.md
python -m soul_studio produce content/posts/mein-beitrag.md --dry-run
```

Das Briefing liegt danach als `output/<beitrag>/brief.json`. Du kannst es von Hand ändern (Skript kürzen, Szene umschreiben) und dann `produce` starten. Vorhandene Briefings werden wiederverwendet.

**Alle neuen Beiträge auf einmal**

```bash
python -m soul_studio run              # verarbeitet alles, was noch nicht in state/processed.json steht
python -m soul_studio watch            # beobachtet den Ordner dauerhaft (alle 5 Minuten)
python -m soul_studio run --publish    # zusätzlich in Metricool einplanen (publish.enabled: true)
```

**Format erzwingen**

```bash
python -m soul_studio produce beitrag.md --format image
```

---

## Vollautomatisch mit GitHub Actions

Der Workflow `.github/workflows/soul-studio.yml` startet, sobald ein Beitrag nach `content/posts/` gepusht wird, außerdem täglich um 8 Uhr (für Notion) und per Knopfdruck. Fertige Videos werden ins Repository committet und sind damit über GitHub Pages öffentlich erreichbar (`publish.public_base_url`), was Metricool zum Einplanen braucht.

Secrets im Repository (Settings → Secrets and variables → Actions):

- `ANTHROPIC_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `SOUL_ID`
- `HIGGSFIELD_CREDENTIALS_JSON`: Inhalt von `~/.config/higgsfield/credentials.json` nach `higgsfield auth login` auf deinem Rechner. Die CLI arbeitet mit OAuth, es gibt keinen dauerhaften API-Schlüssel; läuft die Sitzung ab, einmal neu anmelden und das Secret aktualisieren.
- `HIGGSFIELD_WORKSPACE_ID`, wenn du in einem Workspace arbeitest
- optional `NOTION_TOKEN`, `METRICOOL_TOKEN`

---

## Notion als Quelle (optional)

In `config.yaml` unter `sources.notion` die Datenbank-ID eintragen. Beiträge mit Status „Video erstellen“ werden geholt, nach der Produktion auf „Video erstellt“ gesetzt. Der Text kommt aus der Eigenschaft `Text` oder, wenn leer, aus dem Seiteninhalt.

## Metricool (optional)

`publish.enabled: true`, `user_id` und `blog_id` eintragen, `METRICOOL_TOKEN` setzen (Advanced-Plan nötig). Beiträge werden standardmäßig als Entwurf 24 Stunden später angelegt. Du gibst frei.

---

## Stellschrauben (`config.yaml`)

| Feld | Wirkung |
|---|---|
| `video.mode` | `mixed` (Sprechszenen und B-Roll), `talking_head` (nur du), `broll_only` (Stimme aus dem Off, günstiger) |
| `video.target_seconds`, `min_blocks`, `max_blocks` | Länge und Rhythmus |
| `video.captions` | `word` (wortweise hervorgehoben), `line`, `none` |
| `models.talking_video` | `seedance_2_5` (Standard, Lipsync aus deiner Tonspur), alternativ `seedance_2_0` |
| `models.broll_video` | `kling3_0`, `seedance_2_5`, `veo3_1` |
| `voice.provider` | `elevenlabs` oder `higgsfield` (nutzt Higgsfield-Credits, keine Wort-Zeitstempel) |
| `llm.model`, `llm.effort` | Claude-Modell fürs Briefing |

Der Stil des Briefings steht in `prompts/brief_system.md`. Dort kannst du Tonalität, Regeln und Formate ändern.

## Kosten im Blick

Pro Video entstehen je Block ein Soul-Bild und ein Videoclip (Higgsfield-Credits) sowie ein paar Sekunden Sprache (ElevenLabs-Zeichen). Mit `--dry-run` siehst du das Briefing, bevor etwas generiert wird. `broll_only` und kürzere `target_seconds` sparen am meisten.

## Tests

```bash
python -m pytest soul-studio/tests -q
python -m soul_studio produce content/posts/_beispiel-posteingang.md --mock   # ganze Strecke mit Platzhaltern, ohne Dienste
```
