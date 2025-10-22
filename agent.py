#!/usr/bin/env python3
"""
Financial Research Agent - Optimiert für Google Gemini Flash
JETZT MIT WEB-SUCHE (DuckDuckGo)
"""

import os
import json
import requests
from typing import Dict, List
import yfinance as yf
import google.generativeai as genai
# --- NEU: Import für die Web-Suche ---
from duckduckgo_search import DDGS

class FinancialAgent:
    """
    Financial Research Agent powered by Google Gemini Flash
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        # --- NEU: Initialisiert das Such-Tool ---
        self.search_tool = DDGS()
        
        print(f"✅ Agent initialized with Google Gemini ({model}) and DuckDuckGo Search")
    
    # --- NEU: Web-Such-Funktion ---
    def search_web(self, query: str) -> List[Dict]:
        """Führt eine Web-Suche durch für allgemeine Anfragen."""
        print(f"🔍 Searching web for: {query}")
        try:
            # max_results=5 liefert die Top 5 Ergebnisse
            results = self.search_tool.text(query, max_results=5)
            return results if results else [{"snippet": "Keine Suchergebnisse gefunden."}]
        except Exception as e:
            print(f"❌ Web search failed: {e}")
            return [{"error": f"Fehler bei der Web-Suche: {str(e)}"}]

    def get_stock_data(self, ticker: str, period: str = "1y") -> Dict:
        """Holt Aktiendaten von Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)
            
            # Fundamentals
            fundamentals = {
                "ticker": ticker,
                "name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "enterprise_value": info.get("enterpriseValue", "N/A"),
            }
            
            # Valuation
            valuation = {
                "current_price": info.get("currentPrice", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "forward_pe": info.get("forwardPE", "N/A"),
                "peg_ratio": info.get("pegRatio", "N/A"),
                "price_to_book": info.get("priceToBook", "N/A"),
                "price_to_sales": info.get("priceToSalesTrailing12Months", "N/A"),
                "ev_to_revenue": info.get("enterpriseToRevenue", "N/A"),
                "ev_to_ebitda": info.get("enterpriseToEbitda", "N/A"),
            }
            
            # Profitability
            profitability = {
                "profit_margin": info.get("profitMargins", "N/A"),
                "operating_margin": info.get("operatingMargins", "N/A"),
                "gross_margin": info.get("grossMargins", "N/A"),
                "roe": info.get("returnOnEquity", "N/A"),
                "roa": info.get("returnOnAssets", "N/A"),
            }
            
            # Growth
            growth = {
                "revenue_growth": info.get("revenueGrowth", "N/A"),
                "earnings_growth": info.get("earningsGrowth", "N/A"),
                "revenue": info.get("totalRevenue", "N/A"),
                "earnings": info.get("netIncomeToCommon", "N/A"),
            }
            
            # Financial Health
            financial_health = {
                "total_cash": info.get("totalCash", "N/A"),
                "total_debt": info.get("totalDebt", "N/A"),
                "debt_to_equity": info.get("debtToEquity", "N/A"),
                "current_ratio": info.get("currentRatio", "N/A"),
                "quick_ratio": info.get("quickRatio", "N/A"),
                "free_cash_flow": info.get("freeCashflow", "N/A"),
            }
            
            # Price History
            price_history = {}
            if len(hist) > 0:
                price_history = {
                    "current": float(hist['Close'].iloc[-1]),
                    "1_month_ago": float(hist['Close'].iloc[-22]) if len(hist) > 22 else None,
                    "3_months_ago": float(hist['Close'].iloc[-66]) if len(hist) > 66 else None,
                    "6_months_ago": float(hist['Close'].iloc[-132]) if len(hist) > 132 else None,
                    "1_year_ago": float(hist['Close'].iloc[0]),
                    "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                    "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                }
            
            # Analyst Recommendations
            recommendations = {
                "target_price": info.get("targetMeanPrice", "N/A"),
                "recommendation": info.get("recommendationKey", "N/A"),
                "number_of_analysts": info.get("numberOfAnalystOpinions", "N/A"),
            }
            
            return {
                "source": "Yahoo Finance (yfinance)",
                "fundamentals": fundamentals,
                "valuation": valuation,
                "profitability": profitability,
                "growth": growth,
                "financial_health": financial_health,
                "price_history": price_history,
                "recommendations": recommendations,
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}

    def get_crypto_data(self, symbol: str) -> Dict:
        """Holt Krypto-Daten von CoinGecko (IN EUR)"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}"
            response = requests.get(url, timeout=10)
            data = response.json()
            market_data = data.get("market_data", {})
            
            return {
                "source": "CoinGecko API",
                "symbol": symbol,
                "name": data.get("name", "N/A"),
                "current_price_eur": market_data.get("current_price", {}).get("eur", "N/A"),
                "market_cap_eur": market_data.get("market_cap", {}).get("eur", "N/A"),
                "market_cap_rank": data.get("market_cap_rank", "N/A"),
                "total_volume_eur": market_data.get("total_volume", {}).get("eur", "N/A"),
                "price_change_24h_percent": market_data.get("price_change_percentage_24h", "N/A"),
                "price_change_7d_percent": market_data.get("price_change_percentage_7d", "N/A"),
                "price_change_30d_percent": market_data.get("price_change_percentage_30d", "N/A"),
                "price_change_1y_percent": market_data.get("price_change_percentage_1y", "N/A"),
                "ath_eur": market_data.get("ath", {}).get("eur", "N/A"),
                "ath_date_eur": market_data.get("ath_date", {}).get("eur", "N/A"),
                "atl_eur": market_data.get("atl", {}).get("eur", "N/A"),
                "circulating_supply": market_data.get("circulating_supply", "N/A"),
                "total_supply": market_data.get("total_supply", "N/A"),
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch crypto data for {symbol}: {str(e)}"}

    def get_economic_indicators(self) -> Dict:
        """Holt makroökonomische Indikatoren"""
        try:
            # S&P 500
            sp500 = yf.Ticker("^GSPC")
            sp500_hist = sp500.history(period="1mo")
            
            # VIX (Volatility Index)
            vix = yf.Ticker("^VIX")
            vix_hist = vix.history(period="1mo")
            
            # 10-Year Treasury
            treasury = yf.Ticker("^TNX")
            treasury_hist = treasury.history(period="1mo")
            
            return {
                "source": "Yahoo Finance (yfinance)",
                "sp500": {
                    "current": float(sp500_hist['Close'].iloc[-1]) if len(sp500_hist) > 0 else None,
                    "change_1m": ((sp500_hist['Close'].iloc[-1] / sp500_hist['Close'].iloc[0] - 1) * 100) if len(sp500_hist) > 0 else None,
                },
                "vix": {
                    "current": float(vix_hist['Close'].iloc[-1]) if len(vix_hist) > 0 else None,
                    "interpretation": "Low volatility" if (len(vix_hist) > 0 and vix_hist['Close'].iloc[-1] < 20) else "High volatility",
                },
                "treasury_10y": {
                    "current": float(treasury_hist['Close'].iloc[-1]) if len(treasury_hist) > 0 else None,
                },
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch economic indicators: {str(e)}"}

    def analyze_with_gemini(self, query: str, data: Dict) -> str:
        """Nutzt Gemini für intelligente Analyse"""
        
        system_instruction = """Du bist ein präziser Finanzdaten-Analyst.
        Deine Aufgabe:
        1. Analysiere AUSSCHLIESSLICH die bereitgestellten JSON-Daten (von APIs oder Web-Suche).
        2. Beantworte die Frage des Nutzers präzise.
        3. Verwende NUR Zahlen und Fakten aus den Daten. Gib die Quelle an (z.B. "Laut CoinGecko...", "Laut Web-Suche...").
        WICHTIGE REGELN:
        - ERFINDE NIEMALS Daten.
        - Wenn eine Information nicht in den Daten enthalten ist, sage klar: "Ich habe keine Daten zu [Thema]."
        - Wenn Daten Währungs-Suffixe haben (z.B. 'current_price_eur'), verwende diese.
        - Dies ist KEINE Finanzberatung. Weise am Ende immer darauf hin.
        """
        
        user_prompt = f"""
        Nutzer-Frage: {query}
        
        Verfügbare Daten (aus APIs und Web-Suche):
        {json.dumps(data, indent=2, default=str)}
        
        Analysiere die Daten professionell und beantworte die Frage umfassend, basierend NUR auf den obigen Daten.
        """
        
        try:
            model_with_instruction = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction
            )
            response = model_with_instruction.generate_content(user_prompt)
            return response.text
            
        except Exception as e:
            return f"Error generating analysis: {str(e)}"
    
    def plan_research(self, query: str) -> List[Dict]:
        """Plant die Research-Schritte basierend auf der Query"""
        planning_prompt = f"""
        Nutzer-Frage: {query}
        
        Erstelle einen strukturierten Research-Plan. Entscheide für JEDE Frage, welches Tool das beste ist.

        Verfügbare Aktionen:
        1. search_web:
           - Zweck: Für allgemeine Fragen, Definitionen ("Was ist..."), unbekannte Unternehmen/Protokolle oder aktuelle Nachrichten.
           - Parameter: {{"query": "Suchbegriff"}}
        
        2. get_stock_data:
           - Zweck: NUR für spezifische Finanzkennzahlen einer bekannten Aktie (z.B. Apple, TSLA).
           - Parameter: {{"ticker": "AAPL"}}
        
        3. get_crypto_data:
           - Zweck: NUR für spezifische Preis- und Marktdaten einer bekannten Kryptowährung (z.B. bitcoin, ethereum).
           - Parameter: {{"symbol": "bitcoin"}}
        
        4. get_economic_indicators:
           - Zweck: Für allgemeine Markt-Indikatoren (S&P 500, VIX, Zinsen).
           - Parameter: {{}}

        Beispiele:
        - Frage "Was ist Virtuals Protocol?": Nutze `search_web`.
        - Frage "Wie ist das P/E Ratio von Tesla?": Nutze `get_stock_data` mit `ticker="TSLA"`.
        - Frage "Aktueller Bitcoin Kurs": Nutze `get_crypto_data` mit `symbol="bitcoin"`.
        - Frage "Wie ist die Marktstimmung?": Nutze `get_economic_indicators`.
        - Frage "Vergleiche Apple und Microsoft": Nutze ZWEI `get_stock_data` Schritte.

        Gib den Plan als JSON zurück:
        {{
            "steps": [
                {{
                    "action": "ACTION_NAME",
                    "params": {{"param": "value"}},
                    "reason": "Warum dieser Schritt nötig ist"
                }},
                ...
            ]
        }}
        
        Wichtig: Nur JSON ausgeben!
        """
        
        try:
            response = self.model.generate_content(planning_prompt)
            text = response.text
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = text[start:end]
                plan = json.loads(json_str)
                return plan.get("steps", [])
            else:
                print(f"⚠️  Planning failed: Konnte kein JSON im Text finden: {text}")
                return []
                
        except Exception as e:
            print(f"⚠️  Planning failed: {e}")
            return []
    
    def execute_step(self, step: Dict) -> Dict:
        """Führt einen Research-Schritt aus"""
        action = step.get("action")
        params = step.get("params", {})
        
        print(f"🔍 Executing: {action} with {params}")
        
        if action == "search_web":
            return self.search_web(**params)
        elif action == "get_stock_data":
            return self.get_stock_data(**params)
        elif action == "get_crypto_data":
            return self.get_crypto_data(**params)
        elif action == "get_economic_indicators":
            return self.get_economic_indicators()
        else:
            return {"error": f"Unknown action: {action}"}
    
    def run(self, query: str) -> str:
        """Hauptfunktion: Führt die komplette Analyse durch"""
        print(f"\n{'='*80}\n❓ Query: {query}\n")
        
        # 1. Plan erstellen
        print("📋 Planning research steps...")
        steps = self.plan_research(query)
        
        if not steps:
            print("⚠️  Could not create research plan. Fallback to direct search.")
            # Fallback: Wenn die Planung fehlschlägt, einfach direkt googeln
            steps = [{"
