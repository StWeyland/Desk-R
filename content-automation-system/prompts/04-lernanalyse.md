# Prompt: Lern-Analyse

Wird nach dem Einsammeln der Kennzahlen aufgerufen (Schritt 9 im Lern-Loop). Eingabe: die neuen Zahlen `{{neue_kennzahlen}}`, der zugehörige Post-Text `{{post_text}}` und der Durchschnitt der letzten ca. 10 Posts `{{durchschnittswerte}}`.

---

Du analysierst die Performance eines einzelnen LinkedIn-Posts von Desk Revolution und ziehst daraus eine konkrete, wiederverwendbare Erkenntnis für zukünftige Content-Ideen.

Post-Text:
```
{{post_text}}
```

Kennzahlen dieses Posts:
```
{{neue_kennzahlen}}
```

Durchschnittswerte der letzten Posts (zum Vergleich):
```
{{durchschnittswerte}}
```

**Deine Aufgabe:**

1. Berechne die Engagement-Rate dieses Posts: `(Reaktionen + Kommentare + Shares) / Impressionen * 100`.
2. Ordne den Post ein: **Top-Performer** (deutlich über Durchschnitt, ab ca. +30 %), **Durchschnitt** (im üblichen Bereich, +/-30%), oder **Underperformer** (deutlich darunter, ab ca. -30 %).
3. Formuliere EINE konkrete, handlungsleitende Erkenntnis — kein allgemeines Statement wie „Posts mit Emotionen funktionieren gut", sondern etwas, das sich direkt auf die nächste Ideengenerierung anwenden lässt. Beispiele für die Art von Aussage, die gebraucht wird:
   - „Ein konkreter Alltagsmoment im ersten Satz (statt einer allgemeinen These) korreliert hier mit höherem Engagement."
   - „Posts, die eine eigene Unsicherheit von Steffi zeigen, erzeugen mehr Kommentare als reine Beobachtungs-Posts."
   - „Karussells zu Prozessthemen performen bisher schwächer als Einzelbild-Posts zu Rollenbild-Themen — evtl. Format nicht zum Thema passend."
4. Bleib beschreibend und ehrlich, nicht beschönigend. Ein Underperformer ist ein valides, nützliches Ergebnis — keine Enttäuschung, die kaschiert werden muss. Wenn die Datenlage (z. B. nur 1-2 Vergleichswerte) noch keine verlässliche Aussage zulässt, sag das offen, statt eine Erkenntnis zu erfinden.

**Ausgabeformat** (JSON):
```json
{
  "engagement_rate": 0.0,
  "performance_kategorie": "Top-Performer | Durchschnitt | Underperformer",
  "learning": "Die eine konkrete Erkenntnis, max. 2 Sätze",
  "research_pool_eintrag": {
    "titel_thema": "Kurztitel für den neuen Research-Pool-Eintrag",
    "zusammenfassung": "Gleicher Inhalt wie 'learning', als eigenständiger Eintrag formuliert"
  }
}
```
