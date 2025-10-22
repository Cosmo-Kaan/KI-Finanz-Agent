#!/usr/bin/env python3
import streamlit as st
from agent import FinancialAgent  # Importiert agent.py

# --- HIER BEGINNT DIE PASSWORTSCHUTZ-LOGIK ---
def check_password():
    """Gibt True zurück, wenn das Passwort korrekt ist, sonst False."""
    
    # 1. Passwort aus den Streamlit Secrets holen
    try:
        # Holt das Passwort, das Sie in den Secrets gespeichert haben
        correct_password = st.secrets["APP_PASSWORD"]
    except KeyError:
        st.error("Fehler: APP_PASSWORD wurde nicht in den Streamlit Secrets gesetzt!")
        st.stop() # Hält die App an

    # 2. Passwort-Eingabefeld anzeigen
    password = st.text_input("Bitte geben Sie das Passwort ein:", type="password")

    # 3. Überprüfen
    if not password:
        st.stop()  # Stoppt die Ausführung, bis etwas eingegeben wird
    
    if password == correct_password:
        return True  # Passwort korrekt, App darf starten
    else:
        st.error("Passwort ist falsch.")
        return False # Passwort falsch, App stoppt

# --- Die eigentliche App-Logik (Ihr bisheriger Code) ---
def run_app():
    """Führt die Finanz-Agent-App aus, NACHDEM das Passwort korrekt war."""
    st.set_page_config(page_title="Financial Research Agent", layout="wide")
    
    # Der API-Key wird jetzt HIER geladen, nicht mehr in der Seitenleiste
    try:
        api_key_secret = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("Fehler: GOOGLE_API_KEY nicht in Streamlit Secrets gefunden!")
        st.stop()
    
    # Seitenleiste (Sidebar)
    with st.sidebar:
        st.title("Einstellungen")
        # Das alte API-Key-Feld ist jetzt weg.
        
        # Stattdessen können wir anzeigen, dass der Key geladen ist:
        if api_key_secret:
            st.success("API Key erfolgreich geladen!", icon="✅")

        # Badge (wie in der Anleitung)
        st.markdown(
            '<div style="background-color: #28a745; color: white; padding: 10px; border-radius: 5px; font-weight: bold; text-align: center;">KOSTENLOS!<br>$0/Monat</div>',
            unsafe_allow_html=True
        )
        st.subheader("Limits (Free Tier):")
        st.markdown("""
        * 15 Requests/Minute
        * 1M Tokens/Minute
        * 1.500 Requests/Tag
        """)
        st.caption("Für normale Nutzung völlig ausreichend!")
        
        st.subheader("Beispiel-Fragen")
        if st.button("Analyze Apple's financial health"):
            st.session_state.query = "Analyze Apple's financial health"
        if st.button("Compare Tesla and Ford"):
            st.session_state.query = "Compare Tesla and Ford"

    # Hauptseite
    st.title("📊 Financial Research Agent")
    st.markdown("Stellen Sie Fragen zu Aktien, Krypto oder Märkten. Der Agent analysiert automatisch die relevanten Daten und gibt Ihnen professionelle Insights – **komplett kostenlos!**")
    st.caption("Powered by Google Gemini 2.0 Flash ⚡")

    # Initialisierung des Agenten
    try:
        # Wir übergeben den Key, den wir aus den Secrets geholt haben
        # HINWEIS: Ihre agent.py MUSS dies unterstützen.
        # Ihre agent.py lädt den Key selbst
        # Daher ist die Zeile unten auskommentiert, da agent.py es selbst macht.
        # agent = FinancialAgent(api_key=api_key_secret) 
        
        # Stattdessen rufen wir es ohne Argument auf:
        agent = FinancialAgent()
        
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Agenten: {e}")
        st.stop()

    # Chat/Query-Eingabe
    if 'query' not in st.session_state:
        st.session_state.query = ""

    query = st.text_input("Ihre Anfrage (z.B. Analyze Apple's financial health):", 
                          value=st.session_state.query,
                          placeholder="z.B. Analyze Apple's financial health")
    
    if st.button("Analysieren"):
        if query:
            with st.spinner("Agent recherchiert und analysiert... (Dies kann 10-30 Sekunden dauern)"):
                try:
                    # Annahme: Ihr Agent hat eine 'run' Methode
                    response = agent.run(query) 
                    st.success("Analyse abgeschlossen!")
                    st.markdown(response)
                except Exception as e:
                    st.error(f"Ein Fehler ist aufgetreten: {e}")
        else:
            st.warning("Bitte geben Sie eine Anfrage ein.")

    # Footer
    st.markdown("---")
    st.caption("Gebaut mit 🤍 | Open Source | MIT Lizenz")
    st.caption("⚠️ Keine Finanzberatung - Konsultieren Sie einen Finanzberater")


# --- HAUPT-LOGIK ---

# 1. Prüfe das Passwort
if check_password():
    # 2. Wenn Passwort korrekt ist, starte die Hauptanwendung
    run_app()

