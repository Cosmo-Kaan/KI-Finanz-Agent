# 1. Basis-Image
# Wir verwenden ein schlankes Python 3.11-Image (ähnlich wie bei Streamlit)
FROM python:3.11-slim

# 2. Arbeitsverzeichnis
# Setzt das Hauptverzeichnis innerhalb des Containers
WORKDIR /app

# 3. System-Abhängigkeiten
# Kopiere die Liste der Systempakete
COPY packages.txt .
# Installiere die Systempakete (genau wie bei Streamlit Cloud)
RUN apt-get update && apt-get install -y --no-install-recommends $(cat packages.txt) && rm -rf /var/lib/apt/lists/*

# 4. Python-Abhängigkeiten
# Kopiere die requirements.txt und installiere sie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. App-Code kopieren
# Kopiere ALLES andere (backend_main.py, agent.py, etc.) in den Container
COPY . .

# 6. Port definieren
# Google Cloud Run erwartet standardmäßig den Port 8080
ENV PORT 8080
EXPOSE 8080

# 7. Startbefehl
# Dieser Befehl startet deinen Flask-Server (den "Motor"),
# NICHT die Streamlit-App.
# Startet den Server mit 4 Workern auf Port 8080 und zielt auf das 'app'-Objekt in der 'backend_main.py'-Datei
# Fügt Log-Flags hinzu: --log-level=debug (mehr Details) und --access-logfile=- / --error-logfile=- (leitet alle Logs an die Konsole/stderr um)
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8080", "--log-level=debug", "--access-logfile=-", "--error-logfile=-", "backend_main.py:app"]
