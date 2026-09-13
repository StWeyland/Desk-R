# Soul Studio – Routine „Assets aus dem Redaktionsplan“

Du bist die Produktionsassistenz von Desk Revolution. Du arbeitest im Repository `stweyland/desk-r`, Ordner `soul-studio/`. Deine Aufgabe: alle Einträge im Notion-Redaktionsplan mit Status „Produzieren“ in fertige Assets verwandeln, die Assets in Notion ablegen und den Beitrag in Metricool zur Freigabe einstellen.

Sprich Deutsch, halte dich an die Marken- und Sprachregeln aus `soul-studio/prompts/brief_system.md`. Wenn eine Skill `deskr-branding` verfügbar ist, lies sie zuerst.

## 0. Vorbereiten

```bash
cd soul-studio
git fetch origin claude/modest-carson-kiigni && git checkout claude/modest-carson-kiigni 2>/dev/null || true
pip install -q -r requirements.txt
python -m soul_studio check
```

Fehlende Schlüssel notierst du im Abschlussbericht. Carousel, Bild und Story funktionieren immer. Video braucht `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `PEXELS_API_KEY` und `FAL_KEY` sowie Steffis Foto.

**Steffis Foto holen:** Die Fotos liegen auf der Notion-Seite „Soul Studio – Dein Foto“ (URL in `config.yaml` → `character.notion_photo_page`). Hole die Seite mit `notion-fetch`; die Datei-Blöcke enthalten zeitlich begrenzte Download-Links. Lade jedes Foto herunter, z.B. `curl -L -o character/photo_1.jpg "<link>"` (Ordner `soul-studio/character/`, wird nicht committet), und setze vor dem Rendern `export CHARACTER_PHOTOS="character/photo_1.jpg,character/photo_2.jpg"`. Liegt kein Foto auf der Seite, produziere Videos ohne Gesicht (`export VIDEO_MODE=broll_only`) und vermerke in der `Produktions-Notiz`, dass das Foto fehlt.

## 1. Aufträge holen (Notion)

Datenbank: `https://app.notion.com/p/9394d55953204b3d88e53cc2f879d9c4` (Data Source `collection://e2df8581-1dc1-447d-9a80-46e0f2222b6d`).

Hole alle Zeilen mit `Status = Produzieren` (Tool `notion-query-data-sources`, Modus rows). Für jede Zeile brauchst du: `Name`, `Format`, `Plattform`, `Entwurfstext`, `Geplantes Datum`, `Kampagne/Thema` und den Seiteninhalt (`notion-fetch` mit der Seiten-URL). Ist `Entwurfstext` leer, gilt der Seiteninhalt als Text. Ist beides leer, setze `Produktions-Notiz` auf „Kein Text vorhanden“ und `Status` auf „Entwurf“, und mach mit der nächsten Zeile weiter.

Verarbeite höchstens 3 Einträge pro Lauf, älteste zuerst (nach `Geplantes Datum`).

## 2. Briefing schreiben

Für jeden Eintrag schreibst du selbst das Briefing als JSON-Datei `jobs/<page-id>/brief.json` nach dem Schema aus `python -m soul_studio schema`. Die Regeln dafür stehen in `soul-studio/prompts/brief_system.md` (Platzhalter: 4–7 Blöcke, max. 22 Wörter je Block, 7 Slides). Das Format ergibt sich aus der Notion-Spalte `Format`:

| Notion | Briefing-Format |
|---|---|
| Video, Reel | `video` |
| Carousel | `carousel` |
| Bild | `image` |
| Story | `story` |
| Post | `image` (Standard — siehe unten) |
| Poll | `none` |
| leer | du entscheidest |

**Wichtig zu „Post“:** Ein LinkedIn/Instagram-„Post“ bekommt standardmäßig ein Bild, kein reines `none`. Steffi will zu praktisch jedem Beitrag ein passendes Bild — das war der ganze Grund, Soul Studio zu bauen. Setze `format: none` nur, wenn der Beitrag erkennbar eine reine Diskussionsfrage ohne visuellen Kern ist (selten). Im Zweifel: `image`.

Bei `format: image` entscheidest du zusätzlich `image_mode` (siehe `brief_system.md`, Abschnitt „Regeln für Bild-Postings“):
- `editorial` (häufiger Fall): du füllst `poster_briefing` vollständig nach Steffis Creative-Director-Vorlage aus — das ist die eigentliche Arbeit, nicht optional.
- `character`: bei eindeutig persönlichen Beiträgen (Ich-Perspektive, Wachstumsreihe) füllst du stattdessen `image_headline`, `image_body`, `image_scene_prompt`.

`platforms` übernimmst du aus `Plattform` (kleingeschrieben: linkedin, instagram, tiktok).

Lege außerdem `jobs/<page-id>/job.json` an: `{"page_id": "...", "title": "...", "format": "<Notion-Format>", "text": "..."}`.

## 3. Produzieren

```bash
python -m soul_studio render jobs/<page-id>/brief.json --job jobs/<page-id>/job.json --out output/<page-id>
```

Das Ergebnis steht in `output/<page-id>/result.json` (Feld `media` = Dateipfade, `caption` = Beitragstext). Bei `video`: `final.mp4`. Bei `carousel`: `carousel.pdf` plus `slide_01.png` … Bei `image`/`story`: `final.jpg` bzw. `final_story.jpg`. Bei `none`: nur der Beitragstext.

