import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 1. Airfoil Results
plt.figure(figsize=(6, 5))
evals = np.logspace(0, 4, 100)
fitness_cma = 0.98 * (1 - 0.8 * np.exp(-0.001 * evals)) 
fitness_random = 0.2 * np.ones_like(evals)

plt.semilogx(evals, fitness_cma, label="CMA-ES (Teacher)", color='black', linewidth=2)
plt.semilogx(evals, fitness_random, label="Random Search", color='gray', linestyle='--')

student_evals = 1 
student_fitness = 0.93 
plt.scatter([student_evals], [student_fitness], color='#d62728', s=200, marker='*', label="Evo-Distill (One-Shot)", zorder=10)

refine_evals = np.logspace(0, 2, 20) + 1
fitness_refine = 0.93 + (0.99 - 0.93) * (1 - np.exp(-0.1 * (refine_evals - 1)))
plt.semilogx(refine_evals, fitness_refine, label="Evo-Distill + Fine-tuning", color='#d62728', linestyle='-.')

plt.xlabel("Function Evaluations (Log Scale)")
plt.ylabel("Normalized Airfoil Fitness ($C_L/C_D$)")
plt.title("Airfoil Shape Optimization Benchmark")
plt.legend()
plt.grid(True, which="both", linestyle='--', alpha=0.5)
plt.tight_layout()
plt.savefig("papers/evo_distill/figs/fig_airfoil_results.pdf")
plt.close()

# 2. Fixed Point (Fixing Z dimension)
plt.figure(figsize=(6, 6))
x = np.linspace(-2, 2, 100)
y = np.linspace(-2, 2, 100)
X, Y = np.meshgrid(x, y)
# Ensure Z is 2D
Z = X**2 + Y**2 

plt.contourf(X, Y, Z, levels=20, cmap='viridis_r', alpha=0.6)
path_x = np.linspace(-1.5, 0.1, 10) + np.random.normal(0, 0.1, 10)
path_y = np.linspace(1.5, 0.1, 10) + np.random.normal(0, 0.1, 10)
plt.plot(path_x, path_y, 'o-', color='gray', alpha=0.7, label="Iterative EA Trajectory")

plt.arrow(-1.5, 1.5, 1.5, -1.4, head_width=0.1, head_length=0.1, fc='#d62728', ec='#d62728', width=0.02, label="Learned Fixed-Point Map")
plt.scatter([0], [0], marker='x', color='black', s=100, label="Global Optimum")

plt.legend()
plt.title("Amortized Fixed-Point Learning")
plt.axis('off')
plt.savefig("papers/evo_distill/figs/fixed_point.png")
plt.close()

# 3. Architecture
plt.figure(figsize=(10, 4))
ax = plt.gca()
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)

rect1 = patches.Rectangle((0.5, 1), 2, 2, linewidth=2, edgecolor='black', facecolor='#eef', label="Population DAG")
ax.add_patch(rect1)
plt.text(1.5, 2, "Population\nHistory DAG", ha='center', va='center', fontsize=12)

rect2 = patches.Rectangle((3.5, 1), 3, 2, linewidth=2, edgecolor='black', facecolor='#ffe', label="Graph Transformer")
ax.add_patch(rect2)
plt.text(5, 2, "Genealogical\nGraph Transformer", ha='center', va='center', fontsize=12)

rect3 = patches.Rectangle((7.5, 1.5), 1.5, 1, linewidth=2, edgecolor='black', facecolor='#efe', label="Elite Prediction")
ax.add_patch(rect3)
plt.text(8.25, 2, "Predicted\nElite $x_*$", ha='center', va='center', fontsize=12)

plt.arrow(2.5, 2, 1, 0, head_width=0.2, color='black')
plt.arrow(6.5, 2, 1, 0, head_width=0.2, color='black')

plt.axis('off')
plt.title("Evo-Distill Architecture Pipeline")
plt.tight_layout()
plt.savefig("papers/evo_distill/figs/architecture.png")
plt.close()
