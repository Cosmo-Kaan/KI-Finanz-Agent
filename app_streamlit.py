#!/usr/bin/env python3
import streamlit as st
# Annahme: Dein Agenten-Code ist immer noch in 'agent.py'
from agent import FinancialAgent 
import google.oauth2.service_account
from google.cloud import firestore
import json

# --- Firestore Initialisierung ---
try:
    key_dict = {
        "type": "service_account",
        "project_id": st.secrets["FIRESTORE_PROJECT_ID"],
        "private_key_id": st.secrets["FIRESTORE_PRIVATE_KEY_ID"],
        "private_key": st.secrets["FIRESTORE_PRIVATE_KEY"].replace('\\n', '\n'), 
        "client_email": st.secrets["FIRESTORE_CLIENT_EMAIL"],
        "client_id": st.secrets["FIRESTORE_CLIENT_ID"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": st.secrets["FIRESTORE_CLIENT_CERT_URL"]
    }
    credentials = google.oauth2.service_account.Credentials.from_service_account_info(key_dict)
    db = firestore.Client(credentials=credentials)
    st.sidebar.success("Firestore verbunden!", icon="🔥") 
except Exception as e:
    st.error(f"Fehler bei Firestore-Verbindung (Prüfe Secrets!): {e}") 
    st.stop()

# --- Passwortschutz (Unverändert) ---
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
    st.error("Passwort ist falsch.")
    return False

# --- Datenbank-Funktionen ---
USER_ID = "default_user" 
NUM_CHATS = 10

# --- HIER IST DIE ÄNDERUNG ---
@st.cache_resource # Cache die Funktion
def load_chats_from_db():
    """Lädt Chats aus Firestore. Erstellt initiale Struktur, falls nicht vorhanden."""
    print("Lade Chats aus Firestore...")
    user_doc_ref = db.collection("users").document(USER_ID)
    chats_ref = user_doc_ref.collection("chats").order_by("index")
    
    chats = [None] * NUM_CHATS
    found_chats = False

    # NEU: Prüfen, ob das Nutzer-Dokument existiert, bevor wir lesen
    user_doc = user_doc_ref.get()
    if not user_doc.exists:
        print(f"Nutzer-Dokument '{USER_ID}' existiert nicht. Erstelle initiale Struktur...")
        # Erstelle leere Chats
        chats = [{"name": f"Chat {i+1}", "history": [], "index": i} for i in range(NUM_CHATS)]
        # Speichere die initialen leeren Chats in der DB
        batch = db.batch()
        # Erstelle das (leere) Nutzerdokument, damit die Sammlung erstellt werden kann
        batch.set(user_doc_ref, {}) 
        for i, chat in enumerate(chats):
            doc_ref = chats_ref.document(f"chat_{i}") # Pfad zur Untersammlung
            batch.set(doc_ref, chat)
        batch.commit()
        print("Initiale Struktur erstellt.")
        return chats # Gibt die frisch erstellten Chats zurück
    else:
        # Nutzer-Dokument existiert, versuche Chats zu lesen
        print(f"Nutzer-Dokument '{USER_ID}' gefunden. Lese Chats...")
        for doc in chats_ref.stream():
            chat_data = doc.to_dict()
            chat_index = chat_data.get("index")
            if chat_index is not None and 0 <= chat_index < NUM_CHATS:
                if "history" not in chat_data or not isinstance(chat_data["history"], list):
                    chat_data["history"] = []
                chats[chat_index] = chat_data 
                found_chats = True

        # Wenn das Nutzer-Dokument existiert, aber keine Chat-Dokumente gefunden wurden
        if not found_chats:
            print("Nutzer-Dokument existiert, aber keine Chats gefunden. Erstelle initiale Chats...")
            chats = [{"name": f"Chat {i+1}", "history": [], "index": i} for i in range(NUM_CHATS)]
            batch = db.batch()
            for i, chat in enumerate(chats):
                doc_ref = chats_ref.document(f"chat_{i}")
                batch.set(doc_ref, chat)
            batch.commit()
            print("Initiale Chats erstellt.")
        else:
             # Fülle eventuell fehlende Slots auf
            for i in range(NUM_CHATS):
                if chats[i] is None:
                    chats[i] = {"name": f"Chat {i+1}", "history": [], "index": i}
                    # Optional: Fehlenden Chat auch in DB speichern
                    # doc_ref = chats_ref.document(f"chat_{i}")
                    # doc_ref.set(chats[i])
            print("Chats erfolgreich geladen.")

    return chats
# --- ENDE DER ÄNDERUNG ---

# (Restliche DB-Funktionen save_chat_to_db etc. bleiben unverändert)
def save_chat_to_db(chat_index, chat_data):
    """Speichert ein einzelnes Chat-Objekt (Name und Verlauf) in Firestore."""
    print(f"Speichere Chat {chat_index} in Firestore...")
    doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{chat_index}")
    doc_ref.set(chat_data, merge=True) 

def save_chat_name_to_db(chat_index, new_name):
    """Speichert nur den neuen Namen eines Chats in Firestore."""
    print(f"Speichere neuen Namen für Chat {chat_index}: {new_name}")
    doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{chat_index}")
    doc_ref.update({"name": new_name})

def delete_chat_history_in_db(chat_index):
    """Löscht nur den Verlauf ('history') eines Chats in Firestore."""
    print(f"Lösche Verlauf von Chat {chat_index}...")
    doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{chat_index}")
    doc_ref.update({"history": []})


# --- HAUPT-ANWENDUNG (Rest unverändert) ---
def run_app():
    st.set_page_config(page_title="Financial Research Agent", layout="wide")

    st.session_state.chats = load_chats_from_db()
    
    if "active_chat_index" not in st.session_state:
        st.session_state.active_chat_index = 0

    with st.sidebar:
        st.title("Einstellungen")
        try:
            if st.secrets["GOOGLE_API_KEY"]:
                st.success("Google API Key geladen!", icon="✅")
            if st.secrets["TAVILY_API_KEY"]:
                st.success("Tavily API Key geladen!", icon="✅")
        except KeyError:
            st.warning("Einer der API Keys fehlt in den Secrets!", icon="⚠️")

        st.subheader("Meine Chats")
        chat_option_names = [chat["name"] for chat in st.session_state.chats]
        selected_chat_name = st.radio(
            "Wählen Sie einen Chat:",
            options=chat_option_names,
            index=st.session_state.active_chat_index,
            key=f"radio_{st.session_state.active_chat_index}" 
        )
        
        new_active_index = chat_option_names.index(selected_chat_name)
        if new_active_index != st.session_state.active_chat_index:
             st.session_state.active_chat_index = new_active_index
             st.rerun() 
        
        active_chat_data = st.session_state.chats[st.session_state.active_chat_index]

        new_name = st.text_input(
            "Chat umbenennen:", 
            value=active_chat_data["name"],
            key=f"name_input_{st.session_state.active_chat_index}" 
        )
        if new_name != active_chat_data["name"] and new_name.strip(): 
            st.session_state.chats[st.session_state.active_chat_index]["name"] = new_name.strip()
            save_chat_name_to_db(st.session_state.active_chat_index, new_name.strip())
            st.rerun() 

        st.markdown("---")
        if st.button("Aktuellen Chat löschen", type="primary"):
            st.session_state.chats[st.session_state.active_chat_index]["history"] = []
            delete_chat_history_in_db(st.session_state.active_chat_index)
            st.rerun()

        st.markdown("---") 
        st.markdown(
            '<div style="background-color: #28a745; color: white; padding: 10px; border-radius: 5px; font-weight: bold; text-align: center;">KOSTENLOS!<br>$0/Monat</div>',
            unsafe_allow_html=True
        )
        st.subheader("Limits (Free Tier):")
        st.markdown("""
        * Google API: Tageslimit? (Prüfen!)
        * Tavily API: 1000/Monat
        """)

    try:
        agent = FinancialAgent() 
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Agenten: {e}")
        st.stop()

    st.title("📊 Financial Research Agent")
    st.caption(f"Aktuell in: **{active_chat_data['name']}** | ⚠️ Keine Finanzberatung")

    current_chat_history = active_chat_data["history"]
    for message in current_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if query := st.chat_input("Stellen Sie Ihre Finanzfrage..."):
        user_message = {"role": "user", "content": query}
        st.session_state.chats[st.session_state.active_chat_index]["history"].append(user_message)
        save_chat_to_db(st.session_state.active_chat_index, st.session_state.chats[st.session_state.active_chat_index]) 

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Agent recherchiert..."):
                try:
                    response = agent.run(query) 
                    st.markdown(response)
                    assistant_message = {"role": "assistant", "content": response}
                    st.session_state.chats[st.session_state.active_chat_index]["history"].append(assistant_message)
                    save_chat_to_db(st.session_state.active_chat_index, st.session_state.chats[st.session_state.active_chat_index]) 
                except Exception as e:
                    error_msg = f"Ein Fehler ist aufgetreten: {e}"
                    st.error(error_msg)
                    error_message = {"role": "assistant", "content": error_msg}
                    st.session_state.chats[st.session_state.active_chat_index]["history"].append(error_message)
                    save_chat_to_db(st.session_state.active_chat_index, st.session_state.chats[st.session_state.active_chat_index])

# --- Start-Logik ---
if check_password():
    run_app()
