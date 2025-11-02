import os
import json
import google.oauth2.service_account
from google.cloud import firestore
from flask import Flask, request, jsonify
from agent import FinancialAgent  # Importiert deinen bestehenden Analysten
import datetime

# --- Initialisierung ---

# Erstellt die Flask-App
app = Flask(__name__)

# Lade Secrets aus Umgebungsvariablen (so funktioniert Cloud Run)
try:
    # Lade den Auth-Token, den wir später für den "Wecker" brauchen
    AUTH_TOKEN = os.getenv("AUTH_TOKEN")
    if not AUTH_TOKEN:
        raise ValueError("AUTH_TOKEN nicht in Umgebungsvariablen gefunden!")

    # Baue die Firestore-Credentials aus Umgebungsvariablen
    key_dict = {
        "type": "service_account",
        "project_id": os.getenv("FIRESTORE_PROJECT_ID"),
        "private_key_id": os.getenv("FIRESTORE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIRESTORE_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("FIRESTORE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIRESTORE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("FIRESTORE_CLIENT_CERT_URL")
    }

    credentials = google.oauth2.service_account.Credentials.from_service_account_info(key_dict)

    # Initialisiere die DB-Verbindung (mit der richtigen Datenbank-ID)
    db = firestore.Client(
        credentials=credentials,
        database="finanz-agent-db" 
    )

    # Initialisiere deinen Analysten-Agenten
    # (agent.py nutzt auch os.getenv() für GOOGLE_API_KEY und TAVILY_API_KEY)
    analyst = FinancialAgent()
    print("✅ Agent und Firestore erfolgreich initialisiert.")

except Exception as e:
    print(f"❌ Fehler bei der Initialisierung: {e}")
    # Beende die App nicht, damit wir den Fehler im Log sehen können
    analyst = None 
    db = None


# --- Der "Wecker"-Endpunkt ---

@app.route('/run-analysis', methods=['POST'])
def run_analysis():
    """
    Diese Funktion wird vom Google Cloud Scheduler ("Wecker") aufgerufen.
    Sie führt die Analyse aus und speichert sie in Firestore.
    """

    # --- 1. Sicherheit ---
    # Überprüft, ob der "Wecker" den richtigen geheimen Token mitschickt
    request_token = request.headers.get('Authorization')
    if request_token != f"Bearer {AUTH_TOKEN}":
        print(f"❌ Fehler: Ungültiger Auth-Token. Erhalten: {request_token}")
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if not analyst or not db:
        print("❌ Fehler: Agent oder DB wurden nicht initialisiert.")
        return jsonify({"status": "error", "message": "Agent not initialized"}), 500

    print("Auth-Token korrekt. Starte autonome Analyse...")

    # --- 2. Ausführung ---
    try:
        # Definiere den "Auftrag" für den Agenten
        analysis_query = "Erstelle einen zusammenfassenden Bericht über die Marktlage und die wichtigsten Nachrichten für Bitcoin und Ethereum für die vergangene Woche."

        # Lasse den Agenten laufen (kostet 1x Google & 1x Tavily API)
        report_content = analyst.run(analysis_query)

        # --- 3. Speichern ---
        # Speichere den Bericht in einer NEUEN Sammlung in Firestore
        report_data = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "query": analysis_query,
            "report": report_content
        }

        # Fügt ein neues Dokument hinzu, Firestore generiert die ID
        doc_ref = db.collection("reports").add(report_data)

        print(f"✅ Bericht erfolgreich erstellt und in Firestore gespeichert: {doc_ref[1].id}")
        return jsonify({"status": "success", "report_id": doc_ref[1].id}), 200

    except Exception as e:
        print(f"❌ Fehler während der Analyse-Ausführung: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Startet den Server ---
# if __name__ == "__main__":
#    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
# Gunicorn startet die 'app' jetzt direkt, dieser Block wird nicht mehr benötigt.
