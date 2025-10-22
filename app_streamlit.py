#!/usr/bin/env python3
"""
Streamlit Web-App für Financial Research Agent
Optimiert für Google Gemini Flash (KOSTENLOS!)
"""

import streamlit as st
import os
from agent import FinancialAgent
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Financial Research Agent (Gemini)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .cost-badge {
        background-color: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'agent' not in st.session_state:
    st.session_state.agent = None

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Einstellungen")
    
    # API Key Input
    api_key = st.text_input(
        "Google API Key",
        type="password",
        value=os.getenv("GOOGLE_API_KEY", ""),
        help="Ihr Google API Key (beginnt mit AIza...)"
    )
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        if st.session_state.agent is None:
            try:
                st.session_state.agent = FinancialAgent()
                st.success("✅ API Key gesetzt")
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
    else:
        st.warning("⚠️ Bitte API Key eingeben")
    
    st.markdown("---")
    
    # Cost Info
    st.markdown("""
    <div class="cost-badge">
        💰 KOSTENLOS!<br>
        $0/Monat
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    **Limits (Free Tier):**
    - 15 Requests/Minute
    - 1M Tokens/Minute
    - 1.500 Requests/Tag
    
    **Für normale Nutzung völlig ausreichend!**
    """)
    
    st.markdown("---")
    
    # Example Queries
    st.markdown("### 💡 Beispiel-Fragen")
    
    examples = [
        "Analyze Apple's financial health",
        "Compare Tesla and Ford",
        "What's the current state of Bitcoin?",
        "Is NVIDIA overvalued?",
        "Analyze Microsoft's growth potential",
        "Should I invest in Amazon?",
        "Compare Bitcoin and Ethereum"
    ]
    
    for example in examples:
        if st.button(example, key=f"example_{example}"):
            st.session_state.current_query = example
    
    st.markdown("---")
    
    # Clear History
    if st.button("🗑️ Verlauf löschen"):
        st.session_state.history = []
        st.rerun()
    
    st.markdown("---")
    
    # Info
    st.markdown("""
    ### ℹ️ Info
    
    **Powered by:**
    - Google Gemini 2.0 Flash
    
    **Datenquellen:**
    - Yahoo Finance (Aktien)
    - CoinGecko (Krypto)
    
    **Kosten:**
    - Hosting: $0 (Streamlit Cloud)
    - LLM: $0 (Gemini Free Tier)
    - Daten: $0 (kostenlose APIs)
    
    **Total: $0/Monat** 🎉
    
    **Open Source:**
    - MIT Lizenz
    - Frei nutzbar
    """)

# Main Content
st.markdown('<div class="main-header">📊 Financial Research Agent</div>', unsafe_allow_html=True)

st.markdown("""
Stellen Sie Fragen zu Aktien, Krypto oder Märkten. Der Agent analysiert automatisch 
die relevanten Daten und gibt Ihnen professionelle Insights - **komplett kostenlos**!

**Powered by Google Gemini 2.0 Flash** 🚀
""")

# Query Input
col1, col2 = st.columns([4, 1])

with col1:
    query = st.text_input(
        "Ihre Frage:",
        value=st.session_state.get('current_query', ''),
        placeholder="z.B. Analyze Apple's financial health",
        label_visibility="collapsed"
    )

with col2:
    analyze_button = st.button("🔍 Analysieren", type="primary")

# Clear current_query after use
if 'current_query' in st.session_state:
    del st.session_state.current_query

# Process Query
if (analyze_button or query) and query:
    if not api_key:
        st.error("⚠️ Bitte geben Sie zuerst Ihren Google API Key in der Sidebar ein!")
        st.info("""
        **API Key erhalten:**
        1. Gehen Sie zu https://aistudio.google.com
        2. Sign in mit Google Account
        3. Klicken Sie auf "Get API Key"
        4. Kopieren Sie den Key (beginnt mit AIza...)
        """)
    else:
        with st.spinner("🔬 Analysiere mit Google Gemini..."):
            try:
                # Run agent
                analysis = st.session_state.agent.run(query)
                
                # Add to history
                st.session_state.history.append({
                    'timestamp': datetime.now(),
                    'query': query,
                    'analysis': analysis
                })
                
                # Display result
                st.markdown("### 📈 Analyse-Ergebnis")
                st.markdown(analysis)
                
                # Success message
                st.success("✅ Analyse abgeschlossen! (Kosten: $0)")
                
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
                
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    st.warning("""
                    **Rate Limit erreicht!**
                    
                    Free Tier Limits:
                    - 15 Requests/Minute
                    - 1.500 Requests/Tag
                    
                    Bitte warten Sie kurz und versuchen Sie es erneut.
                    """)

# Display History
if st.session_state.history:
    st.markdown("---")
    st.markdown("## 📜 Verlauf")
    
    for i, item in enumerate(reversed(st.session_state.history)):
        with st.expander(
            f"🕐 {item['timestamp'].strftime('%H:%M:%S')} - {item['query'][:50]}...",
            expanded=(i == 0)
        ):
            st.markdown(f"**Frage:** {item['query']}")
            st.markdown("**Antwort:**")
            st.markdown(item['analysis'])

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    Powered by Google Gemini 2.0 Flash 🚀 | Komplett kostenlos 💰<br>
    Gebaut mit ❤️ | Open Source | MIT Lizenz<br>
    ⚠️ Keine Finanzberatung - Konsultieren Sie einen Finanzberater
</div>
""", unsafe_allow_html=True)

