import pandas as pd
import numpy as np
from phase1_pipeline import build_portfolio_dataframe

def analyze_trades():
    print("Loading market data agent history...")
    df,kept_tickers=build_portfolio_dataframe()

    try:
        actions_df=pd.read_csv("agent_action_history.csv")
    except FileExistsError:
        print("Could not find agent_actions_history.csv. Did you run the eval loop?")
        return

    close_cols=[f"{t}_close"for t in kept_tickers]
    prices_df=df[close_cols].copy()

    min_len=min(len(prices_df),len(actions_df))
    prices_df=prices_df.iloc[:min_len].reset_index()
    actions_df=actions_df.iloc[:min_len]

    daily_returns=prices_df[close_cols].pct_changes().shfit(-1)
    daily_returns.columns=kept_tickers
    daily_contributions=actions_df*daily_returns

    total_contributions=daily_contributions.sum().sort_values(ascending=False)

    print("\n" + "="*40)
    print("🏆 TOP 5 MOST PROFITABLE STOCKS 🏆")
    print("="*40)
    for stock, return_val in total_contributions.head(5).items():
        print(f"{stock}: +{return_val*100:.2f}% contribution")

    print("\n" + "="*40)
    print("📉 TOP 5 BIGGEST LOSERS 📉")
    print("="*40)
    for stock, return_val in total_contributions.tail(5).items():
        print(f"{stock}: {return_val*100:.2f}% contribution")

if __name__ == "__main__":
    analyze_trades()

