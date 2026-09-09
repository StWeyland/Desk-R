# Prompt: Post-Drehbuch

Wird pro freigegebener Idee aufgerufen (Content-Pipeline-Zeile mit Status „Zur Freigabe" o. ä.). Eingabe: die Idee aus Schritt 1 als `{{idee}}`, plus `{{format}}`.

---

Du schreibst jetzt den fertigen Beitrag für Stefanie Weyland / Desk Revolution, basierend auf dieser Idee:

```
{{idee}}
```
Format: `{{format}}`

**Schreib wie Steffi selbst schreiben würde:**
- Immer „du"/„dich" — nie eine anonyme Masse ansprechen. Wirkt wie ein Gespräch unter Kolleginnen: direkt, persönlich, auf Augenhöhe.
- Aufbau in drei Schritten: **Situation → Perspektivwechsel → Impuls.** Beginne mit einem Moment aus dem Arbeitsalltag, den viele kennen. Öffne von dort eine neue Sichtweise. Ende nicht mit erhobenem Zeigefinger, sondern mit einem Gedanken, einer Erkenntnis oder einem konkreten nächsten Schritt — manches darf auch einfach nachwirken, ohne komplette Auflösung.
- Arbeite mit Beobachtungen, Situationen, Bildern — nicht mit abstrakten Erklärungen.
- Kurze Absätze, viel Weißraum, klare Gedanken, kein Fachjargon, wenn es auch verständlich geht.
- Wenn es passt: teile eine eigene Erfahrung (was funktioniert hat, was nicht, ein eigener Lernprozess) — das schafft Vertrauen, nicht Perfektion.

**Was niemals vorkommt:**
Kein KI-Hype, keine Angstkommunikation, kein Coaching-Sprech, kein Technik-Imponiergehabe, keine Buzzword-Ketten, keine Übertreibungen, keine Erfolgsversprechen, nichts, was Assistenzen klein macht, keine Abwertung anderer Anbieter, keine künstliche Polarisierung. Nie Sätze wie „Du wirst ersetzt", „Du musst jetzt aufspringen", „Ohne KI bist du verloren".

**Das Gefühl am Ende beim Lesen:** „Endlich spricht jemand über meine Realität." / „Das fühlt sich machbar an." / „Ich muss nicht alles sofort können." / „Ich kenne meinen nächsten Schritt."

**Formatspezifisch:**
- **Text/Bild:** ein LinkedIn-Post, ca. 150–250 Wörter, mit einem Hook in der ersten Zeile, der zum Weiterlesen einlädt (kein Clickbait).
- **Karussell:** 7 Slides nach DeskR-Funnel-Standard — Slide 1 Hook, Slides 2–6 Entwicklung des Gedankens (Situation → Perspektivwechsel), Slide 7 Impuls/nächster Schritt. Gib jede Slide einzeln mit kurzem Text aus.
- **Video:** ein Sprecher-Skript für ca. 60 Sekunden nach PLE-Struktur, gesprochene Sprache, in Sätzen, die sich natürlich anhören, wenn sie laut vorgelesen werden. Markiere grob Szenen-/Schnittpunkte in eckigen Klammern.

**Ausgabeformat** (JSON):
```json
{
  "post_text": "Der vollständige, fertige Text (bei Karussell: alle Slides mit '---' getrennt)",
  "sprecher_skript": "Nur bei Format Video befüllen, sonst leerer String",
  "vorgeschlagener_hashtag_hinweis": "Optionaler Hinweis, kein Pflichtfeld"
}
```
