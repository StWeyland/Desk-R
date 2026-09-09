---
name: neue-impuls-seite
description: Legt eine neue Landingpage der Serie "KI im Klartext #N" (impuls-XX.html) in diesem Repo an — inklusive OG-Tags, Brevo-Formular und OG-Bild-Checkliste. Nutzen, wenn eine neue Impuls-/Lead-Magnet-Seite für Desk Revolution gebraucht wird.
---

# Neue Impuls-Seite anlegen

Jede Impuls-Seite ist ein eigenständiger Lead-Magnet-Funnel für die
LinkedIn-Serie „KI im Klartext #N“. Sie folgt immer demselben Aufbau:
Topbar mit Logo → `lp-body` (Tag, Headline, Sub, Bullets) → Brevo-Formular
zur Listeneintragung → OG-Meta-Tags für die Social-Vorschau.

`impuls-01.html` ist die vollständigste, sauberste Referenz (OG-Tags +
OG-Bild vorhanden, Formular-Button in Markenfarbe). Als Vorlage nehmen,
nicht `impuls-03.html` oder `impuls-12.html` (dort fehlen Teile, siehe
`.claude/CLAUDE.md`).

## Schritte

1. **Nummer bestimmen**: höchste bestehende `impuls-XX.html`-Nummer + 1
   (Lücken in der Nummerierung sind ok, nicht aus Versehen eine belegte
   Nummer wiederverwenden).
2. **Datei kopieren**: `impuls-01.html` als Basis für `impuls-XX.html`
   duplizieren.
3. **Title & Meta anpassen**:
   - `<title>` nach Muster `<Thema> — KI im Klartext #<N> · Desk Revolution`
   - `<meta name="description">`
   - `og:title`, `og:description` (eigenständiger, klickstarker Text — nicht
     nur den Title wiederholen)
   - `og:url` → `https://stweyland.github.io/Desk-R/impuls-XX.html`
   - `og:image` / `twitter:image` → `https://stweyland.github.io/Desk-R/og-impuls-XX.svg`
4. **OG-Bild erstellen**: `og-impuls-XX.svg` (und optional `.png`,
   1200×630) anlegen, analog zu `og-impuls-01.svg`. Ohne dieses Bild fällt
   die Social-Vorschau auf den Browser-Default zurück (siehe die
   bestehenden Lücken bei impuls-04/impuls-12).
5. **Content anpassen**: Tag, Headline, Sub, Bullets auf das neue Thema
   umschreiben. Ton: „du“-Ansprache, Situation → Perspektivwechsel →
   Impuls, keine Angstkommunikation, keine leeren Superlative.
6. **Brevo-Formular umverkabeln**: NIEMALS die kopierte `action`-URL des
   `<form>` unverändert lassen — die zeigt sonst auf die Liste der
   Ursprungsseite. Neue Formular-Action (und ggf. abweichende versteckte
   Felder) aus Brevo für die passende Liste holen. Success-/Error-Messages
   auf Deutsch und zum neuen Thema passend formulieren.
7. **Marke prüfen**: Farben/Schriften gegen die Skill `deskr-branding`
   abgleichen, nicht nur gegen `impuls-01.html` (das Repo nutzt aktuell
   noch die alte Palette, siehe `.claude/CLAUDE.md`).
8. **Manuell testen**: Datei lokal im Browser öffnen, Formular-Interaktion
   und (falls vorhanden) Light/Dark-Toggle prüfen. Es gibt kein
   automatisiertes Test-Setup in diesem Repo.
9. Vor dem Veröffentlichen optional den Subagent `landingpage-reviewer`
   gegenlesen lassen.
