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

    # --- GEÄNDERT: Logik für mehrere, benennbare Chats ---
    NUM_CHATS = 10
    
    # 1. Initialisiere 10 Chat-Objekte (Diktionäre), falls sie nicht existieren
    if "chats" not in st.session_state:
        # Jedes Objekt speichert jetzt seinen eigenen Namen und Verlauf
        st.session_state.chats = [
            {"name": f"Chat {i+1}", "history": []} for i in range(NUM_CHATS)
        ]
    
    # 2. Initialisiere den Index des aktiven Chats (unverändert)
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

        # --- GEÄNDERT: Chat-Auswahl liest jetzt custom Namen ---
        st.subheader("Meine Chats")
        
        # Holt die *aktuellen* Namen aus der session_state Struktur
        chat_option_names = [chat["name"] for chat in st.session_state.chats]
        
        # Zeigt die Radio-Buttons mit den custom Namen an
        selected_chat_name = st.radio(
            "Wählen Sie einen Chat:",
            options=chat_option_names,
            index=st.session_state.active_chat_index
        )
        
        # Aktualisiere den aktiven Chat-Index basierend auf dem Namen
        st.session_state.active_chat_index = chat_option_names.index(selected_chat_name)

        # --- NEU: Textfeld zum Umbenennen des AKTIVEN Chats ---
        active_chat = st.session_state.chats[st.session_state.active_chat_index]
        
        new_name = st.text_input(
            "Chat umbenennen:", 
            value=active_chat["name"] # Zeigt den aktuellen Namen an
        )
        
        if new_name != active_chat["name"]:
            # Wenn der Name geändert wurde, speichere ihn
            st.session_state.chats[st.session_state.active_chat_index]["name"] = new_name
            # Erzwinge einen Neustart des Scripts, damit die Radio-Liste aktualisiert wird
            st.rerun()

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
    # --- GEÄNDERT: Zeigt jetzt den custom Namen an ---
    st.caption(f"Aktuell in: **{st.session_state.chats[st.session_state.active_chat_index]['name']}** | ⚠️ Keine Finanzberatung")

    # --- GEÄNDERT: Angepasste Chat-Logik ---

    # 1. Holt den Verlauf für den *aktuell ausgewählten* Chat
    current_chat_history = st.session_state.chats[st.session_state.active_chat_index]["history"]

    # 2. Zeige alle bisherigen Nachrichten DIESES Chats an (unverändert)
    for message in current_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. Neue Chat-Eingabe (unten fixiert)
    if query := st.chat_input("Stellen Sie Ihre Finanzfrage..."):
        
        # 4. Zeige die User-Nachricht an und speichere sie im AKTIVEN Chat
        with st.chat_message("user"):
            st.markdown(query)
        # --- GEÄNDERT: Speichert im "history"-Teil des Chat-Objekts ---
        current_chat_history.append({"role": "user", "content": query})

        # 5. Rufe den Agenten auf und zeige die Antwort an
        with st.chat_message("assistant"):
            with st.spinner("Agent recherchiert und analysiert..."):
                try:
                    response = agent.run(query) 
                    st.markdown(response)
                    # 6. Speichere die Agenten-Antwort im AKTIVEN Chat
                    # --- GEÄNDERT: Speichert im "history"-Teil des Chat-Objekts ---
                    current_chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Ein Fehler ist aufgetreten: {e}"
                    st.error(error_msg)
                    current_chat_history.append({"role": "assistant", "content": error_msg})

# --- FINALE LOGIK: ZUERST PASSWORT PRÜFEN (Unverändert) ---
if check_password():
    run_app()
