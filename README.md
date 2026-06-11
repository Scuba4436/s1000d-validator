# S1000D Validator (ASD S1000D Issues 2.3, 3.0, 4.0.1, 4.1, 4.2 und 5.0)

Eine moderne, Streamlit-basierte Web-Applikation zur schnellen und automatisierten Validierung von XML-Dateien. Die App ist darauf ausgelegt, XML-Dateien auf korrekte Syntax und gegen spezifische XSD-Schemas (insbesondere aus dem offiziellen ASD S1000D Issues 2.3, 3.0, 4.0.1, 4.1, 4.2 und 5.0 Schema Package) zu prüfen.

## 🚀 Funktionen

- **Drag & Drop Upload**: Gleichzeitiges Hochladen und Prüfen von hunderten XML-Dateien.
- **Automatische Schema-Erkennung**: Die App analysiert das Root-Element (`xsi:noNamespaceSchemaLocation`, `xsi:schemaLocation` oder Namespaces), um vollautomatisch das passende XSD-Schema im lokalen Verzeichnis zu finden.
- **Detaillierte Validierung**: Prüft zunächst auf "Well-formedness" (XML-Syntax) und führt anschließend eine strenge Schema-Validierung (XSD) via `lxml` durch.
- **Integrierter XML-Viewer**: Klickbare Dateinamen in der Ergebnistabelle öffnen die entsprechende XML-Datei in einem neuen Tab – sauber strukturiert ("beautified"), mit Syntax-Highlighting und Zeilennummern.
- **Vibrant Dark Mode UI**: Modernes Dashboard mit dynamischen Schatten, Hover-Effekten und Neon-Akzentfarben für direktes visuelles Feedback.
- **Excel-Export**: Lade die gesamten Validierungsergebnisse mit einem Klick als übersichtliche `.xlsx`-Datei herunter.
- **Dynamische Tabellengröße**: Passe die Anzahl der gleichzeitig sichtbaren Zeilen in der Ergebnistabelle flexibel an.

---

## 🛠️ Bedienung

1. **App starten**: Führe die App wie unten beschrieben aus. Es öffnet sich automatisch dein Browser.
2. **Validieren**: Ziehe deine XML-Dateien in das gestrichelte Feld. Die Validierung startet sofort.
3. **Ergebnisse prüfen**:
   - Die Zusammenfassung zeigt dir die Erfolgsquote auf einen Blick.
   - In der Detailtabelle siehst du genaue Fehlermeldungen inkl. Zeilennummer, falls eine Datei ungültig ist.
   - Ein Klick auf den Dateinamen öffnet die XML in einer gut lesbaren Ansicht zur direkten Fehlersuche.
4. **Exportieren**: Mit dem Button "Ergebnisse als Excel (.xlsx)" oben rechts über der Tabelle kannst du den Bericht sichern.

---

## 💻 Installation & Start

### Voraussetzungen
- Installiertes **Python 3.9** (oder neuer)
- Git (optional, zum Klonen)

---

### Windows

Öffne die Kommandozeile (`cmd` oder PowerShell), navigiere in den Projektordner und führe folgende Befehle aus:

1. **Virtuelle Umgebung erstellen:**
   ```cmd
   python -m venv .venv
   ```
2. **Virtuelle Umgebung aktivieren:**
   ```cmd
   .venv\Scripts\activate
   ```
3. **Abhängigkeiten installieren:**
   ```cmd
   pip install -r requirements.txt
   ```
4. **Applikation starten:**
   ```cmd
   python -m streamlit run validator.py
   ```

---

### Linux / macOS

Öffne dein Terminal, navigiere in den Projektordner und führe folgende Befehle aus:

1. **Virtuelle Umgebung erstellen:**
   ```bash
   python3 -m venv .venv
   ```
2. **Virtuelle Umgebung aktivieren:**
   - Standard (Bash/Zsh):
     ```bash
     source .venv/bin/activate
     ```
   - Fish-Shell:
     ```bash
     source .venv/bin/activate.fish
     ```
3. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Applikation starten:**
   ```bash
   python -m streamlit run validator.py
   ```

---

### Hinweise zur Fehlerbehebung
- **Kein passendes Schema gefunden?** Prüfe, ob die `.xsd`-Datei im Ordner `schemas/` im entsprechenden Unterordner für die S1000D Version liegt. Der Dateiname muss mit dem im XML-Root-Element referenzierten Schema übereinstimmen.
- **Port belegt?** Falls Port `8501` bereits genutzt wird, sucht Streamlit automatisch den nächsten freien Port (z. B. `8502`). Die Konsolenausgabe zeigt dir immer die richtige lokale URL an.
