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

    # --- Logik für mehrere, benennbare Chats (Unverändert) ---
    NUM_CHATS = 10
    
    if "chats" not in st.session_state:
        st.session_state.chats = [
            {"name": f"Chat {i+1}", "history": []} for i in range(NUM_CHATS)
        ]
    
    if "active_chat_index" not in st.session_state:
        st.session_state.active_chat_index = 0

    # --- Seitenleiste (Sidebar) ---
    with st.sidebar:
        st.title("Einstellungen")
        try:
            if st.secrets["GOOGLE_API_KEY"]:
                st.success("API Key erfolgreich geladen!", icon="✅")
        except KeyError:
            st.error("API Key nicht in Secrets gefunden!", icon="❌")

        st.subheader("Meine Chats")
        
        chat_option_names = [chat["name"] for chat in st.session_state.chats]
        
        selected_chat_name = st.radio(
            "Wählen Sie einen Chat:",
            options=chat_option_names,
            index=st.session_state.active_chat_index
        )
        
        st.session_state.active_chat_index = chat_option_names.index(selected_chat_name)
        active_chat = st.session_state.chats[st.session_state.active_chat_index]
        
        new_name = st.text_input(
            "Chat umbenennen:", 
            value=active_chat["name"]
        )
        
        if new_name != active_chat["name"]:
            st.session_state.chats[st.session_state.active_chat_index]["name"] = new_name
            st.rerun()
            
        # --- "Chat löschen"-Button ---
        st.markdown("---")
        if st.button("Aktuellen Chat löschen", type="primary"):
            # Setzt den Verlauf des aktiven Chats zurück
            st.session_state.chats[st.session_state.active_chat_index]["history"] = []
            # Setzt optional den Namen zurück
            st.session_state.chats[st.session_state.active_chat_index]["name"] = f"Chat {st.session_state.active_chat_index + 1}"
            st.rerun()

        # --- (Rest der Sidebar, unverändert) ---
        st.markdown("---") 
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
        # Initialisiert den Agenten (der jetzt 'gemini-2.5-flash' verwendet)
        agent = FinancialAgent()
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Agenten (Prüfen Sie den API Key): {e}")
        st.stop()

    # --- HAUPTSEITE (Titel) ---
    st.title("📊 Financial Research Agent")
    st.caption(f"Aktuell in: **{st.session_state.chats[st.session_state.active_chat_index]['name']}** | ⚠️ Keine Finanzberatung")

    # --- Chat-Logik (Unverändert) ---
    current_chat_history = st.session_state.chats[st.session_state.active_chat_index]["history"]

    for message in current_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if query := st.chat_input("Stellen Sie Ihre Finanzfrage..."):
        
        current_chat_history.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Agent recherchiert, sucht im Web und analysiert..."):
                try:
                    # Ruft die 'run'-Funktion auf, die jetzt auch googeln kann
                    response = agent.run(query) 
                    st.markdown(response)
                    current_chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Ein Fehler ist aufgetreten: {e}"
                    st.error(error_msg)
                    current_chat_history.append({"role": "assistant", "content": error_msg})

# --- FINALE LOGIK: ZUERST PASSWORT PRÜFEN (Unverändert) ---
if check_password():
    run_app()
