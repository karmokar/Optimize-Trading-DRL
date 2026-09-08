import os
import numpy as np
import pandas as pd
import yfinance as yf
import feedparser
import urllib.parse
from stable_baselines3 import PPO
from transformers import pipeline
from portfolio_env import PortfolioTradingEnv
import warnings
import json
with open ("trained_models/training_tickers.json") as f:
    training_tickers=json.load(f)
tickers = [f"{t}.NS" for t in training_tickers]

warnings.filterwarnings('ignore')

MODEL_PATH = "trained_models/ppo_portfolio_agent.zip"
SENTIMENT_THRESHOLD = -1.0  # Trigger threshold for flagging a veto

def load_sentiment_pipeline():
    print("Loading FinBERT sentiment engine...")
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

def fetch_rss_news(query_keyword,max_articles=5):
    """Fetches clean headline strings from Google News RSS."""
    search_query=f"{query_keyword} Stock India"
    encoded_query=urllib.parse.quote(search_query)

    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed=feedparser.parse(rss_url)

    headlines=[]
    for entry in feed.entries[:max_articles]:
        if hasattr(entry,'title') and entry.title:
            headlines.append(entry.title)
    return headlines

TICKER_NAME_MAP = {
    "ABB": "ABB India",
    "ADANIENSOL": "Adani Energy Solutions",
    "ADANIENT": "Adani Enterprises",
    "ADANIPORTS": "Adani Ports and SEZ",
    "ADANIPOWER": "Adani Power",
    "AMBUJACEM": "Ambuja Cements",
    "APOLLOHOSP": "Apollo Hospitals",
    "ASIANPAINT": "Asian Paints",
    "AXISBANK": "Axis Bank",
    "BAJAJ-AUTO": "Bajaj Auto",
    "BAJFINANCE": "Bajaj Finance",
    "BAJAJFINSV": "Bajaj Finserv",
    "BAJAJHLDNG": "Bajaj Holdings & Investment",
    "BANKBARODA": "Bank of Baroda",
    "BEL": "Bharat Electronics",
    "BPCL": "Bharat Petroleum Corporation",
    "BHARTIARTL": "Bharti Airtel",
    "BOSCHLTD": "Bosch",
    "BRITANNIA": "Britannia Industries",
    "CGPOWER": "CG Power and Industrial Solutions",
    "CANBK": "Canara Bank",
    "CHOLAFIN": "Cholamandalam Investment and Finance",
    "CIPLA": "Cipla",
    "COALINDIA": "Coal India",
    "CUMMINSIND": "Cummins India",
    "DLF": "DLF",
    "DIVISLAB": "Divi's Laboratories",
    "DRREDDY": "Dr. Reddy's Laboratories",
    "EICHERMOT": "Eicher Motors",
    "GAIL": "GAIL India",
    "GODREJCP": "Godrej Consumer Products",
    "GRASIM": "Grasim Industries",
    "HCLTECH": "HCL Technologies",
    "HDFCBANK": "HDFC Bank",
    "HINDALCO": "Hindalco Industries",
    "HINDUNILVR": "Hindustan Unilever",
    "HINDZINC": "Hindustan Zinc",
    "ICICIBANK": "ICICI Bank",
    "ITC": "ITC Limited",
    "INDHOTEL": "Indian Hotels Company",
    "IOC": "Indian Oil Corporation",
    "INFY": "Infosys",
    "INDIGO": "InterGlobe Aviation IndiGo",
    "JSWSTEEL": "JSW Steel",
    "JINDALSTEL": "Jindal Steel & Power",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen & Toubro",
    "M&M": "Mahindra & Mahindra",
    "MARUTI": "Maruti Suzuki India",
    "MUTHOOTFIN": "Muthoot Finance",
    "NTPC": "NTPC",
    "NESTLEIND": "Nestle India",
    "ONGC": "Oil & Natural Gas Corporation ONGC",
    "PIDILITIND": "Pidilite Industries",
    "PFC": "Power Finance Corporation",
    "POWERGRID": "Power Grid Corporation of India",
    "PNB": "Punjab National Bank",
    "RECLTD": "REC Limited",
    "RELIANCE": "Reliance Industries",
    "MOTHERSON": "Samvardhana Motherson International",
    "SHREECEM": "Shree Cement",
    "SHRIRAMFIN": "Shriram Finance",
    "SIEMENS": "Siemens India",
    "SOLARINDS": "Solar Industries India",
    "SBIN": "State Bank of India",
    "SUNPHARMA": "Sun Pharmaceutical",
    "TVSMOTOR": "TVS Motor Company",
    "TCS": "Tata Consultancy Services",
    "TATACONSUM": "Tata Consumer Products",
    "TMPV": "Tata Motors",
    "TATAPOWER": "Tata Power",
    "TATASTEEL": "Tata Steel",
    "TECHM": "Tech Mahindra",
    "TITAN": "Titan Company",
    "TORNTPHARM": "Torrent Pharmaceuticals",
    "TRENT": "Trent Limited",
    "ULTRACEMCO": "UltraTech Cement",
    "UNIONBANK": "Union Bank of India",
    "UNITDSPR": "United Spirits",
    "VEDL": "Vedanta",
    "WIPRO": "Wipro",
    "ZYDUSLIFE": "Zydus Lifesciences"
}


