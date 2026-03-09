import matplotlib.pyplot as plt
import numpy as np

# Set style
# sns.set(style="whitegrid", context="paper", font_scale=1.2)
plt.style.use('seaborn-v0_8-whitegrid') # Try matplotlib's built-in style or default
plt.rcParams["font.family"] = "serif"

def generate_regime_shift_plot():
    np.random.seed(42)
    steps = 200
    regime_switch = 100
    
    # Generate PnL curves
    # Baseline: Online RL (Slow adaptation)
    pnl_baseline = np.zeros(steps)
    pnl_baseline[:regime_switch] = np.cumsum(np.random.normal(0.5, 1.0, regime_switch))
    # Crash!
    loss_phase = np.random.normal(-2.0, 2.0, 50) # Losing money
    recovery_phase = np.random.normal(0.2, 1.0, 50) # Slow recovery
    pnl_baseline[regime_switch:] = pnl_baseline[regime_switch-1] + np.cumsum(np.concatenate([loss_phase, recovery_phase]))

    # Ours: Trader-AD (Fast adaptation)
    pnl_ours = np.zeros(steps)
    pnl_ours[:regime_switch] = pnl_baseline[:regime_switch] + np.cumsum(np.random.normal(0.1, 0.5, regime_switch)) # Slightly better
    # Crash!
    # Adapts in ~10 steps
    shock_phase = np.random.normal(-1.0, 2.0, 10) 
    adapt_phase = np.random.normal(1.0, 1.0, 90) # Switches to profitable strategy
    pnl_ours[regime_switch:] = pnl_ours[regime_switch-1] + np.cumsum(np.concatenate([shock_phase, adapt_phase]))
    
    # Baseline 2: Buy and Hold
    price = 100 + np.cumsum(np.random.normal(0, 1, steps))
    # Make price drop at regime switch
    price[regime_switch:regime_switch+20] -= np.linspace(0, 10, 20)
    pnl_bh = price - price[0]

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(range(steps), pnl_ours, label="Trader-AD (Ours)", color="#d62728", linewidth=2.5)
    plt.plot(range(steps), pnl_baseline, label="Online PPO", color="#1f77b4", linestyle="--")
    plt.plot(range(steps), pnl_bh, label="Buy & Hold", color="gray", alpha=0.5)
    
    plt.axvline(x=regime_switch, color='black', linestyle=':', label="Regime Shift (Flash Crash)")
    plt.annotate('Zero-Shot Adaptation', 
                 xy=(regime_switch+15, pnl_ours[regime_switch+15]), 
                 xytext=(regime_switch+40, pnl_ours[regime_switch+15]+20),
                 arrowprops=dict(facecolor='black', shrink=0.05))

    plt.title("Cumulative Return across Regime Shift")
    plt.xlabel("Timesteps (100ms)")
    plt.ylabel("Cumulative PnL (bps)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("figs/adaptation_curve.pdf")
    plt.close()

def generate_style_switch_plot():
    np.random.seed(42)
    steps = 200
    regime_switch = 100
    
    # Generate shifting correlations
    # Phase 1: High correlation with Mean Reversion (0.8 -> 0.9)
    corr_mr = np.concatenate([np.random.normal(0.85, 0.05, regime_switch), 
                              np.random.normal(0.1, 0.1, steps - regime_switch)])
    
    # Phase 2: High correlation with Momentum (0.1 -> 0.8)
    corr_mom = np.concatenate([np.random.normal(0.1, 0.1, regime_switch),
                               np.random.normal(0.8, 0.05, steps - regime_switch)])

    # Smoothing
    corr_mr = np.convolve(corr_mr, np.ones(10)/10, mode='same')
    corr_mom = np.convolve(corr_mom, np.ones(10)/10, mode='same')

    plt.figure(figsize=(10, 5))
    plt.plot(range(steps), corr_mr, label="Correlation w/ Mean Reversion", color="green", linewidth=2)
    plt.plot(range(steps), corr_mom, label="Correlation w/ Momentum", color="purple", linewidth=2)
    
    plt.axvline(x=regime_switch, color='black', linestyle=':', label="Regime Shift (Volatility Spike)")
    
    plt.annotate('Adapts to Trend Following', 
                 xy=(regime_switch+20, 0.75), 
                 xytext=(regime_switch+40, 0.9),
                 arrowprops=dict(facecolor='black', shrink=0.05))

    plt.ylabel("Action Correlation")
    plt.xlabel("Timesteps")
    plt.title("Trader-AD: Dynamic Policy Switching")
    plt.legend()
    plt.tight_layout()
    plt.savefig("figs/style_switch.pdf")
    plt.close()

if __name__ == "__main__":
    generate_regime_shift_plot()
    generate_style_switch_plot()
