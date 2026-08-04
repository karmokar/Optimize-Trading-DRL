import warnings
from portfolio_env import PortfolioTradingEnv
from phase1_pipeline import build_portfolio_dataframe

warnings.filterwarnings('ignore')


def build_portfolio_envs(split_date="2025-01-01"):
    df, tickers = build_portfolio_dataframe()
 
    train_df = df[df.index < split_date].copy()
    test_df = df[df.index >= split_date].copy()
    print(f"Dataset split! Training rows: {len(train_df)}, Testing rows: {len(test_df)}")
 
    def env_train_fn():
        return PortfolioTradingEnv(train_df, tickers)
 
    return train_df, test_df, tickers, env_train_fn
 
 
if __name__ == "__main__":
    train_df, test_df, tickers, env_train_fn = build_portfolio_envs()
    env = env_train_fn()
    obs, info = env.reset()
    print(f"\nPortfolio env built OK. {len(tickers)} stocks, obs shape: {obs.shape}")
    