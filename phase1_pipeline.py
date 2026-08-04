import yfinance as yf
import pandas as pd
import warnings

from Nifity50list import get_nifity50_tickers

warnings.filterwarnings('ignore')


def build_portfolio_dataframe(tickers=None, start="2020-01-01", end="2026-01-01"):
    """Fetch each ticker's price history and assemble one wide DataFrame,
    indexed by date, with '{TICKER}_Close', '{TICKER}_SMA_20', '{TICKER}_SMA_50'
    columns per stock. Stocks missing data on the common date range are dropped.
    """
    if tickers is None:
        tickers=get_nifity50_tickers()

    per_stock_frames=[]
    kept_tickers=[]

    for ticker in tickers:
        print(f"fetching {ticker}...")
        try:
            df=yf.download(ticker, start=start,end=end,progress=False)
            if isinstance(df.columns,pd.MultiIndex):
                df.columns=df.columns.get_level_values(0)
            if df.empty or len(df)<60:
                print(f"skipping {ticker}: insufficient data ({len(df)}rows)")
                continue

            df =df[['Close']].copy()
            df['SMA_20']=df['Close'].rolling(window=20).mean()
            df['SMA_50']=df['Close'].rolling(window=50).mean()
            df.dropna(inplace=True)
            df.index=pd.to_datetime(df.index).tz_localize(None)

            # Skip stocks that don't actually cover most of the target range
            # (recent IPOs/demergers/relistings) - one of these in an inner
            # join would otherwise crush the whole combined dataset down to
            # just its short overlap.
            target_start=pd.Timestamp(start)
            if df.index.min()>target_start+pd.Timedelta(days=90):
                print(f" skipping {ticker}data only starts {df.index.min().date()},"f"too late for target start{target_start.date()}")
                continue

            key = ticker.replace('.NS','')
            df.columns=[f"{key}_Close",f"{key}_SMA_20",f"{key}_SMA_50"]
            per_stock_frames.append(df)
            kept_tickers.append(key)
        except Exception as e:
            print(f" skipping {ticker}:{e}")

    if not per_stock_frames:
        raise RuntimeError("No ticker data was successfully fetched.")

     # Inner join on date so every row has complete data for every kept stock
    combined = per_stock_frames[0]
    for frame in per_stock_frames[1:]:
        combined = combined.join(frame,how='inner')

    print(f"\nBuilt portfolio dataframe: {len(kept_tickers)} stocks, {len(combined)} common trading days")
    return combined,kept_tickers


    
if __name__ == "__main__":
    df,tickers=build_portfolio_dataframe()
    print(df.tail())