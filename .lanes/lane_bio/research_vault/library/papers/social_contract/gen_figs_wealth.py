import numpy as np
import matplotlib.pyplot as plt

# Simulate Data
t = np.linspace(0, 100, 200)
# Gini Dynamics
gini_naive = 0.3 + 0.65 * (1 - np.exp(-0.05 * t)) + 0.02 * np.random.randn(len(t))
gini_tax = 0.3 + 0.2 * (1 - np.exp(-0.1 * t)) + 0.02 * np.random.randn(len(t))
gini_csc = 0.3 + 0.05 * np.sin(0.1 * t) + 0.01 * np.random.randn(len(t)) 

# 1. Gini Coefficient over Time
plt.figure(figsize=(6, 5))
plt.plot(t, gini_naive, label="Naive-RL (Laissez-faire)", color='#21918c', linewidth=2.5)
plt.plot(t, gini_tax, label="Classical Tax", color='#440154', linewidth=2.5, linestyle="--")
plt.plot(t, gini_csc, label="CSC + AVoI", color='#fde725', linewidth=3)

plt.xlabel("Training Episodes (x100)")
plt.ylabel("Wealth Gini Coefficient")
plt.title("Evolution of Inequality")
plt.legend()
plt.ylim(0.2, 1.0)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig("papers/social_contract/fig_gini_placeholder.pdf")
plt.close()

# 2. Output vs Inequality Trade-off
plt.figure(figsize=(6, 5))

# Generate scatter points
n_points = 20
np.random.seed(42)
# Naive: High output, High inequality
naive_x = np.random.normal(0.9, 0.03, n_points) # Gini
naive_y = np.random.normal(1.0, 0.05, n_points) # Output (Normalized)

# Tax: Moderate inequality, Lower output
tax_x = np.random.normal(0.5, 0.03, n_points)
tax_y = np.random.normal(0.6, 0.05, n_points)

# CSC: Low inequality, High output
csc_x = np.random.normal(0.3, 0.02, n_points)
csc_y = np.random.normal(0.95, 0.03, n_points)

plt.scatter(naive_x, naive_y, label="Naive-RL", color='#21918c', s=100, alpha=0.7)
plt.scatter(tax_x, tax_y, label="Classical Tax", color='#440154', s=100, alpha=0.7, marker="s")
plt.scatter(csc_x, csc_y, label="CSC + AVoI", color='#fde725', s=150, alpha=0.9, marker="*")

plt.xlabel("Wealth Gini Coefficient")
plt.ylabel("Relative Productivity (vs Laissez-faire)")
plt.title("Equity-Efficiency Frontier")
plt.legend(loc="lower left")
plt.grid(True, linestyle="--", alpha=0.6)
plt.tight_layout()
plt.savefig("papers/social_contract/fig_output_placeholder.pdf")
plt.close()

print("Figures generated successfully using pure matplotlib.")
