import os
import sys
import traceback
from flask import Flask, request, jsonify
from datetime import datetime
import google.generativeai as genai
from tavily import TavilyClient
from google.cloud import firestore

# --- 1. Konfiguration und Initialisierung ---

# Flask-App initialisieren
app = Flask(__name__)

# Umgebungsvariablen laden (wird von Cloud Run bereitgestellt)
# Wir brauchen den AUTH_TOKEN hier nicht mehr.
GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY')
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY')

# Firestore-Client initialisieren
# Die Umgebungsvariablen für das Service Account (FIRESTORE_...) 
# werden von der Google Cloud-Umgebung automatisch erkannt,
# wenn sie als Secrets bereitgestellt werden.
# Wir müssen den Client nur "nackt" initialisieren.
try:
    db = firestore.Client()
    print("✅ Firestore-Client erfolgreich initialisiert.")
except Exception as e:
    print(f"❌ SCHWERER FEHLER: Firestore-Client konnte nicht initialisiert werden: {e}")
    # Beende die Anwendung, wenn die DB nicht läuft
    sys.exit(f"Anwendung kann nicht ohne Firestore-Verbindung starten: {e}")

# Gemini-Modell konfigurieren
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    print("✅ Gemini-Modell erfolgreich konfiguriert.")
except Exception as e:
    print(f"❌ SCHWERER FEHLER: Gemini-Modell konnte nicht konfiguriert werden: {e}")
    sys.exit(f"Anwendung kann nicht ohne Gemini-Verbindung starten: {e}")

# Tavily-Client initialisieren
try:
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    print("✅ Tavily-Client erfolgreich initialisiert.")
except Exception as e:
    print(f"❌ WARNUNG: Tavily-Client konnte nicht initialisiert werden: {e}")
    # Wir fahren fort, da Tavily ein Fallback ist


# --- 2. Haupt-Endpunkt (Der "Motor") ---

@app.route('/run-analysis', methods=['POST'])
def run_analysis_endpoint():
    """
    Dieser Endpunkt wird vom Cloud Scheduler aufgerufen, um die 
    tägliche Finanzanalyse zu starten und in Firestore zu speichern.
    """
    
    print("🚀 /run-analysis Endpunkt aufgerufen. Starte Analyse...")

    # --- HIER WURDE DER AUTH_TOKEN SICHERHEITS-CHECK ENTFERNT ---
    # Wir verlassen uns jetzt auf die Google Cloud IAM-Authentifizierung,
    # die VOR diesem Code-Aufruf stattfindet.

    try:
        # --- 2. Agenten-Logik (aus agent.py) ---
        print("Schritt 1: Definiere Prompt für den Analysten...")
        prompt = """
        Du bist ein spezialisierter Hedgefonds-Analyst. 
        Deine Aufgabe ist es, die 5 wichtigsten täglichen Finanznachrichten zu identifizieren, 
        die den größten Einfluss auf die globalen Märkte (Aktien, Anleihen, Rohstoffe) haben könnten.

        Führe für jede dieser 5 Nachrichten eine prägnante Analyse durch:
        1.  **Zusammenfassung:** Was ist passiert?
        2.  **Marktauswirkung (Sentiment):** Ist dies bullish, bearish oder neutral für globale Märkte?
        3.  **Begründung:** Warum ist das so? Welche Sektoren oder Anlageklassen sind am stärksten betroffen?

        Strukturiere deine Antwort ausschließlich als Markdown.
        Beginne direkt mit '### Finanzanalyse des Tages'.
        """

        print("Schritt 2: Führe Tavily-Suche für 'top global financial news' durch...")
        try:
            # Versuche, aktuelle Nachrichten über Tavily zu erhalten
            search_context = tavily.search(query="top global financial news", search_depth="advanced")
            context_text = "\n".join([item['content'] for item in search_context['results']])
            final_prompt = f"{prompt}\n\nAktueller Kontext aus den Nachrichten:\n{context_text}"
            print("✅ Tavily-Suche erfolgreich, verwende erweiterten Kontext.")
        
        except Exception as e:
            # Fallback, wenn Tavily fehlschlägt
            print(f"⚠️ WARNUNG: Tavily-Suche fehlgeschlagen ({e}). Verwende Basis-Prompt.")
            final_prompt = prompt

        print("Schritt 3: Rufe Gemini-Modell für die Analyse auf...")
        response = model.generate_content(final_prompt)
        analysis_report = response.text
        print("✅ Gemini-Analyse erfolgreich abgeschlossen.")

        # --- 3. Speichern in Firestore ---
        print(f"Schritt 4: Speichere Bericht in Firestore (Sammlung: 'reports')...")
        
        # Erstelle ein neues Dokument mit einer Zeitstempel-basierten ID
        now = datetime.now()
        doc_id = now.strftime('%Y-%m-%d_%H-%M-%S')
        doc_ref = db.collection('reports').document(doc_id)
        
        # Daten für das Dokument vorbereiten
        report_data = {
            'timestamp': now,
            'report_content': analysis_report,
            'source': 'autonomer-finanz-agent-motor'
        }
        
        # Daten in Firestore schreiben
        doc_ref.set(report_data)
        print(f"✅ Bericht erfolgreich in Firestore unter ID {doc_id} gespeichert.")

        # Erfolgreiche Antwort an den Cloud Scheduler senden
        return jsonify({"status": "success", "message": "Analyse erfolgreich durchgeführt und gespeichert.", "doc_id": doc_id}), 200

    except Exception as e:
        # Fehlerbehandlung, falls irgendetwas im 'try'-Block fehlschlägt
        print(f"❌ FEHLER bei der Analyse-Ausführung: {e}")
        print(traceback.format_exc()) # Detailliertes Fehler-Logging
        
        # Fehlermeldung an den Cloud Scheduler senden
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 3. Start-Logik für Gunicorn (Produktion) ---

if __name__ == '__main__':
    # Diese Sektion wird von Gunicorn (Produktion) NICHT ausgeführt.
    # Sie ist nur für lokale Tests (z.B. `python backend_main.py`)
    print("Starte Flask-Server im lokalen Debug-Modus...")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