def get_live_sentiment(ticker_symbol, sentiment_model, max_articles=5):
    """Fetches recent news via RSS and calculates net sentiment score using FinBERT."""
    clean_ticker=ticker_symbol.replace('.NS','')
    company_name=TICKER_NAME_MAP.get(clean_ticker,clean_ticker)
    try:
        
        headlines=fetch_rss_news(company_name,max_articles=max_articles)

        if not headlines:
            return 0.0,[]


        results=sentiment_model(headlines)
        net_score=0.0
        details=[]
                
        for headline,res in zip(headlines,results):
            label=res['label'].lower()
            score =float(res['score'])

            if label=='positive':
                net_score+=score
            elif label=='negative':
                net_score-=score

            details.append((headline,res))
        return net_score,details
    except Exception as e:
        print(f"  [FAIL] News fetch for {clean_ticker}: {type(e).__name__}: {e}")
        return 0.0, []


def run_hybrid_veto_system(auto_veto=False):
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}. Train and save the model first.")
        
    print(f"Loading trained PPO model from {MODEL_PATH}...")
    model = PPO.load(MODEL_PATH)
    
    sentiment_model = load_sentiment_pipeline()
    
    print("Fetching latest market state for portfolio evaluation...")
    
    per_stock_frames = []
    kept_tickers = []
    
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="3mo", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 30:
                continue
                
            df = df[['Close']].copy()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_Distance'] = df['SMA_20'] - df['SMA_50']
            df.dropna(inplace=True)
            df.index = pd.to_datetime(df.index).tz_localize(None)
            
            key = ticker.replace('.NS', '')
            df.columns = [f"{key}_Close", f"{key}_SMA_20", f"{key}_SMA_50", f"{key}_SMA_Distance"]
            per_stock_frames.append(df)
            kept_tickers.append(key)
        except Exception as e:
            print(f"  [FAIL] {ticker}: {type(e).__name__}: {e}")
            continue
            
    if not per_stock_frames:
        raise RuntimeError("Failed to fetch market data. Check your network connection.")
        
    # Join individual stock DataFrames into a single combined DataFrame
    combined = per_stock_frames[0]
    for frame in per_stock_frames[1:]:
        combined = combined.join(frame, how='inner')
        
    print(f"\nSuccessfully processed {len(kept_tickers)} active stocks across {len(combined)} trading days.")
    
    # Run model prediction on live environment
    print("\n--- Running RL Policy Inference on Current Market Data ---")
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    env_raw = DummyVecEnv([lambda: PortfolioTradingEnv(df=combined, tickers=kept_tickers)])
    env = VecNormalize.load("trained_models/vecnormalize_portfolio_stats.pkl", env_raw)
    env.training = False
    env.norm_reward = False
    obs = env.reset()
    
    done = [False]
    target_action = None
    
    while not done[0]:
        action, _ = model.predict(obs, deterministic=True)
        target_action = action[0]
        obs, reward, done, info = env.step(action)

    positive_action = np.clip(target_action, 0, None)
    action_sum = np.sum(positive_action)
    if action_sum > 0:
        normalized_weights = positive_action / action_sum
    else:
        normalized_weights = positive_action

    # Map weights to active stock tickers (> 1% allocation threshold)
    target_portfolio_raw = {}
    dust_weight = 0.0
    for i, ticker in enumerate(kept_tickers):
        if i < len(normalized_weights):
            w = float(normalized_weights[i])
            if w > 0.01:
                target_portfolio_raw[ticker] = w
            else:
                dust_weight += w

    target_portfolio_raw = dict(sorted(target_portfolio_raw.items(), key=lambda item: item[1], reverse=True))

    print(f"\nRL Agent selected {len(target_portfolio_raw)} stocks for portfolio allocation.")
    
    print("\n==================================================")
    print(" RUNNING HYBRID SENTIMENT GUARDRAIL & VETO CHECK")
    print("==================================================")
    
    final_portfolio = {}
    vetoed_trades = []
    cash_buffer = dust_weight
    
    for ticker, target_weight in target_portfolio_raw.items():
        symbol_ns = f"{ticker}.NS"
        score, details = get_live_sentiment(symbol_ns, sentiment_model)
        
        print(f"\nStock: {ticker:<12} | Agent Target: {target_weight*100:.1f}% | Net Sentiment: {score:+.2f}")
        
        if score < SENTIMENT_THRESHOLD:
            print(f"🛑 [VETO ALERT] Negative sentiment threshold breached ({score:.2f})!")
            
            if auto_veto:
                veto_confirmed = True
            else:
                choice = input(f"   Do you want to VETO and block the trade for {ticker}? ([y]/N override): ").strip().lower()
                veto_confirmed = (choice != 'n')
            
            if veto_confirmed:
                print(f"   🛑 [CONFIRMED] Trade blocked. Rerouting allocation to cash reserve.")
                cash_buffer += target_weight
                vetoed_trades.append({
                    "ticker": ticker,
                    "target_weight": round(target_weight * 100, 2),
                    "sentiment_score": round(score, 2),
                    "headline_sample": details[0][0] if details else "Negative news breach"
                })
            else:
                print(f"   ✅ [OVERRIDE] Executing trade for {ticker}.")
                final_portfolio[ticker] = round(target_weight * 100, 2)
        else:
            print(f"   ✅ [APPROVED] Sentiment within safe limits. Clear to execute.")
            final_portfolio[ticker] = round(target_weight * 100, 2)

    print("\n==================================================")
    print(" FINAL EXECUTABLE PORTFOLIO (AFTER HYBRID VETOS):")
    print("==================================================")
    for stock, weight in final_portfolio.items():
        print(f"  {stock:<12}: {weight:.1f}%")
    print(f"  CASH RESERVE: {cash_buffer*100:.1f}%")
    print("==================================================")

    # Return structured dict for FastAPI / external calls
    return {
        "active_allocations": final_portfolio,
        "cash_reserve": round(cash_buffer * 100, 2),
        "vetoed_trades": vetoed_trades
    }


if __name__ == "__main__":
    run_hybrid_veto_system(auto_veto=False)
if __name__ == "__main__":
    run_hybrid_veto_system()