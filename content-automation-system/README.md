# Content-Automation-Learning-Loop — Desk Revolution

Ein System, das für Steffi automatisch Content erstellt, veröffentlicht, auswertet — und aus der Auswertung wieder neue Content-Ideen ableitet. Genau der Kreislauf aus der Skizze: **Idee → Claude → Recherche/Assets → Auto-Post → Analytics → zurück zur nächsten Idee.**

```
   IDEE ──▶ CLAUDE ──▶ APIFY ──▶ ELEVENLABS ──▶ GPT IMAGE 2 ──▶ SEEDANCE 2.5 ──▶ AUTO-POST
    ▲                          (alles orchestriert über n8n)                        │
    │                                                                                ▼
    └──────────────────────────── ANALYTICS ◀──────────────────────── LinkedIn (Instagram/TikTok später)
```

## Was schon steht

Drei Notion-Datenbanken bilden das Gedächtnis des Systems — die habe ich in deinem Notion-Workspace bereits angelegt bzw. erweitert:

| Datenbank | Rolle | Link |
|---|---|---|
| 🔎 **Research-Pool** | Rohstoff für Ideen: Trends, Konkurrenz, Studien, Zitate — und jetzt auch **Learnings** aus eigenen Posts | [öffnen](https://app.notion.com/p/975d768936234fa29e81c4877a45663b) |
| 🗓️ **Content-Pipeline** | Der Redaktionsplan: Entwurf → Zur Freigabe → Freigegeben → Geplant → Gepostet | [öffnen](https://app.notion.com/p/cb3d701d818a498cb5e39aa53dc3a894) |
| 📊 **Performance** *(neu)* | Kennzahlen je gepostetem Beitrag, verknüpft mit der Content-Pipeline | [öffnen](https://app.notion.com/p/340f93186c7e4db8a3ff092b08409ec9) |

Details, Feldbeschreibungen und eine kurze "so benutzt du das" findest du in [`notion-datenmodell.md`](./notion-datenmodell.md).

## Die Dateien in diesem Ordner

- **`architektur.md`** — wie das System als Ganzes funktioniert, Schritt für Schritt entlang des Bildes.
- **`notion-datenmodell.md`** — die drei Datenbanken im Detail + Einstieg für Notion-Neulinge.
- **`n8n-workflow.json`** — der importierbare n8n-Workflow, der die komplette Kette baut.
- **`setup-checkliste.md`** — was du an Accounts/API-Keys brauchst, in der Reihenfolge, in der du sie anlegen solltest.
- **`prompts/`** — die vier Claude-Prompts, die im Workflow stecken (Ideengenerierung, Post-Drehbuch, Bildprompt, Lern-Analyse), fertig in deiner Stimme geschrieben.

## Der wichtigste Designentscheid: dein Freigabe-Punkt

Das System läuft **nicht** vollautomatisch von der Idee bis zum Post. Claude generiert Idee, Text und Bild in einem Zug und legt alles als Entwurf in der Content-Pipeline ab (Status „Entwurf" → „Zur Freigabe", sobald alles fertig ist). Nichts geht raus, bevor du den Status manuell auf „Freigegeben" setzt.

Entwürfe, die dich gar nicht überzeugen, kannst du schon vorher — solange sie noch bei „Entwurf" liegen — einfach archivieren, ganz ohne Automatisierung dafür zu brauchen.

Das ist kein technisches Limit, sondern Absicht: Du bleibst diejenige, die entscheidet, was unter deinem Namen rausgeht — das System übernimmt die Fleißarbeit davor und danach.

## Nächster Schritt

Lies `setup-checkliste.md` und arbeite sie von oben nach unten ab — jeder Punkt baut auf dem vorherigen auf. Wenn du willst, gehe ich sie mit dir gemeinsam Schritt für Schritt durch.
