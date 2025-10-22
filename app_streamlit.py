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

    # --- NEU: Logik für mehrere Chats ---
    NUM_CHATS = 10
    
    # 1. Initialisiere 10 leere Chat-Verläufe, falls sie nicht existieren
    if "all_chats" not in st.session_state:
        # Erstellt eine Liste, die 10 leere Listen enthält: [ [], [], ..., [] ]
        st.session_state.all_chats = [[] for _ in range(NUM_CHATS)]
    
    # 2. Initialisiere den Index des aktiven Chats
    if "active_chat_index" not in st.session_state:
        st.session_state.active_chat_index = 0 # Startet mit "Chat 1"

    # --- Seitenleiste (Sidebar) ---
    with st.sidebar:
        st.title("Einstellungen")
        try:
            if st.secrets["GOOGLE_API_KEY"]:
                st.success("API Key erfolgreich geladen!", icon="✅")
        except KeyError:
            st.error("API Key nicht in Secrets gefunden!", icon="❌")

        # --- NEU: Chat-Auswahl ---
        st.subheader("Meine Chats")
        # Erstellt die Namen, z.B. "Chat 1", "Chat 2", ...
        chat_option_names = [f"Chat {i+1}" for i in range(NUM_CHATS)]
        
        # Zeigt die Radio-Buttons an
        selected_chat_name = st.radio(
            "Wählen Sie einen Chat:",
            options=chat_option_names,
            index=st.session_state.active_chat_index
        )
        
        # Aktualisiere den aktiven Chat-Index basierend auf der Auswahl
        st.session_state.active_chat_index = chat_option_names.index(selected_chat_name)
        
        # --- (Rest der Sidebar, unverändert) ---
        st.markdown("---") # Trennlinie
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

    # --- Agent initialisieren (Unverändert) ---
    try:
        agent = FinancialAgent()
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Agenten (Prüfen Sie den API Key): {e}")
        st.stop()

    # --- HAUPTSEITE (Titel) ---
    st.title("📊 Financial Research Agent")
    st.caption(f"Aktuell in: **{selected_chat_name}** | ⚠️ Keine Finanzberatung")

    # --- Angepasste Chat-Logik ---

    # 1. Holt den Verlauf für den *aktuell ausgewählten* Chat
    current_chat_history = st.session_state.all_chats[st.session_state.active_chat_index]

    # 2. Zeige alle bisherigen Nachrichten DIESES Chats an
    for message in current_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Neue Chat-Eingabe (unten fixiert)
    if query := st.chat_input("Stellen Sie Ihre Finanzfrage..."):
        
        # 4. Zeige die User-Nachricht an und speichere sie im AKTIVEN Chat
        with st.chat_message("user"):
            st.markdown(query)
        # --- NEU: Speichert im richtigen Chat-Slot ---
        current_chat_history.append({"role": "user", "content": query})

        # 5. Rufe den Agenten auf und zeige die Antwort an
        with st.chat_message("assistant"):
            with st.spinner("Agent recherchiert und analysiert..."):
                try:
                    response = agent.run(query) 
                    st.markdown(response)
                    # 6. Speichere die Agenten-Antwort im AKTIVEN Chat
                    # --- NEU: Speichert im richtigen Chat-Slot ---
                    current_chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Ein Fehler ist aufgetreten: {e}"
                    st.error(error_msg)
                    # --- NEU: Speichert im richtigen Chat-Slot ---
                    current_chat_history.append({"role": "assistant", "content": error_msg})

# --- FINALE LOGIK: ZUERST PASSWORT PRÜFEN (Unverändert) ---
if check_password():
    run_app()
