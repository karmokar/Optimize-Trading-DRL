import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
import numpy as np
import warnings
from tqdm import tqdm

warnings.filterwarnings('ignore')

def fetch_sector_mapping(tickers):
    """Fetches sector metadata from yfinance for the given tickers."""
    print(f"Fetching sector data for {len(tickers)} stocks (this takes a minute).....")
    sector_map={}
    for ticker in tqdm(tickers):
        try:
            info =yf.Ticker(f"{ticker}.NS").info
            sector_map[ticker]=info.get('sector','unknown')
        except Exception:
            sector_map[ticker]='Unknown'
    return sector_map

def visualize_allocation():
    print("Loading agent action history.....")
    try:
        df=pd.read_csv("agent_actions_history.csv")
    except FileExistsError:
        print("Error: agent_actions_history.csv not found. Run phase3_train_eval.py first.")
        return

    tickers=df.columns.tolist()

    sector_map=fetch_sector_mapping(tickers)

    sector_df=pd.DataFrame()
    unique_sectors=set(sector_map.values())

    for sector in unique_sectors:
        stocks_in_sector=[ticker for ticker,sec in sector_map.items() if sec == sector]

        sector_df[sector]=df[stocks_in_sector].sum(axis=1)

    sector_df_smoothed=sector_df.rolling(window=20).mean().dropna()

    plt.figure(figsize=(16,8))
    plt.stackplot(sector_df_smoothed.index,sector_df_smoothed.T,labels=sector_df_smoothed.columns,alpha=0.8)
    plt.title("Agent Portfolio Allocation by Sector Overtime (20-Day Smoothed)",fontsize=14)
    plt.xlabel("Time (Trading Days)",fontsize=12)
    plt.ylabel("Combined Action Weights",fontsize=12)
    plt.legend(loc="upper left",bbox_to_anchor=(1.02,1),borderaxespad=0.)
    plt.margins(0,0)
    plt.tight_layout()
    plt.savefig("portfolio_sector_area_chart.png")
    print("\nSaved sector area chart to 'portfolio_sector_area_chart.png'")

    print("Generating Heatmap...")

    monthly_avg=df.groupby(np.arange(len(df))//20).mean()

    plt.figure(figsize=(20,12))

    sns.heatmap(monthly_avg.T, cmap="RdYlGn", center=0, yticklabels=True,xticklabels=False, cbar_kws={'label':'Portfolio Weight'})
    plt.title("Agent Indvidual Stocks Weight Over Time (Monthly Average)",fontsize=16)
    plt.xlabel("Time (Trading Months)",fontsize=12)
    plt.tight_layout()
    plt.savefig("portfolio_heatmap.png")
    print("Saved stock heatmap to 'portfolio_heatmap.png'")

if __name__ == "__main__":
    visualize_allocation()

