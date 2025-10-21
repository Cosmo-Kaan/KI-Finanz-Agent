#!/usr/bin/env python3
"""
Financial Research Agent - Optimiert für Google Gemini Flash
Komplett kostenlos (bis 1.500 Queries/Tag)
"""

import os
import json
import requests
from typing import Dict, List
import yfinance as yf
import google.generativeai as genai

class FinancialAgent:
    """
    Financial Research Agent powered by Google Gemini Flash
    """
    
    def __init__(self, model: str = "gemini-2.0-flash-exp"):
        """
        Initialisiert den Agent mit Gemini
        
        Args:
            model: Gemini Model (default: gemini-2.0-flash-exp)
        """
        # Konfiguriere Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        
        print(f"✅ Agent initialized with Google Gemini ({model})")
        print(f"💰 Cost: $0/month (free tier)")
    
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
        """Holt Krypto-Daten von CoinGecko"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            market_data = data.get("market_data", {})
            
            return {
                "symbol": symbol,
                "name": data.get("name", "N/A"),
                "current_price": market_data.get("current_price", {}).get("usd", "N/A"),
                "market_cap": market_data.get("market_cap", {}).get("usd", "N/A"),
                "market_cap_rank": data.get("market_cap_rank", "N/A"),
                "total_volume": market_data.get("total_volume", {}).get("usd", "N/A"),
                "price_change_24h": market_data.get("price_change_percentage_24h", "N/A"),
                "price_change_7d": market_data.get("price_change_percentage_7d", "N/A"),
                "price_change_30d": market_data.get("price_change_percentage_30d", "N/A"),
                "price_change_1y": market_data.get("price_change_percentage_1y", "N/A"),
                "ath": market_data.get("ath", {}).get("usd", "N/A"),
                "ath_date": market_data.get("ath_date", {}).get("usd", "N/A"),
                "atl": market_data.get("atl", {}).get("usd", "N/A"),
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
        system_instruction = """Du bist ein erfahrener Finanzanalyst mit tiefer Expertise in:
        - Fundamental-Analyse (Bewertung, Profitabilität, Wachstum)
        - Technischer Analyse (Trends, Unterstützung/Widerstand)
        - Makroökonomie (Marktkontext, Zinsen, Volatilität)
        - Risikobewertung (Chancen/Risiken-Verhältnis)
        
        Deine Aufgabe:
        1. Analysiere die bereitgestellten Finanzdaten gründlich
        2. Beantworte die Frage des Nutzers präzise und umfassend
        3. Nutze konkrete Zahlen und Berechnungen
        4. Strukturiere deine Antwort klar (Executive Summary, Detailanalyse, Fazit)
        5. Weise auf Chancen UND Risiken hin
        6. Gib einen klaren Ausblick
        
        WICHTIG: 
        - Dies ist KEINE Finanzberatung
        - Weise den Nutzer darauf hin, eigene Research zu machen
        - Empfehle Konsultation eines Finanzberaters für Investitionsentscheidungen
        """
        
        user_prompt = f"""
        Nutzer-Frage: {query}
        
        Verfügbare Daten:
        {json.dumps(data, indent=2, default=str)}
        
        Analysiere die Daten professionell und beantworte die Frage umfassend.
        """
        
        try:
            # Gemini mit System Instruction
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
        
        Erstelle einen strukturierten Research-Plan mit konkreten Schritten.
        
        Verfügbare Aktionen:
        - get_stock_data: Holt Aktiendaten (Parameter: ticker, z.B. "AAPL")
        - get_crypto_data: Holt Krypto-Daten (Parameter: symbol, z.B. "bitcoin")
        - get_economic_indicators: Holt Makro-Indikatoren (keine Parameter)
        
        Gib den Plan als JSON zurück:
        {{
            "steps": [
                {{
                    "action": "get_stock_data",
                    "params": {{"ticker": "AAPL"}},
                    "reason": "Warum dieser Schritt nötig ist"
                }},
                ...
            ]
        }}
        
        Wichtig: Nur JSON ausgeben, keine zusätzlichen Erklärungen!
        """
        
        try:
            response = self.model.generate_content(planning_prompt)
            text = response.text
            
            # Extrahiere JSON aus Response
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = text[start:end]
                plan = json.loads(json_str)
                return plan.get("steps", [])
            else:
                return []
                
        except Exception as e:
            print(f"⚠️  Planning failed: {e}")
            return []
    
    def execute_step(self, step: Dict) -> Dict:
        """Führt einen Research-Schritt aus"""
        action = step.get("action")
        params = step.get("params", {})
        
        print(f"🔍 Executing: {action} with {params}")
        
        if action == "get_stock_data":
            return self.get_stock_data(**params)
        elif action == "get_crypto_data":
            return self.get_crypto_data(**params)
        elif action == "get_economic_indicators":
            return self.get_economic_indicators()
        else:
            return {"error": f"Unknown action: {action}"}
    
    def run(self, query: str) -> str:
        """Hauptfunktion: Führt die komplette Analyse durch"""
        print(f"\n{'='*80}")
        print(f"📊 Financial Research Agent (Google Gemini)")
        print(f"{'='*80}")
        print(f"\n❓ Query: {query}\n")
        
        # 1. Plan erstellen
        print("📋 Planning research steps...")
        steps = self.plan_research(query)
        
        if not steps:
            print("⚠️  Could not create research plan. Using direct analysis.")
            # Fallback: Versuche Ticker/Symbol aus Query zu extrahieren
            query_lower = query.lower()
            data = {}
            
            # Crypto?
            if any(kw in query_lower for kw in ["bitcoin", "ethereum", "btc", "eth", "crypto"]):
                symbol = "bitcoin" if "bitcoin" in query_lower or "btc" in query_lower else "ethereum"
                data["crypto"] = self.get_crypto_data(symbol)
            else:
                # Versuche Ticker zu erraten
                common_tickers = {
                    "apple": "AAPL", "tesla": "TSLA", "microsoft": "MSFT",
                    "google": "GOOGL", "amazon": "AMZN", "nvidia": "NVDA",
                    "meta": "META", "netflix": "NFLX", "ford": "F"
                }
                ticker = None
                for name, symbol in common_tickers.items():
                    if name in query_lower:
                        ticker = symbol
                        break
                
                if ticker:
                    data["stock"] = self.get_stock_data(ticker)
                    data["market"] = self.get_economic_indicators()
            
            return self.analyze_with_gemini(query, data)
        
        print(f"✅ Created {len(steps)} research steps\n")
        
        # 2. Schritte ausführen
        print("🔬 Executing research steps...")
        collected_data = {}
        
        for i, step in enumerate(steps, 1):
            print(f"\nStep {i}/{len(steps)}: {step.get('reason', 'No reason provided')}")
            result = self.execute_step(step)
            collected_data[f"step_{i}_{step.get('action')}"] = result
        
        print("\n✅ All steps executed\n")
        
        # 3. Gemini-Analyse
        print("🤖 Generating analysis with Gemini...")
        analysis = self.analyze_with_gemini(query, collected_data)
        
        print(f"\n{'='*80}")
        print(f"📈 ANALYSIS")
        print(f"{'='*80}\n")
        print(analysis)
        print(f"\n{'='*80}\n")
        
        return analysis


def main():
    """Interaktive CLI"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         FINANCIAL RESEARCH AGENT (GOOGLE GEMINI)             ║
    ║                                                              ║
    ║  Powered by: Google Gemini 2.0 Flash                        ║
    ║  Cost: $0/month (free tier)                                 ║
    ║  Limits: 15 RPM, 1M TPM, 1.500 RPD                          ║
    ║                                                              ║
    ║  Datenquellen:                                              ║
    ║  - Yahoo Finance (Aktien)                                   ║
    ║  - CoinGecko (Krypto)                                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Agent initialisieren
    try:
        agent = FinancialAgent()
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren: {e}")
        print(f"\nBitte setzen Sie Ihren Google API Key:")
        print(f"  export GOOGLE_API_KEY='AIza...'")
        print(f"\nAPI Key erhalten Sie bei: https://aistudio.google.com")
        return
    
    while True:
        try:
            query = input("\n💬 Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not query:
                continue
            
            agent.run(query)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()

