import os
import warnings
import pandas as pd
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
import pyfolio as pf

from portfolio_env import PortfolioTradingEnv
from phase2_portfolio_env import build_portfolio_envs

warnings.filterwarnings('ignore')

PPO_PARAMS = {
    "n_steps": 2048,
    "ent_coef": 0.01,
    "learning_rate": 0.00025,
    "batch_size": 128,
}


def train_and_evaluate(total_timesteps=50000):
    train_df, test_df, tickers, env_train_fn = build_portfolio_envs()

    # --- train ---
    env_train = DummyVecEnv([env_train_fn])
    env_train = VecNormalize(env_train, norm_obs=True, norm_reward=True, clip_obs=10.0)
    print(f'\nTraining PPO agent on {len(tickers)}-stock portfolio...')
    model = PPO("MlpPolicy", env_train, verbose=1, **PPO_PARAMS)
    model.learn(total_timesteps=total_timesteps)

    os.makedirs("./trained_models", exist_ok=True)
    model.save("./trained_models/ppo_portfolio_agent")
    env_train.save("./trained_models/vecnormalize_portfolio_stats.pkl")
    print("Training complete! Saved trained policy model + normalization stats.")

    # --- out-of-sample backtest ---
    print("\nExecuting out-of-sample backtest on unseen data...")
    env_test_raw = DummyVecEnv([lambda: PortfolioTradingEnv(test_df, tickers)])
    env_test = VecNormalize.load("./trained_models/vecnormalize_portfolio_stats.pkl", env_test_raw)
    env_test.training = False
    env_test.norm_reward = False

    obs = env_test.reset()
    net_worths = []
    dates = test_df.index.tolist()
    for i in range(len(test_df) - 1):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, info = env_test.step(action)
        net_worths.append(info[0]['net_worth'])
        if done[0]:
            break

    df_account_value = pd.DataFrame({
        'date': dates[1:len(net_worths) + 1],
        'account_value': net_worths
    }).set_index('date')
    agent_returns = df_account_value['account_value'].pct_change().dropna()

    # Benchmark: equal-weight buy-and-hold across all tickers
    close_cols = [f"{t}_Close" for t in tickers]
    equal_weight_index = test_df[close_cols].div(test_df[close_cols].iloc[0]).mean(axis=1)
    benchmark_returns = equal_weight_index.pct_change().dropna()

    common_dates = agent_returns.index.intersection(benchmark_returns.index)
    agent_returns = agent_returns.loc[common_dates]
    benchmark_returns = benchmark_returns.loc[common_dates]

    # sanity check the two series before handing them to pyfolio
    benchmark_returns.name="Nifity50_EqualWeight"
    agent_total_return=(1+agent_returns).prod()-1
    bench_total_return=(1+benchmark_returns).prod()-1
    print(f"\nCommon dates for comparison: {len(common_dates)}")
    print(f"Agent total return:     {agent_total_return:.2%}")
    print(f"Benchmark total return: {bench_total_return:.2%}")
    print(f"Agent daily returns  - mean: {agent_returns.mean():.5f}, std: {agent_returns.std():.5f}")
    print(f"Benchmark daily returns - mean: {benchmark_returns.mean():.5f}, std: {benchmark_returns.std():.5f}")

    # --- pyfolio tear sheet ---
    print('\nGenerating performance tear sheet...')
    pf.create_returns_tear_sheet(
        returns=agent_returns,
        benchmark_rets=benchmark_returns
    )
    plt.savefig("portfolio_backtest_tear_sheet.png")
    print("Tear sheet saved as 'portfolio_backtest_tear_sheet.png'!")

    return model, agent_returns, benchmark_returns


if __name__ == "__main__":
    train_and_evaluate()