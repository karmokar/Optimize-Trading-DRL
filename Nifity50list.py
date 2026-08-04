import requests
import pandas as pd
import io

NSE_NIFTY50_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"

_FALLBACK_SYMBOLS=[
     "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "HINDUNILVR", "ITC",
    "SBIN", "BHARTIARTL", "BAJFINANCE", "KOTAKBANK", "LT", "AXISBANK",
    "ASIANPAINT", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND",
    "WIPRO", "ONGC", "NTPC", "POWERGRID", "M&M", "TATAMOTORS", "TATASTEEL",
    "ADANIENT", "ADANIPORTS", "JSWSTEEL", "HCLTECH", "TECHM", "BAJAJFINSV",
    "GRASIM", "CIPLA", "DRREDDY", "EICHERMOT", "BPCL", "COALINDIA",
    "DIVISLAB", "HEROMOTOCO", "HINDALCO", "INDUSINDBK", "APOLLOHOSP",
    "BAJAJ-AUTO", "BRITANNIA", "SBILIFE", "HDFCLIFE", "UPL", "SHREECEM",
    "TATACONSUM", "LTIM",
]

def get_nifity50_tickers():
      """Returns Nifty 50 symbols with the .NS suffix yfinance expects."""
      try:
           headers={"User-Agent":"Mozilla/5.0"}
           session=requests.Session()
           session.headers.update(headers)
           session.get("https://www.nseindia.com",timeout=5)
           resp=session.get(NSE_NIFTY50_URL,timeout=10)
           resp.raise_for_status()
           df=pd.read_csv(io.BytesIO(resp.content))
           symbols=df['Symbol'].tolist()
           print(f"Fetched {len(symbols)} live Nifty 50 constituents from NSE.")           
      except Exception as e:
             print(f"Could not fetch live NSE list ({e}); using fallback list.")
             symbols=_FALLBACK_SYMBOLS
      return [f"{s}.NS" for s in symbols]

if __name__ =="__main__":
      tickers=get_nifity50_tickers()
      print(tickers)
      
