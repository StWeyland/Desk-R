# Architektur: der Lern-Loop im Detail

Das System besteht aus zwei Zyklen, die ineinandergreifen: einem **Content-Zyklus** (Idee → fertiger Post) und einem **Lern-Zyklus** (Post → Analyse → neue Idee). n8n ist der Motor, der beide antreibt; Notion ist das Gedächtnis dazwischen.

## Zyklus 1 — Von der Idee zum Post

**1. Impuls sammeln (Apify)**
Ein n8n-Trigger (z. B. jeden Montagmorgen) startet einen Apify-Actor, der aktuelle Trends, Hashtags oder Konkurrenz-Posts zu deinen Kernthemen scraped (Zukunft der Assistenzrolle, KI-Zusammenarbeit, digitale Arbeitssysteme). Die Treffer landen automatisch als neue Einträge im **Research-Pool** (Kategorie „Trends" oder „Konkurrenz").

**2. Ideen generieren (Claude)**
n8n ruft Claude mit dem Prompt aus [`prompts/01-ideengenerierung.md`](./prompts/01-ideengenerierung.md) auf. Claude bekommt drei Dinge mit:
- die neuesten Research-Pool-Einträge (roher Impuls von außen),
- die letzten „Learnings"-Einträge (was aus vorherigen Posts gelernt wurde),
- deine Markenstimme (Situation → Perspektivwechsel → Impuls, „du"-Ansprache, keine KI-Verräter).

Ergebnis: 2–3 konkrete Content-Ideen mit Hook, Kernaussage und Format-Vorschlag (Text/Bild/Karussell/Video). Diese werden als neue Zeilen in der **Content-Pipeline** angelegt, Status „Entwurf", verknüpft mit der Research-Quelle über das Feld „Basiert auf Research". Der Workflow arbeitet jede Idee direkt weiter durch (Schritte 3-5) — willst du eine Idee gar nicht erst weiterverfolgen, archivierst du die Karte einfach, solange sie noch bei „Entwurf" steht.

**3. Drehbuch schreiben (Claude)**
Für jede Idee schreibt Claude mit [`prompts/02-drehbuch-post.md`](./prompts/02-drehbuch-post.md) den fertigen Post-Text (PLE-Struktur, kurze Absätze, kein Fachjargon) und — je nach Format — ein Sprecher-Skript fürs Video. Der Text landet im Feld „Text" der Pipeline-Zeile.

**4. Bild erzeugen (GPT Image 2)**
Claude formuliert dazu passend einen Bild-Prompt im DeskR-Look ([`prompts/03-bildprompt.md`](./prompts/03-bildprompt.md), basierend auf dem Master-Image-Prompt aus dem Branding-Skill: Burgundy/Salmon-Palette, Playfair/League Spartan). n8n schickt den Prompt an die GPT-Image-API und speichert die Bild-URL am Pipeline-Eintrag.

**5. Nur bei Video-Format: Ton + Bewegtbild**
- **ElevenLabs** vertont das Sprecher-Skript aus Schritt 3.
- **Seedance 2.5** baut daraus, zusammen mit dem generierten Bild, das fertige Video.
Bei reinen Text- oder Bild-Posts werden diese beiden Schritte übersprungen — das ist im Workflow eine Weiche (IF-Node) auf dem Feld „Format".

**6. Zur Freigabe stellen**
n8n setzt den Pipeline-Status auf „Zur Freigabe" und benachrichtigt dich (z. B. per Mail oder Slack — trag hier ein, was du bevorzugst).

**→ Dein Freigabe-Punkt:** Du liest den Text, schaust dir Bild/Video an, setzt Status auf „Freigegeben" (oder schreibst um, oder archivierst die Karte, wenn sie dich nicht überzeugt).

**7. Posten (Auto-Post)**
Ein Trigger prüft regelmäßig die Pipeline nach Einträgen mit Status „Freigegeben" und passendem „Geplantes Datum". Für den Start: **LinkedIn**. n8n veröffentlicht den Post, setzt Status auf „Gepostet" und trägt Zeitpunkt + Post-Link ein.

## Zyklus 2 — Vom Post zurück zur Idee (der Lern-Loop)

**8. Kennzahlen einsammeln (Analytics)**
Ein bis drei Tage nach dem Posten holt n8n die Post-Kennzahlen (Impressionen, Reaktionen, Kommentare, Shares) und legt eine neue Zeile in **Performance** an, verknüpft mit dem Pipeline-Eintrag.

**9. Bewerten (Claude)**
Mit [`prompts/04-lernanalyse.md`](./prompts/04-lernanalyse.md) vergleicht Claude die neuen Zahlen mit dem Durchschnitt der letzten Posts, vergibt „Top-Performer" / „Durchschnitt" / „Underperformer" und schreibt eine kurze, konkrete Erkenntnis ins Feld „Learning" — z. B. *„Posts mit einer konkreten Alltagsszene im Hook performen deutlich über Durchschnitt. Abstrakte Eröffnungssätze eher meiden."*

**10. Zurück in den Kreislauf**
Diese Erkenntnis wird automatisch als neuer Eintrag im **Research-Pool** angelegt (Kategorie „Learnings"). Beim nächsten Durchlauf von Schritt 2 fließt sie direkt in die nächste Ideengenerierung ein — der Kreis schließt sich, genau wie der gestrichelte Pfeil im Bild.

## Warum n8n und nicht „alles in einem Tool"

n8n übernimmt ausschließlich die **Orchestrierung** — es ruft die einzelnen Dienste (Claude, Apify, ElevenLabs, GPT Image 2, Seedance, Notion, LinkedIn) der Reihe nach auf, reicht Daten weiter und wartet auf deine Freigaben. Die eigentliche Kreativarbeit passiert bei Claude; das Gedächtnis liegt in Notion. So kannst du jeden Baustein einzeln austauschen, ohne das ganze System neu zu bauen.