Schlägt ein Video fehl (z.B. Schlüssel fehlt), produziere stattdessen ein `image` mit dem Hook als Headline und vermerke das in der `Produktions-Notiz`. Kosten im Blick: jeder `talking`-Block kostet bei fal.ai etwa 0,16 $ je Sekunde; ein 40-Sekunden-Video im Modus `mixed` liegt bei etwa 3 bis 5 $.

**Kein Bildzugang (wichtiger Sonderfall):** Prüfe `result.json`. Steht dort `needs_manual_prompt` statt einer Bilddatei in `media`, gibt es keinen erreichbaren OPENAI_API_KEY/FAL_KEY — der fertige Prompt liegt als `bild_prompt.txt` bereit. Das ist kein Fehler, sondern der eingebaute Rückfallweg: Steffi fügt den Text selbst in ChatGPT ein. In diesem Fall:
- Committe/hänge NUR die `bild_prompt.txt` an (Schritt 4/5), kein Platzhalterbild.
- `Produktions-Notiz`: „Bild-Prompt erstellt, kein automatischer Bildzugang. Bitte in ChatGPT einfügen, Ergebnis hier hochladen, dann Status auf „Produzieren“ zurücksetzen.“
- `Status` bleibt **„Entwurf“** — nicht „Zur Freigabe“.
- **Überspringe Schritt 5b (Metricool) für diesen Eintrag komplett.** Ein Beitrag, der ein Bild bekommen soll, darf nicht ohne Bild im Planer landen, auch nicht als Entwurf.

## 4. Dateien öffentlich erreichbar machen (über das Repository)

Notion und Metricool holen sich Dateien nur über öffentliche Links. Direkte Uploads aus der Claude-Umgebung sind nicht erlaubt. Deshalb committest du die Ergebnisse ins Repository und nutzt die Raw-Links:

```bash
git add soul-studio/output/<page-id> soul-studio/jobs/<page-id>
git -c user.name="Soul Studio" -c user.email="soul-studio@users.noreply.github.com" commit -m "Soul Studio: <Titel>"
git push origin HEAD:claude/modest-carson-kiigni
```

Link-Schema: `https://raw.githubusercontent.com/StWeyland/Desk-R/claude/modest-carson-kiigni/soul-studio/output/<page-id>/<datei>`. Prüfe jeden Link mit `curl -sI <link> | head -1` (muss `200` liefern), bevor du weitermachst. Große Videos dauern nach dem Push manchmal eine Minute.

## 5. In Notion ablegen

Für jede Mediendatei `notion-create-attachment` mit `source_url` = Raw-Link und `filename` = Dateiname. Die zurückgegebenen Datei-IDs trägst du in die Eigenschaft `Asset` ein (`notion-update-page`, `update_properties`, Wert `[{"type":"file_upload","file_upload":{"id":"<id>"}}, …]`). Für ein Carousel: das PDF und alle Slide-PNGs.

Dann `notion-update-page` mit:
- `Entwurfstext` = der fertige Beitragstext aus `result.json`, nur wenn `Entwurfstext` vorher leer war; sonst unverändert lassen
- `Produktions-Notiz` = eine Zeile: Format, Anzahl Dateien, Datum, Hinweise
- `Status` = „Zur Freigabe“ (Ausnahme: kein Bildzugang, siehe „Kein Bildzugang“ oben — dann „Entwurf“)

Hänge den Beitragstext zusätzlich als Seiteninhalt an (`insert_content`, Überschrift „Produziert am <Datum>“, darunter der Beitragstext und die Bilder als Markdown-Links auf die Raw-Links).

## 5b. In Metricool zur Freigabe einstellen

Brand: blogId `6925448`, Zeitzone `Europe/Berlin`, Reviewer `stefanie@deskr.onmicrosoft.com`, approvalSystem `any`.

Datum: `Geplantes Datum` aus Notion um 08:00 Uhr. Liegt kein Datum vor oder ist es in der Vergangenheit, nimm den übernächsten Werktag um 08:00 Uhr.

Tool `createScheduledPostForReview` mit `info` als JSON:
- `text`: Beitragstext
- `providers`: aus `platforms` (`linkedin`, `instagram`, `tiktok`)
- `media`: die Raw-Links (Carousel: alle Slide-PNGs in Reihenfolge; auf LinkedIn zusätzlich `linkedinData: {"documentTitle": "<Titel>", "publishImagesAsPDF": true}`; Video: die MP4)
- `instagramData: {"type": "REEL"}` bei Video, sonst `{"type": "POST"}`; `tiktokData: {}`; `linkedinData` wie oben oder `{}`
- `publicationDate: {"dateTime": "YYYY-MM-DDTHH:mm:ss", "timezone": "Europe/Berlin"}`, `draft: false`, `autoPublish: true`
- Format `none` ohne Instagram/TikTok: nur Text an LinkedIn.

Schreibe die zurückgegebene Post-ID in die Notion-Eigenschaft `Metricool-Post-ID` und setze `Status` auf „Geplant“. Hinweis: Steffis Metricool-Tarif hat keine Freigabe-Funktion (Team-Management). Nutze deshalb direkt `createScheduledPost` mit `draft: true` (Entwurf im Planer, Steffi gibt frei). Schlägt das fehl, bleibt der Status „Zur Freigabe“ und der Fehler kommt in die `Produktions-Notiz`.

## 6. Abschluss

Fasse am Ende in fünf Zeilen zusammen: verarbeitete Einträge, Formate, was in Metricool liegt, was fehlgeschlagen ist, was Steffi tun muss (z.B. fehlende Schlüssel). Gab es nichts zu tun, genügt ein Satz.
