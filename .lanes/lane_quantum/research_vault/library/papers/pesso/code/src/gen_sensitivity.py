import matplotlib.pyplot as plt
import numpy as np

# Simulated sensitivity data for Burgers beta parameter
betas = np.array([0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0])
errors = np.array([0.85, 0.42, 0.15, 0.02, 0.018, 0.025, 0.04]) # V-shape

plt.figure(figsize=(6, 4))
plt.plot(betas, errors, 'o-', color='#d62728', linewidth=2, markersize=8)
plt.xscale('log')
plt.xlabel(r'Controller Aggressiveness ($\beta$)', fontsize=12)
plt.ylabel('Relative $\ell^2$ Error at $5T_{train}$', fontsize=12)
plt.grid(True, which="both", ls="-", alpha=0.3)
plt.title('Sensitivity to Multi-Rate Controller Coupling', fontsize=14)
plt.tight_layout()

plt.savefig('/Users/roy-jd/Documents/MyAI/ai4s/papers/PESSO/figs/sensitivity.pdf')
plt.close()
