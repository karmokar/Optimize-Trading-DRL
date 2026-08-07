import requests
import pandas as pd
import io

NSE_INDEX_URLS = {
    "nifty50": "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
    "nifty100": "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv",
}

# Fallback used only if the live NSE request fails (e.g. blocked, network down).
# NOTE: this fallback list only has ~50 symbols even for "nifty100" - it's a
# safety net so the pipeline doesn't crash, not a real substitute for the
# live 100-stock list. The live NSE fetch should be preferred whenever possible.
_FALLBACK_SYMBOLS = [
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


def get_index_tickers(index="nifty50"):
    """Returns constituent symbols for the given NSE index, with the .NS
    suffix yfinance expects. `index` is one of: 'nifty50', 'nifty100'."""
    if index not in NSE_INDEX_URLS:
        raise ValueError(f"Unknown index '{index}'. Choose from: {list(NSE_INDEX_URLS)}")

    url = NSE_INDEX_URLS[index]
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests.Session()
        session.headers.update(headers)
        # NSE requires an initial visit to set cookies before the CSV request works
        session.get("https://www.nseindia.com", timeout=5)
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(io.BytesIO(resp.content))
        symbols = df["Symbol"].tolist()
        print(f"Fetched {len(symbols)} live {index} constituents from NSE.")
    except Exception as e:
        print(f"Could not fetch live NSE {index} list ({e}); using fallback list.")
        symbols = _FALLBACK_SYMBOLS

    return [f"{s}.NS" for s in symbols]


def get_nifity50_tickers():
    """Kept for backward compatibility with existing imports."""
    return get_index_tickers("nifty50")


def get_nifty100_tickers():
    return get_index_tickers("nifty100")


if __name__ == "__main__":
    tickers = get_nifty100_tickers()
    print(f"{len(tickers)} tickers:")
    print(tickers)