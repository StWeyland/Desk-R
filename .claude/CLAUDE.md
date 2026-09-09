# Desk-R — Projektkontext für Claude Code

## Was das hier ist
Die statische Website von Desk Revolution, gehostet über GitHub Pages unter
`https://stweyland.github.io/Desk-R/`. Kein Build-Prozess, kein Framework,
kein `package.json`. Jede Seite ist eine einzelne, in sich geschlossene
HTML-Datei mit Inline-CSS im `<head>`.

## Seitentypen
- **`index.html`** — Hauptseite. Dark/Light-Theme über `data-theme="dark|light"`
  am `<html>`-Tag plus CSS-Variablen (`--bg`, `--accent`, `--text`, …). Die
  Toggle-Logik nicht ohne konkreten Grund anfassen.
- **`impuls-XX.html`** — Lead-Magnet-Landingpages der Serie „KI im Klartext #N“.
  Aufbau: Topbar mit Logo, `lp-body` (Tag → Headline → Sub → Bullets), Brevo-
  Formular (sibforms.com) zur Listeneintragung, OG-Meta-Tags fürs Teilen.
- **Kunden-Landingpages** (z. B. `cashmor-landingpage-gehalt.html`) — eigenes
  Branding des Kunden (eigene Farben, eigene Schrift), bewusst NICHT im
  DeskR-Look. Nicht versehentlich an die DeskR-Marke angleichen.
- **`og-impuls-XX.svg` / `.png`** — Open-Graph-Vorschaubilder, 1200×630, je
  eins pro Impuls-Seite.

## Marke & Design
Die verbindliche Markenreferenz (Farben, Schriften, Logo-Regeln, Funnel-
Aufbau) liegt in der Skill `deskr-branding`. Vor jeder gestalterischen
Änderung an DeskR-eigenen Seiten dort nachlesen und den Qualitätscheck am
Ende der Referenz vor Auslieferung anwenden.

⚠️ **Bekannte Abweichung:** `index.html` und die `impuls-*.html`-Seiten
nutzen aktuell noch das alte Farbschema (Sage `#8fa99b`, Waldgrün `#41584c`).
Der aktuelle Brand-Standard verlangt Burgundy `#4A081E` / Cream `#FAF7F0` /
Deep Salmon `#983D15` / Salmon `#FCA27A` / Pale Salmon `#FEC7AF`. Beim
Anfassen einer bestehenden Seite kurz mit Steffi klären, ob im selben Zug
auf die neue Palette migriert wird, statt die alte Farbe einfach
fortzuschreiben.

Schriften bei DeskR-eigenen Seiten: **Playfair Display** (Headlines/Logo),
**League Spartan** (Body/Interface). Nie Inter, Roboto, Arial oder Bebas
Neue als Display-Schrift auf DeskR-Seiten (Kunden-Landingpages sind davon
ausgenommen, siehe oben).

## Konventionen
- Ein HTML-File = eine Seite, komplett self-contained. Kein externes
  CSS-/JS-Bundle, keine Build-Schritte.
- Impuls-Seiten sind fortlaufend nummeriert; Lücken (bislang: 01, 03, 04, 12)
  sind normal — nicht rückwirkend auffüllen.
- `og:url` muss exakt dem echten GitHub-Pages-Pfad entsprechen:
  `https://stweyland.github.io/Desk-R/<datei>.html`.
- Jede Brevo-Liste hat ihre eigene Formular-`action`-URL. Beim Duplizieren
  einer Impuls-Seite die `<form action="...">` und alle verstecken Felder
  auf die neue Liste umstellen — sonst landen Leads in der falschen Liste.

## Bekannte Stolperfallen
- `impuls-04.html` und `impuls-12.html` haben aktuell **keine** OG-Meta-Tags
  bzw. kein OG-Bild — die Social-Vorschau fällt auf den Browser-Default
  zurück. Beim nächsten Anfassen ergänzen.
- Das Formular in `impuls-03.html` nutzt noch Brevo-Default-Farben statt
  Markenfarbe beim Button — beim nächsten Anfassen angleichen.
- Es gibt kein Test- oder Lint-Setup. Vor dem Commit die Datei lokal im
  Browser öffnen (direktes Öffnen reicht, kein Server nötig) und
  Light/Dark-Toggle sowie Formular-Interaktion manuell prüfen.

## Arbeiten in diesem Repo
- Änderungen direkt in der jeweiligen HTML-Datei, keine Build-Schritte nötig.
- Für neue Impuls-Seiten: Skill `neue-impuls-seite` nutzen (Vorlage +
  Checkliste, verhindert die oben genannten Lücken).
- Für eine zweite Meinung vor dem Veröffentlichen: Subagent
  `landingpage-reviewer` prüft Marke, OG-Tags, Formular-Verkabelung und
  Barrierefreiheit unabhängig vom Hauptkontext.
