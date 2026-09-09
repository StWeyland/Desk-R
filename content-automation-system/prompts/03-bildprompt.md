# Prompt: Bildprompt für GPT Image 2

Wird direkt nach dem Post-Drehbuch aufgerufen, mit `{{post_text}}` bzw. `{{ausgangssituation}}` als Kontext. Die Ausgabe geht 1:1 als Prompt an die GPT-Image-API weiter — deshalb hier bewusst als Bild-Prompt formuliert, nicht als Beschreibung.

Basiert auf dem DeskR Master Image Prompt (Creative-Director-Persona) aus dem Branding-Skill — verbindliche Farb- und Stilregeln, nicht verhandelbar.

---

Formuliere einen einzigen, direkt einsetzbaren Bildgenerierungs-Prompt (Englisch, wie bei GPT Image üblich) für folgenden Post-Kontext:

```
{{post_text}}
```

**Verbindliche DeskR-Bildsprache:**
- Farbpalette ausschließlich: Burgundy `#4A081E`, Cream `#FAF7F0`, Deep Salmon `#983D15`, Salmon `#FCA27A`, Pale Salmon `#FEC7AF`, Pale Salmon Tint `#FFF2EB`. Keine anderen Farben, kein altes Farbschema.
- Stimmung: ruhig, warm, souverän — nie hektisch, nie Tech-Glossy, nie generisches Corporate-Stock-Foto-Gefühl.
- Zeigt einen Alltagsmoment einer modernen Assistenz/Wissensarbeiterin — nie ein Stereotyp der „überforderten Sekretärin" und nie ein Sci-Fi-Roboter-Klischee für KI.
- Wenn Text im Bild vorkommt: nur kurze, prägnante Wörter, Font-Charakter passend zu Playfair Display (Headline) / League Spartan (Body) beschreiben, keine langen Sätze im Bild.
- Format: quadratisch oder 4:5 (LinkedIn-optimiert), keine extremen Formate.

**Ausgabeformat:** Nur der fertige Bild-Prompt als einzelner Fließtext-String, keine Erklärung, keine Anführungszeichen drumherum, keine Meta-Kommentare.
