import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd


class PortfolioTradingEnv(gym.Env):
    """A single agent that allocates capital across N stocks simultaneously.
 
    Expects `df` to be a wide DataFrame indexed by date, with columns
    named '{TICKER}_Close', '{TICKER}_SMA_20', '{TICKER}_SMA_50' for each
    ticker in `tickers`. Use build_portfolio_dataframe() to construct this
    from per-ticker data.
    """
    metadata = {'render_modes': ['human']}

    def __init__(self, df,tickers, initial_balance=10000, transaction_cost_pct=0.001):
        super(PortfolioTradingEnv, self).__init__()

        if len(df) < 2:
            raise ValueError(
                f"StockTradingEnv needs at least 2 rows of data, got {len(df)}. "
                "Check your train/test split dates against your actual data range."
            )
        self.df = df.reset_index(drop=True)
        self.tickers=tickers
        self.n_assets=len(tickers)
        self.initial_balance = initial_balance
        self.transaction_cost_pct = transaction_cost_pct
        self.current_step = 0

        self.balance = self.initial_balance
        self.shares_held = np.zeros(self.n_assets)
        self.net_worth = self.initial_balance
        self.max_net_worth = self.initial_balance

        # Each dimension = target allocation weight for that stock, roughly
        # -1 (fully exit that position) to 1 (put as much as possible into it).
        # Weights are normalized inside _take_action so they always sum sanely.
        self.action_space = spaces.Box(low=-1.0,high=1.0,shape=(self.n_assets,),dtype=np.float32)

       # Per stock: [Close, SMA_20, SMA_50, shares_held] + 1 for balance
        self.obs_shape=self.n_assets*4+1
        self.observation_space=spaces.Box(low=-np.inf,high=np.inf,shape=(self.obs_shape,),dtype=np.float32)


    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.balance = self.initial_balance
        self.shares_held = np.zeros(self.n_assets)
        self.net_worth = self.initial_balance
        self.max_net_worth = self.initial_balance
        self.current_step = 0

        return self._next_observation(), {}

    def _get_prices(self,step):
        row=self.df.iloc[step]
        return np.array([row[f"{t}_Close"] for t in self.tickers],dtype=np.float64)

    def _next_observation(self):
        row=self.df.iloc[self.current_step]
        obs=[]
        for t in self.tickers:
            obs.append(row[f"{t}_Close"])
            obs.append(row[f"{t}_SMA_20"])
            obs.append(row[f"{t}_SMA_50"])
        obs.extend(self.shares_held.tolist())
        obs.append(self.balance)
        return np.array(obs,dtype=np.float32)

    def step(self, action):
        self._take_action(action)
        self.current_step += 1

        terminated = self.current_step >= len(self.df) - 1
        truncated = self.net_worth <= 0

        # reward should be the INCREMENTAL change in net worth, not the raw
        # (huge, ever-growing) gap from the initial balance
        prev_net_worth = self.net_worth
        prices=self._get_prices(min(self.current_step,len(self.df)-1))
        self.net_worth = self.balance + float(np.dot(self.shares_held,prices))
        reward = self.net_worth - prev_net_worth

        if self.net_worth > self.max_net_worth:
            self.max_net_worth = self.net_worth

        if self.net_worth < self.max_net_worth * 0.8:
            reward -= 1000

        obs = self._next_observation()
        info = {'net_worth': self.net_worth}

        # Gymnasium convention: (obs, reward, terminated, truncated, info)
        return obs, reward, terminated, truncated, info

    def _take_action(self, action):
        prices=self._get_prices(self.current_step)
           # Normalize raw actions into portfolio weights that sum to at most 1
        # (so the agent can't "spend" more than 100% of its balance at once)
        weight=np.clip(action,-1.0,1.0)
        positive=np.clip(weight,0,None)
        total_positive=positive.sum()
        buy_weights=positive/total_positive if total_positive>0 else positive

        total_equity=self.balance+float(np.dot(self.shares_held,prices))
        for i in range(self.n_assets):
            w=weight[1]
            price=prices[i]
            if price<=0 or np.isnan(price):
                continue

            if w>0:
                target_value=total_equity*buy_weights[i]*abs(w)
                investment=min(target_value,self.balance)
                if investment <=0:
                    continue
                shares_bought=investment/price
                cost=investment*self.transaction_cost_pct
                self.balance-=(investment+cost)
                self.shares_held[i]+=shares_bought

            elif w<0:
                shares_sold=self.shares_held[i]*abs(w)
                revenue=shares_sold*price
                cost=revenue*self.transaction_cost_pct
                self.balance+=(revenue-cost)
                self.shares_held[i]-=shares_sold

        self.net_worth=self.balance+float(np.dot(self.shares_held,prices))
        if self.net_worth>self.max_net_worth:
            self.max_net_worth=self.net_worth