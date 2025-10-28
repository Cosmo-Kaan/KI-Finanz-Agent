#!/usr/bin/env python3
import streamlit as st
# Annahme: Dein Agenten-Code ist immer noch in 'agent.py'
from agent import FinancialAgent 
import google.oauth2.service_account
from google.cloud import firestore
import json

# --- Firestore Initialisierung ---
# Versucht, die Verbindung zur Datenbank herzustellen
try:
    # Baut das Credentials-Objekt aus den Streamlit Secrets zusammen
    key_dict = {
        "type": "service_account",
        "project_id": st.secrets["FIRESTORE_PROJECT_ID"],
        "private_key_id": st.secrets["FIRESTORE_PRIVATE_KEY_ID"],
        # Ersetzt die gespeicherten '\n' wieder durch echte Zeilenumbrüche
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
    st.sidebar.success("Firestore verbunden!", icon="🔥") # Zeigt Erfolg in der Sidebar an
except Exception as e:
    # Zeigt eine Fehlermeldung an, wenn die Verbindung fehlschlägt
    st.error(f"Fehler bei Firestore-Verbindung (Prüfe Secrets!): {e}") 
    st.stop() # Hält die App an

# --- Passwortschutz (Unverändert) ---
# Überprüft das eingegebene Passwort gegen das in den Secrets gespeicherte
def check_password():
    try:
        correct_password = st.secrets["APP_PASSWORD"]
    except KeyError:
        st.error("Fehler: APP_PASSWORD wurde nicht in den Streamlit Secrets gesetzt!")
        st.stop() 
    password = st.text_input("Bitte geben Sie das Passwort ein:", type="password")
    if not password: 
        st.stop()  # Wartet auf Eingabe
    if password == correct_password: 
        return True
    st.error("Passwort ist falsch.")
    return False

# --- Datenbank-Funktionen ---
# Definiert eine (noch feste) User-ID. Für eine echte Multi-User-App müsste das dynamisch sein.
USER_ID = "default_user" 
NUM_CHATS = 10 # Anzahl der Chat-Slots

# Lädt die Chat-Daten aus Firestore
@st.cache_resource # Wichtig: Cache die Funktion, damit nicht bei jeder Interaktion neu geladen wird
def load_chats_from_db():
    """Lädt alle Chat-Objekte für den User aus Firestore, sortiert nach Index."""
    print("Lade Chats aus Firestore...") # Hilfreich für Debugging
    # Definiert den Pfad zur Chat-Sammlung des Nutzers
    chats_ref = db.collection("users").document(USER_ID).collection("chats").order_by("index")
    chats = [None] * NUM_CHATS # Erstellt eine Liste mit Platzhaltern
    found_chats = False
    for doc in chats_ref.stream():
        chat_data = doc.to_dict()
        chat_index = chat_data.get("index")
        if chat_index is not None and 0 <= chat_index < NUM_CHATS:
             # Stellt sicher, dass 'history' eine Liste ist
            if "history" not in chat_data or not isinstance(chat_data["history"], list):
                chat_data["history"] = []
            chats[chat_index] = chat_data # Fügt Chat an der richtigen Stelle ein
            found_chats = True
    
    # Wenn keine Chats in der DB gefunden wurden, erstelle 10 leere und speichere sie
    if not found_chats:
        print("Keine Chats gefunden, erstelle initiale Chats...")
        chats = [{"name": f"Chat {i+1}", "history": [], "index": i} for i in range(NUM_CHATS)]
        batch = db.batch()
        for i, chat in enumerate(chats):
            doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{i}")
            batch.set(doc_ref, chat)
        batch.commit()
            
    # Fülle eventuell fehlende Slots mit leeren Chats auf (falls weniger als 10 in DB waren)
    for i in range(NUM_CHATS):
        if chats[i] is None:
             chats[i] = {"name": f"Chat {i+1}", "history": [], "index": i}
             # Optional: Fehlenden Chat auch in DB speichern
             # doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{i}")
             # doc_ref.set(chats[i])

    return chats

# Speichert den kompletten Zustand eines Chats in Firestore
def save_chat_to_db(chat_index, chat_data):
    """Speichert ein einzelnes Chat-Objekt (Name und Verlauf) in Firestore."""
    print(f"Speichere Chat {chat_index} in Firestore...")
    doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{chat_index}")
    doc_ref.set(chat_data, merge=True) # merge=True ist sicherer, falls Struktur geändert wird

# Speichert nur den geänderten Namen eines Chats
def save_chat_name_to_db(chat_index, new_name):
    """Speichert nur den neuen Namen eines Chats in Firestore."""
    print(f"Speichere neuen Namen für Chat {chat_index}: {new_name}")
    doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{chat_index}")
    doc_ref.update({"name": new_name})

# Löscht den Verlauf eines Chats, behält aber den Namen
def delete_chat_history_in_db(chat_index):
    """Löscht nur den Verlauf ('history') eines Chats in Firestore."""
    print(f"Lösche Verlauf von Chat {chat_index}...")
    doc_ref = db.collection("users").document(USER_ID).collection("chats").document(f"chat_{chat_index}")
    doc_ref.update({"history": []})


# --- HAUPT-ANWENDUNG ---
def run_app():
    st.set_page_config(page_title="Financial Research Agent", layout="wide")

    # --- Lade Chats aus DB (nur einmal pro Session dank Cache) ---
    st.session_state.chats = load_chats_from_db()
    
    # Initialisiere aktiven Chat-Index, falls nicht vorhanden
    if "active_chat_index" not in st.session_state:
        st.session_state.active_chat_index = 0

    # --- Seitenleiste ---
    with st.sidebar:
        st.title("Einstellungen")
        # Zeigt API Key Status an
        try:
            if st.secrets["GOOGLE_API_KEY"]:
                st.success("Google API Key geladen!", icon="✅")
            if st.secrets["TAVILY_API_KEY"]:
                st.success("Tavily API Key geladen!", icon="✅")
        except KeyError:
            st.warning("Einer der API Keys fehlt in den Secrets!", icon="⚠️")

        st.subheader("Meine Chats")
        # Holt die aktuellen Namen aus dem Session State (der aus der DB geladen wurde)
        chat_option_names = [chat["name"] for chat in st.session_state.chats]
        
        # Radio-Button zur Chatauswahl
        selected_chat_name = st.radio(
            "Wählen Sie einen Chat:",
            options=chat_option_names,
            index=st.session_state.active_chat_index,
            key=f"radio_{st.session_state.active_chat_index}" # Eindeutiger Key für Streamlit
        )
        
        # Aktualisiert den Index, wenn ein anderer Chat ausgewählt wird
        new_active_index = chat_option_names.index(selected_chat_name)
        if new_active_index != st.session_state.active_chat_index:
            st.session_state.active_chat_index = new_active_index
            st.rerun() # Lädt die App neu, um den neuen Chat anzuzeigen
        
        # Holt die Daten des aktuell aktiven Chats
        active_chat_data = st.session_state.chats[st.session_state.active_chat_index]

        # Feld zum Umbenennen des Chats
        new_name = st.text_input(
            "Chat umbenennen:", 
            value=active_chat_data["name"],
            key=f"name_input_{st.session_state.active_chat_index}" # Eindeutiger Key
        )
        # Wenn der Name geändert wurde, speichere ihn (lokal & DB) und lade neu
        if new_name != active_chat_data["name"] and new_name.strip(): # Verhindert leere Namen
            st.session_state.chats[st.session_state.active_chat_index]["name"] = new_name.strip()
            save_chat_name_to_db(st.session_state.active_chat_index, new_name.strip())
            st.rerun() 

        # Button zum Löschen des Chat-Verlaufs
        st.markdown("---")
        if st.button("Aktuellen Chat löschen", type="primary"):
            st.session_state.chats[st.session_state.active_chat_index]["history"] = []
            delete_chat_history_in_db(st.session_state.active_chat_index)
            st.rerun()

        # --- (Rest der Sidebar: Kostenlos-Badge, Limits) ---
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

    # --- Agent initialisieren ---
    try:
        agent = FinancialAgent() # Nimmt an, agent.py ist im selben Ordner
    except Exception as e:
        st.error(f"Fehler beim Initialisieren des Agenten: {e}")
        st.stop()

    # --- HAUPTSEITE ---
    st.title("📊 Financial Research Agent")
    st.caption(f"Aktuell in: **{active_chat_data['name']}** | ⚠️ Keine Finanzberatung") # Zeigt den Chat-Namen an

    # Zeige den Chatverlauf des aktiven Chats
    current_chat_history = active_chat_data["history"]
    for message in current_chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Eingabefeld für neue Nachrichten
    if query := st.chat_input("Stellen Sie Ihre Finanzfrage..."):
        # Füge User-Nachricht zum lokalen State hinzu
        user_message = {"role": "user", "content": query}
        st.session_state.chats[st.session_state.active_chat_index]["history"].append(user_message)
        # Speichere den gesamten Chat (inkl. neuer User-Nachricht) in der DB
        save_chat_to_db(st.session_state.active_chat_index, st.session_state.chats[st.session_state.active_chat_index]) 

        # Zeige User-Nachricht im Chat an
        with st.chat_message("user"):
            st.markdown(query)

        # Hole und zeige Agenten-Antwort
        with st.chat_message("assistant"):
            with st.spinner("Agent recherchiert..."):
                try:
                    # Rufe die 'run'-Funktion deines Agenten auf
                    response = agent.run(query) 
                    st.markdown(response)
                    # Füge Agenten-Nachricht zum lokalen State hinzu
                    assistant_message = {"role": "assistant", "content": response}
                    st.session_state.chats[st.session_state.active_chat_index]["history"].append(assistant_message)
                    # Speichere den gesamten Chat (inkl. neuer Agenten-Antwort) erneut in der DB
                    save_chat_to_db(st.session_state.active_chat_index, st.session_state.chats[st.session_state.active_chat_index]) 
                except Exception as e:
                    error_msg = f"Ein Fehler ist aufgetreten: {e}"
                    st.error(error_msg)
                    # Füge Fehlermeldung zum lokalen State hinzu (optional auch in DB)
                    error_message = {"role": "assistant", "content": error_msg}
                    st.session_state.chats[st.session_state.active_chat_index]["history"].append(error_message)
                    save_chat_to_db(st.session_state.active_chat_index, st.session_state.chats[st.session_state.active_chat_index])


# --- Start-Logik ---
# Führt zuerst die Passwortprüfung durch, dann die Haupt-App
if check_password():
    run_app()
