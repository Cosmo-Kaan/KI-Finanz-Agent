#!/usr/bin/env python3
"""
Financial Research Agent - Optimiert für Google Gemini Flash
VERSION: Hedgefonds-Analyst mit Tavily-Suche und API-Fallback
"""

import os
import json
import requests
from typing import Dict, List
import yfinance as yf
import google.generativeai as genai
from tavily import TavilyClient

class FinancialAgent:
    """
    Financial Research Agent powered by Google Gemini Flash
    """
    
    def __init__(self, model: str = "gemini-2.5-flash"): # Verwendet das Modell aus deinem AI Studio
        # Google Gemini API Key
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        genai.configure(api_key=google_api_key)
        
        # Tavily Search API Key
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
        
        self.model_name = model
        self.model = genai.GenerativeModel(model)
        # Initialisiert den Tavily Client
        self.search_tool = TavilyClient(api_key=tavily_api_key)
        
        print(f"✅ Agent initialized with Google Gemini ({model}) and Tavily Search")
    
    def search_web(self, query: str) -> List[Dict]:
        """Führt eine Web-Suche mit Tavily durch."""
        
        clean_query = query
        query_lower = query.lower()
        if query_lower.startswith("was ist"):
            clean_query = query[7:].strip(" ?") 
        elif query_lower.startswith("erkläre"):
            clean_query = query[7:].strip(" ?")
        elif "kurs" in query_lower or "preis" in query_lower:
             # Stellt sicher, dass die Suche sauber ist, z.B. "aktueller Ethereum Preis"
            clean_query = f"aktueller {query} Preis"
        
        print(f"🔍 Searching Tavily for (cleaned): {clean_query}")
        
        try:
            response = self.search_tool.search(query=clean_query, search_depth="basic", max_results=5)
            results = [{"snippet": r["content"], "source": r["url"]} for r in response.get("results", [])]
            return {"source": "Tavily Web Search", "results": results if results else [{"snippet": "Keine Suchergebnisse gefunden."}]}
        except Exception as e:
            print(f"❌ Tavily search failed: {e}")
            return {"error": f"Fehler bei der Tavily-Suche: {str(e)}"}

    def get_stock_data(self, ticker: str, period: str = "1y") -> Dict:
        """Holt Aktiendaten von Yahoo Finance"""
        # (Diese Funktion bleibt unverändert)
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period=period)
            
            # Prüfen, ob Daten zurückkamen
            if not info or info.get('quoteType') == 'NONE':
                 return {"error": f"Keine Daten für Ticker {ticker} gefunden."}

            fundamentals = { "ticker": ticker, "name": info.get("longName", "N/A"), ... }
            valuation = { "current_price": info.get("currentPrice", "N/A"), ... }
            # ... (Rest der Datensammlung) ...
            
            return {
                "source": "Yahoo Finance (yfinance)", "fundamentals": fundamentals, ...
            }
        except Exception as e:
            return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}

    # --- HIER IST ÄNDERUNG 1: Bessere Fehlerprüfung ---
    def get_crypto_data(self, symbol: str) -> Dict:
        """Holt Krypto-Daten von CoinGecko (IN EUR)"""
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{symbol.lower()}"
            response = requests.get(url, timeout=10)
            
            # NEU: Explizite Fehlerprüfung des Status-Codes
            if response.status_code != 200:
                print(f"❌ CoinGecko API request failed with status {response.status_code}")
                return {"error": f"CoinGecko API request failed with status code {response.status_code} (Likely Rate-Limiting)"}
            
            data = response.json()
            
            # NEU: Prüfen, ob der 'market_data' Key fehlt (Zeichen für Rate-Limit)
            market_data = data.get("market_data", {})
            if not market_data:
                print("❌ CoinGecko returned 200 OK, but 'market_data' key is missing.")
                return {"error": "CoinGecko API returned no market_data. (Likely Rate-Limiting)"}
                
            return {
                "source": "CoinGecko API", "symbol": symbol, "name": data.get("name", "N/A"),
                "current_price_eur": market_data.get("current_price", {}).get("eur", "N/A"),
