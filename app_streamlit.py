#!/usr/bin/env python3
import streamlit as st
from agent import FinancialAgent  # Importiert agent.py

# --- PASSWORTSCHUTZ (Unverändert) ---
def check_password():
    try:
        correct_password = st.secrets["APP_PASSWORD"]
    except KeyError:
        st.error("Fehler: APP_PASSWORD wurde nicht in den Streamlit Secrets gesetzt!")
        st.stop() 

    password = st.text_input("Bitte geben Sie das Passwort ein:", type="password")

    if not password:
        st.stop()  
    
    if password == correct_password:
        return True
    else:
        st.error("Passwort ist falsch.")
        return False

# --- HAUPT-ANWENDUNG ---
def run_app():
    st.set_page_config(page_title="Financial Research Agent", layout="wide")

    # --- Seitenleiste (Sidebar) ---
    with st.sidebar:
        st.title("Einstellungen")
        try:
            if st.secrets["GOOGLE_API_KEY"]:
                st.success("API Key erfolgreich geladen!", icon="✅")
        except KeyError:
            st.error("API Key nicht in Secrets gefunden!", icon="❌")

        # Badge
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
        
        # HINWEIS: Die Beispiel-Fragen-Buttons wurden entfernt,
        # da wir jetzt st.chat_input() verwenden.

    # --- Agent initialisieren ---
    try:
        agent = FinancialAgent()
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Agenten (Prüfen Sie den API Key): {e}")
        st.stop()

    # --- HAUPTSEITE (Titel) ---
    st.title("📊 Financial Research Agent")
    st.caption("Powered by Google Gemini 2.0 Flash ⚡ | ⚠️ Keine Finanzberatung")

    # --- NEU: Chat-Logik ---

    # 1. Initialisiere den Chat-Verlauf im Session State, falls er nicht existiert
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 2. Zeige alle bisherigen Nachrichten an
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Neue Chat-Eingabe (ersetzt st.text_input und st.button)
    # Die Eingabebox ist jetzt am unteren Rand fixiert.
    if query := st.chat_input("Stellen Sie Ihre Finanzfrage..."):
        
        # 4. Zeige die User-Nachricht an und speichere sie
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.messages.append({"role": "user", "content": query})

        # 5. Rufe den Agenten auf und zeige die Antwort an
        with st.chat_message("assistant"):
            with st.spinner("Agent recherchiert und analysiert..."):
                try:
                    # Ruft die run-Funktion Ihres Agenten auf
                    response = agent.run(query) 
                    st.markdown(response)
                    # 6. Speichere die Agenten-Antwort
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Ein Fehler ist aufgetreten: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

# --- FINALE LOGIK: ZUERST PASSWORT PRÜFEN ---
if check_password():
    run_app()

