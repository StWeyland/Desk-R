# Notion-Datenmodell — die drei Bausteine

Du kennst Notion noch nicht gut, deshalb hier erstmal das Wichtigste: **Eine Notion-„Datenbank" ist im Grunde eine Tabelle**, die du auch als Kanban-Board (Karten in Spalten) anschauen kannst. Jede Zeile/Karte ist ein einzelner Eintrag — eine Idee, ein Post, ein Kennzahlen-Datensatz. Spalten nennt Notion „Properties". Zwei Tabellen können über eine „Relation"-Spalte miteinander verknüpft werden — das ist der Klebstoff, der die drei Datenbanken unten zu einem System macht.

Alle drei existieren schon in deinem Workspace. Die ersten beiden (Research-Pool, Content-Pipeline) waren schon angelegt — ich habe sie unverändert gelassen bis auf eine kleine Ergänzung. Performance ist neu dazugekommen.

## 1. 🔎 Research-Pool
[Öffnen](https://app.notion.com/p/975d768936234fa29e81c4877a45663b)

Der Rohstoff-Speicher. Alles, was von außen kommt oder aus eigenen Ergebnissen gelernt wurde, landet hier zuerst.

| Feld | Typ | Bedeutung |
|---|---|---|
| Titel/Thema | Titel | Kurzbezeichnung des Fundstücks |
| Zusammenfassung | Text | Worum geht's, in 2–3 Sätzen |
| Kategorie | Mehrfachauswahl | KI-Tools · Trends · Konkurrenz · Studien · Zitate · **Learnings** *(neu hinzugefügt)* |
| Relevanz | Auswahl | Hoch / Mittel / Niedrig |
| Status | Auswahl | Neu / In Verwendung / Archiviert |
| Quelle/Link | URL | Woher stammt es |

**Neu:** die Kategorie „Learnings" — hier landen automatisch die Erkenntnisse aus deinen eigenen Post-Ergebnissen (siehe Performance unten). Damit fließt nicht nur externe Recherche, sondern auch dein eigenes Wissen über das, was bei deiner Zielgruppe funktioniert, in die nächste Ideenrunde ein.

## 2. 🗓️ Content-Pipeline
[Öffnen](https://app.notion.com/p/cb3d701d818a498cb5e39aa53dc3a894)

Dein Redaktionsplan. Jede Zeile ist ein Post auf seinem Weg von der Idee bis zur Veröffentlichung.

| Feld | Typ | Bedeutung |
|---|---|---|
| Titel/Hook | Titel | Arbeitstitel bzw. Eröffnungssatz |
| Status | Status | Entwurf → Zur Freigabe → **Freigegeben** → Geplant → Gepostet |
| Format | Auswahl | Text / Video / Bild / Karussell |
| Geplantes Datum | Datum | Wann soll's raus |
| Ziel-Profil | Auswahl | Steffi / Marcel / DeskR |
| Basiert auf Research | Relation → Research-Pool | Woher kam der Impuls |
| Text | Text | Der fertige Post-Text |
| Bild-URL | URL *(neu)* | Vom System generiertes Bild |
| Video-URL | URL *(neu)* | Nur bei Format Video befüllt |
| Sprecher-Skript | Text *(neu)* | Nur bei Format Video befüllt |
| Performance | Relation → Performance *(neu, kommt automatisch von der neuen Datenbank)* | Verweis auf die Kennzahlen nach dem Posten |

**Die beiden Freigabe-Status sind deine Kontrollpunkte:** „Zur Freigabe" heißt „das System wartet auf dein Okay". Erst wenn du selbst auf „Freigegeben" setzt, wird der Beitrag später automatisch gepostet.

## 3. 📊 Performance *(neu angelegt)*
[Öffnen](https://app.notion.com/p/340f93186c7e4db8a3ff092b08409ec9)

Ein Datensatz pro veröffentlichtem Post — die Zahlen, aus denen das System lernt.

| Feld | Typ | Bedeutung |
|---|---|---|
| Post | Titel | Bezug zum Pipeline-Eintrag |
| Content | Relation → Content-Pipeline | Welcher Post genau |
| Plattform | Auswahl | LinkedIn (Instagram/TikTok folgen später) |
| Gepostet am | Datum | |
| Impressionen / Reaktionen / Kommentare / Shares / Klicks | Zahl | Rohdaten aus der Plattform-Analyse |
| Engagement-Rate (%) | Zahl | wird von n8n berechnet |
| Performance-Kategorie | Auswahl | Top-Performer / Durchschnitt / Underperformer / Noch nicht bewertet |
| Learning | Text | Die konkrete Erkenntnis, die Claude daraus zieht |
| Ins Research-Pool übernommen | Checkbox | Haken, sobald das Learning als neuer Research-Pool-Eintrag existiert |

## So bewegst du dich als Erstes darin

1. Öffne die **Content-Pipeline** und wechsle oben zur Ansicht „Pipeline (Board)" — das zeigt dir die Posts als Karten in Spalten nach Status. Das ist deine tägliche Übersicht.
2. Wenn eine Karte bei „Zur Freigabe" liegt: reinklicken, Text/Bild lesen, entweder direkt in der Karte den Status auf „Freigegeben" ändern (Klick auf das Status-Feld) — oder Notizen reinschreiben, wenn etwas geändert werden soll.
3. Der **Research-Pool** und **Performance** brauchen im Alltag nichts von dir — die befüllt und liest das System automatisch. Schau nur rein, wenn dich interessiert, woher eine Idee kam oder wie ein alter Post performt hat.

Wenn du magst, gehe ich einmal live mit dir durch die Ansicht, bevor der erste automatische Durchlauf startet.
