import os
import numpy as np
import pandas as pd
import yfinance as yf
from stable_baselines3 import PPO
from transformers import pipeline
from portfolio_env import PortfolioTradingEnv
import warnings

warnings.filterwarnings('ignore')

MODEL_PATH = "trained_models/ppo_portfolio_agent.zip"
SENTIMENT_THRESHOLD = -1.0  # Trigger threshold for flagging a veto

def load_sentiment_pipeline():
    print("Loading FinBERT sentiment engine...")
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

def get_live_sentiment(ticker_symbol, sentiment_model, max_articles=5):
    """Fetches recent news and calculates net sentiment score using FinBERT."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        if not news:
            return 0.0, []
            
        headlines = []
        for article in news[:max_articles]:
            if 'title' in article:
                headlines.append(article['title'])
            elif 'content' in article and 'title' in article['content']:
                headlines.append(article['content']['title'])
                
        if not headlines:
            return 0.0, []
            
        results = sentiment_model(headlines)
        net_score = 0.0
        details = list(zip(headlines, results))
        for res in results:
            if res['label'] == 'positive':
                net_score += res['score']
            elif res['label'] == 'negative':
                net_score -= res['score']
                
        return net_score, details
    except Exception as e:
        print(f"  [Warning] Could not fetch news for {ticker_symbol}: {e}")
        return 0.0, []

def run_hybrid_veto_system():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}. Train and save the model first.")
        
    print(f"Loading trained PPO model from {MODEL_PATH}...")
    model = PPO.load(MODEL_PATH)
    
    sentiment_model = load_sentiment_pipeline()
    
    from Nifity50list import get_nifty100_tickers
    tickers = get_nifty100_tickers()
    
    print("Fetching latest market state for portfolio evaluation...")
    
    per_stock_frames = []
    kept_tickers = []
    
    for ticker in tickers:
        try:
            # Using period="3m" avoids Yahoo Finance start/end date parsing bugs
            df = yf.download(ticker, period="3mo", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 30:
                continue
                
            df = df[['Close']].copy()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df.dropna(inplace=True)
            df.index = pd.to_datetime(df.index).tz_localize(None)
            
            key = ticker.replace('.NS', '')
            df.columns = [f"{key}_Close", f"{key}_SMA_20", f"{key}_SMA_50"]
            per_stock_frames.append(df)
            kept_tickers.append(key)
        except Exception:
            continue
            
    if not per_stock_frames:
        raise RuntimeError("Failed to fetch market data. Check your network connection.")
        
    print(f"\nSuccessfully processed {len(kept_tickers)} active stocks.")
    
    print("\n==================================================")
    print(" RUNNING HYBRID SENTIMENT GUARDRAIL & VETO CHECK")
    print("==================================================")
    
    final_portfolio = {}
    cash_buffer = 0.0
    
    print("\n--- Initializing Environment with Live Data ---")

    env=PortfolioTradingEnv(df=combined)

    obs,=env.reset()

    done =False
    while not done:

        action,_=model.predict(obs,deterministic=True)

        
        
        print(f"\nStock: {ticker} | Agent Target: {target_weight*100:.1f}% | Net Sentiment: {score:+.2f}")
        
        if score < SENTIMENT_THRESHOLD:
            print(f"🛑 [VETO ALERT] Negative sentiment threshold breached ({score:.2f})!")
            if details:
                print("   Recent Headline Sample:")
                print(f"     -> [{details[0][1]['label'].upper()} ({details[0][1]['score']:.2f})] {details[0][0]}")
            
            choice = input(f"   Do you want to VETO and block the trade for {ticker}? ([y]/N override): ").strip().lower()
            
            if choice == 'n':
                print(f"   ✅ [OVERRIDE] Human operator bypassed veto. Executing trade for {ticker}.")
                final_portfolio[ticker] = target_weight
            else:
                print(f"   🛑 [CONFIRMED] Trade blocked. Rerouting allocation to cash reserve.")
                cash_buffer += target_weight
        else:
            print(f"   ✅ [APPROVED] Sentiment within safe limits. Clear to execute.")
            final_portfolio[ticker] = target_weight

    print("\n==================================================")
    print(" FINAL EXECUTABLE PORTFOLIO (AFTER HYBRID VETOS):")
    print("==================================================")
    for stock, weight in final_portfolio.items():
        print(f"  {stock}: {weight*100:.1f}%")
    print(f"  CASH RESERVE: {cash_buffer*100:.1f}%")
    print("==================================================")

if __name__ == "__main__":
    run_hybrid_veto_system()