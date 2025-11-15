#!/usr/bin/env python3
"""
Autonomer Finanz-Analyst ("Motor")
Basierend auf der Logik von daily_crypto_agent.py,
umgebaut für Google Cloud Run, Gemini und Firestore.
"""

import os
import json
import requests
import time
from datetime import datetime
import google.oauth2.service_account
from google.cloud import firestore
from flask import Flask, request, jsonify
import google.generativeai as genai

# --- Initialisierung ---

app = Flask(__name__)
db = None
gemini_model = None
analyzer = None
AUTH_TOKEN = None

# Logik aus daily_crypto_agent.py, angepasst als Klasse
class CryptoMarketAnalyzer:
    def __init__(self, gemini_model_client):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {"accept": "application/json"}
        # KI-Modell (Gemini) wird von außen übergeben
        self.model = gemini_model_client
        print("✅ CryptoMarketAnalyzer initialisiert.")
        
    def rate_limit_pause(self):
        """Pause, um CoinGecko API-Limit nicht zu überschreiten."""
        time.sleep(1.2) # 1.2 Sekunden zur Sicherheit
    
    def get_global_data(self):
        """Globale Marktstatistiken abrufen."""
        try:
            response = requests.get(f"{self.base_url}/global", headers=self.headers)
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            print(f"Fehler beim Abrufen globaler Daten: {e}")
            return None
    
    def get_top_coins(self, limit=100):
        """Top Coins nach Market Cap abrufen."""
        try:
            params = {
                'vs_currency': 'usd', 'order': 'market_cap_desc',
                'per_page': limit, 'page': 1, 'sparkline': False,
                'price_change_percentage': '24h,7d'
            }
            response = requests.get(f"{self.base_url}/coins/markets", 
                                  headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Fehler beim Abrufen der Top Coins: {e}")
            return []
    
    def get_trending_coins(self):
        """Trending Coins identifizieren."""
        try:
            response = requests.get(f"{self.base_url}/search/trending", 
                                  headers=self.headers)
            response.raise_for_status()
            return response.json()['coins']
        except Exception as e:
            print(f"Fehler beim Abrufen der Trending Coins: {e}")
            return []
    
    def analyze_sentiment(self, coins):
        """Sentiment-Analyse basierend auf 24h Performance."""
        if not coins: return {'sentiment': 'Unbekannt', 'positive_count': 0, 'negative_count': 0, 'avg_change': 0}
        
        positive = [c for c in coins if c.get('price_change_percentage_24h', 0) > 0]
        negative = [c for c in coins if c.get('price_change_percentage_24h', 0) <= 0]
        
        avg_change = sum(c.get('price_change_percentage_24h', 0) for c in coins) / len(coins)
        
        if avg_change > 2: sentiment = "Stark Bullish"
        elif avg_change > 0: sentiment = "Bullish"
        elif avg_change > -2: sentiment = "Bearish"
        else: sentiment = "Stark Bearish"
        
        return {
            'sentiment': sentiment, 'positive_count': len(positive),
            'negative_count': len(negative), 'avg_change': avg_change
        }
    
    def find_low_cap_gems(self, coins):
        """Low-Cap Gems finden."""
        gems = []
        for coin in coins:
            market_cap = coin.get('market_cap', 0)
            price_change_24h = coin.get('price_change_percentage_24h', 0)
            
            if 10_000_000 <= market_cap <= 100_000_000 and price_change_24h > 5:
                gems.append({
                    'name': coin['name'], 'symbol': coin['symbol'].upper(),
                    'price': coin['current_price'], 'market_cap': market_cap,
                    'change_24h': price_change_24h, 'volume': coin.get('total_volume', 0)
                })
        return sorted(gems, key=lambda x: x['change_24h'], reverse=True)[:5]
    
    def generate_ai_analysis(self, market_data):
        """KI-Analyse mit Google Gemini generieren."""
        # Baut den Prompt aus der daily_crypto_agent.py-Logik
        prompt = f"""Als Krypto-Marktanalyst, analysiere die folgenden aktuellen Marktdaten und erstelle eine umfassende Analyse:

GLOBALE MARKTDATEN:
- Gesamte Market Cap: ${market_data['global']['total_market_cap']:,.0f}
- 24h Volumen: ${market_data['global']['total_volume']:,.0f}
- Bitcoin Dominanz: {market_data['global']['btc_dominance']:.2f}%
- Ethereum Dominanz: {market_data['global']['eth_dominance']:.2f}%

MARKT SENTIMENT:
- {market_data['sentiment']['sentiment']}
- Positive Coins: {market_data['sentiment']['positive_count']}
- Negative Coins: {market_data['sentiment']['negative_count']}
- Durchschnittliche 24h Veränderung: {market_data['sentiment']['avg_change']:.2f}%

TOP 3 COINS:
{json.dumps(market_data['top_3'], indent=2)}

TOP 5 GEWINNER:
{json.dumps(market_data['winners'], indent=2)}

TOP 5 VERLIERER:
{json.dumps(market_data['losers'], indent=2)}

Erstelle eine strukturierte Analyse mit folgenden Abschnitten:
1. MARKTLAGE-ZUSAMMENFASSUNG (2-3 Sätze)
2. HAUPTBEWEGUNGEN (wichtigste Entwicklungen)
3. BITCOIN & ETHEREUM TECHNISCHE ANALYSE (Support/Resistance Levels)
4. ALTCOIN-MARKT ÜBERSICHT
5. RISIKOFAKTOREN (3-5 Punkte)
6. CHANCEN (3-5 Punkte)
7. KURZFRISTIGE PROGNOSE (1-3 Tage)
8. MITTELFRISTIGE PROGNOSE (1-2 Wochen)
9. HANDLUNGSEMPFEHLUNGEN:
   - Für konservative Anleger
   - Für moderate Risiko-Anleger
   - Für aggressive Trader

Sei konkret, nutze die Zahlen aus den Daten, und kommuniziere Risiken transparent. Dies ist keine Finanzberatung, sondern eine informative Analyse."""

        try:
            # Verwendet Gemini statt OpenAI
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Fehler bei der KI-Analyse: {e}")
            return "KI-Analyse konnte nicht generiert werden."
    
    def format_number(self, num):
        """Zahlen formatieren"""
        if num >= 1_000_000_000: return f"${num/1_000_000_000:.2f}B"
        elif num >= 1_000_000: return f"${num/1_000_000:.2f}M"
        elif num >= 1_000: return f"${num/1_000:.2f}K"
        else: return f"${num:.2f}"
    
    def create_report_text(self, global_data, top_coins, trending, sentiment, gems, ai_analysis):
        """Report-Text formatieren (Code von daily_crypto_agent.py übernommen)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        report = f"{'='*80}\nCRYPTO-MARKTANALYSE - TÄGLICHER REPORT\n{'='*80}\n"
        report += f"Generiert am: {timestamp}\nDatenquelle: CoinGecko API\nKI-Analyse: Google Gemini\n{'='*80}\n\n"
        
        report += f"{'='*80}\n1. GLOBALE MARKTÜBERSICHT\n{'='*80}\n"
        report += f"Gesamte Market Cap:        {self.format_number(global_data['total_market_cap']['usd'])}\n"
        report += f"24h Handelsvolumen:        {self.format_number(global_data['total_volume']['usd'])}\n"
        report += f"Bitcoin Dominanz:          {global_data['market_cap_percentage']['btc']:.2f}%\n"
        report += f"Ethereum Dominanz:         {global_data['market_cap_percentage']['eth']:.2f}%\n"
        report += f"Aktive Kryptowährungen:   {global_data['active_cryptocurrencies']:,}\n\n"
        
        report += f"{'='*80}\n2. MARKT-SENTIMENT\n{'='*80}\n"
        report += f"Aktuelles Sentiment:       {sentiment['sentiment']}\n"
        report += f"Durchschnittliche Änderung: {sentiment['avg_change']:.2f}%\n\n"

        report += f"{'='*80}\n3. TOP 10 CRYPTOCURRENCIES\n{'='*80}\n"
        for i, coin in enumerate(top_coins[:10], 1):
            change_24h = coin.get('price_change_percentage_24h', 0)
            change_symbol = "📈" if change_24h > 0 else "📉"
            report += f"{i:2d}. {coin['name']} ({coin['symbol'].upper()})\n"
            report += f"    Preis: ${coin['current_price']:,.8f}\n    24h Änderung: {change_symbol} {change_24h:+.2f}%\n"
            report += f"    Market Cap: {self.format_number(coin['market_cap'])}\n\n"
        
        report += f"{'='*80}\n4. TOP 5 GEWINNER (24h)\n{'='*80}\n"
        winners = sorted(top_coins, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)[:5]
        for i, coin in enumerate(winners, 1):
            report += f"{i}. {coin['name']} ({coin['symbol'].upper()}): +{coin['price_change_percentage_24h']:.2f}%\n"
        
        report += f"\n{'='*80}\n5. TOP 5 VERLIERER (24h)\n{'='*80}\n"
        losers = sorted(top_coins, key=lambda x: x.get('price_change_percentage_24h', 0))[:5]
        for i, coin in enumerate(losers, 1):
            report += f"{i}. {coin['name']} ({coin['symbol'].upper()}): {coin['price_change_percentage_24h']:.2f}%\n"
        
        report += f"\n{'='*80}\n6. KI-GESTÜTZTE MARKTANALYSE\n{'='*80}\n\n{ai_analysis}\n"
        
        report += f"\n{'='*80}\n7. TRENDING COINS (Potenzielle Geheimtipps)\n{'='*80}\n"
        for i, item in enumerate(trending[:7], 1):
            coin = item['item']
            report += f"{i}. {coin['name']} ({coin['symbol'].upper()}) - Rank: #{coin.get('market_cap_rank', 'N/A')}\n"

        report += f"\n{'='*80}\nDISCLAIMER\n{'='*80}\n"
        report += "Dieser Report dient ausschließlich zu Informationszwecken und stellt keine Finanzberatung dar...\n"
        
        return report

    def generate_full_report(self):
        """Hauptfunktion: Kompletten Report generieren (wie in main() von daily_crypto_agent.py)"""
        print("🚀 Starte Crypto-Marktanalyse...")
        
        print("📊 Rufe globale Marktdaten ab...")
        global_data = self.get_global_data()
        if not global_data: return "Fehler: Globale Daten konnten nicht abgerufen werden."
        self.rate_limit_pause()
        
        print("💰 Rufe Top 100 Coins ab...")
        top_coins = self.get_top_coins(100)
        self.rate_limit_pause()
        
        print("🔥 Rufe Trending Coins ab...")
        trending = self.get_trending_coins()
        self.rate_limit_pause()
        
        print("📈 Führe Sentiment-Analyse durch...")
        sentiment = self.analyze_sentiment(top_coins)
        
        print("💎 Suche Low-Cap Gems...")
        gems = self.find_low_cap_gems(top_coins)
        
        print("🤖 Generiere KI-Analyse...")
        market_data = {
            'global': {
                'total_market_cap': global_data['total_market_cap']['usd'],
                'total_volume': global_data['total_volume']['usd'],
                'btc_dominance': global_data['market_cap_percentage']['btc'],
                'eth_dominance': global_data['market_cap_percentage']['eth']
            },
            'sentiment': sentiment,
            'top_3': [{'name': c['name'], 'symbol': c['symbol'].upper(), 'price': c['current_price'], 'change_24h': c['price_change_percentage_24h'], 'market_cap': c['market_cap']} for c in top_coins[:3]],
            'winners': [{'name': c['name'], 'symbol': c['symbol'].upper(), 'change_24h': c['price_change_percentage_24h']} for c in sorted(top_coins, key=lambda x: x.get('price_change_percentage_24h', 0), reverse=True)[:5]],
            'losers': [{'name': c['name'], 'symbol': c['symbol'].upper(), 'change_24h': c['price_change_percentage_24h']} for c in sorted(top_coins, key=lambda x: x.get('price_change_percentage_24h', 0))[:5]]
        }
        
        ai_analysis = self.generate_ai_analysis(market_data)
        
        print("📝 Erstelle Report...")
        report = self.create_report_text(global_data, top_coins, trending, sentiment, gems, ai_analysis)
        
        print(f"✅ Report-Generierung abgeschlossen.")
        return report

# --- Globale Initialisierung beim Start des Cloud Run Containers ---
try:
    print("Initialisiere Agenten-Motor...")
    AUTH_TOKEN = os.getenv("AUTH_TOKEN")
    if not AUTH_TOKEN:
        raise ValueError("AUTH_TOKEN nicht in Umgebungsvariablen gefunden!")

    # Firestore-Client
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
    db = firestore.Client(credentials=credentials, database="finanz-agent-db")
    
    # Gemini-Client
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    gemini_model = genai.GenerativeModel("gemini-2.5-flash") # Oder dein verfügbares Modell
    
    # Analyse-Agent
    analyzer = CryptoMarketAnalyzer(gemini_model_client=gemini_model)
    
    print("✅ Agenten-Motor erfolgreich initialisiert.")

except Exception as e:
    print(f"❌ Kritischer Fehler bei der Initialisierung: {e}")
    db = None
    analyzer = None

# --- Der "Wecker"-Endpunkt ---
@app.route('/run-analysis', methods=['POST'])
def run_analysis():
    """Wird vom Google Cloud Scheduler aufgerufen."""
    
    # 1. Sicherheit
    request_token = request.headers.get('Authorization')
    if request_token != f"Bearer {AUTH_TOKEN}":
        print(f"❌ Fehler: Ungültiger Auth-Token. Erhalten: {request_token}")
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    if not analyzer or not db:
        print("❌ Fehler: Agent oder DB wurden nicht initialisiert (siehe Start-Logs).")
        return jsonify({"status": "error", "message": "Agent not initialized"}), 500

    print("Auth-Token korrekt. Starte autonome Analyse...")

    # 2. Ausführung
    try:
        # Führe die Hauptlogik aus daily_crypto_agent.py aus
        report_content = analyzer.generate_full_report()
        
        # 3. Speichern
        report_data = {
            "timestamp": datetime.now(datetime.timezone.utc),
            "report": report_content
        }
        
        # Fügt ein neues Dokument hinzu, Firestore generiert die ID
        doc_ref = db.collection("reports").add(report_data)
        
        print(f"✅ Bericht erfolgreich erstellt und in Firestore gespeichert: {doc_ref[1].id}")
        return jsonify({"status": "success", "report_id": doc_ref[1].id}), 200

    except Exception as e:
        print(f"❌ Fehler während der Analyse-Ausführung: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
