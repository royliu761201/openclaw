import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.patheffects as path_effects

def create_architecture_diagram():
    # Use a style that looks professional
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans', 'Bitstream Vera Sans', 'sans-serif']
    
    fig = plt.figure(figsize=(10, 6.5))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')

    # Palette
    # Outer Loop (Governance) - Cool/Intellectual colors
    c_meta_bg = '#E8F5E9'     # Very light green
    c_meta_stroke = '#2E7D32' # Dark green
    c_meta_text = '#1B5E20'
    
    # Inner Loop (Economy) - Active/Dynamic colors
    c_econ_bg = '#E3F2FD'     # Very light blue
    c_econ_stroke = '#1565C0' # Dark blue
    c_econ_text = '#0D47A1'
    
    # Components
    c_agent_bg = '#FFF3E0'    # Light orange
    c_agent_stroke = '#EF6C00'
    c_prod_bg = '#F5F5F5'     # Light gray
    c_prod_stroke = '#424242'

    # --- ZONES ---
    
    # 1. Governance Zone (Top)
    # y=0.64 to 0.99 (height 0.35)
    rect_gov = patches.FancyBboxPatch((0.05, 0.64), 0.9, 0.33, boxstyle="round,pad=0.03,rounding_size=0.05", 
                                      linewidth=2.5, edgecolor=c_meta_stroke, facecolor=c_meta_bg, zorder=1)
    ax.add_patch(rect_gov)
    
    ax.text(0.5, 0.90, "Outer Loop: Governance (AVoI)", ha='center', va='center', 
            fontsize=14, weight='bold', color=c_meta_text, zorder=2)
    ax.text(0.5, 0.83, "Objective: Maximize Human Flourishing Index (HFI)", ha='center', va='center', 
            fontsize=12, color=c_meta_text, zorder=2)
    ax.text(0.5, 0.76, r"Meta-Update: $\phi \leftarrow \phi + \eta \nabla_\phi J(\phi)$", ha='center', va='center', 
            fontsize=12, color='black', zorder=2)
    
    # Veil of Ignorance Badge
    bbox_props = dict(boxstyle="round,pad=0.5", fc="white", ec="#BDBDBD", alpha=0.9)
    ax.text(0.85, 0.90, "Veil of Ignorance:\n" + r"Sample Roles $r \sim \mathcal{R}$", ha='center', va='center', 
            fontsize=10, bbox=bbox_props, style='italic', zorder=3)

    # 2. Economy Zone (Bottom)
    # y=0.03 to 0.56 (height 0.53) - Created gap between 0.56 and 0.64
    rect_econ = patches.FancyBboxPatch((0.05, 0.03), 0.9, 0.53, boxstyle="round,pad=0.03,rounding_size=0.05", 
                                       linewidth=2.5, edgecolor=c_econ_stroke, facecolor=c_econ_bg, zorder=1)
    ax.add_patch(rect_econ)
    
    # MOVED DOWN: Title is now lower to avoid arrow text
    ax.text(0.5, 0.49, "Inner Loop: The Silicon Commune (MARL Economy)", ha='center', va='center', 
            fontsize=14, weight='bold', color=c_econ_text, zorder=2)

    # --- NODES ---

    # Agents
    rect_agents = patches.FancyBboxPatch((0.15, 0.12), 0.28, 0.25, boxstyle="round,pad=0.02,rounding_size=0.02", 
                                         linewidth=2, edgecolor=c_agent_stroke, facecolor=c_agent_bg, zorder=3)
    ax.add_patch(rect_agents)
    
    ax.text(0.29, 0.32, "Agents (Owners & Citizens)", ha='center', va='center', fontsize=11, weight='bold', zorder=4)
    ax.text(0.29, 0.25, r"Policy $\pi_{\theta}(a|s)$", ha='center', va='center', fontsize=10, zorder=4)
    ax.text(0.29, 0.19, r"Update $\theta$ (PPO)", ha='center', va='center', fontsize=10, style='italic', color='#5D4037', zorder=4)

    # Production
    rect_prod = patches.FancyBboxPatch((0.57, 0.12), 0.28, 0.25, boxstyle="round,pad=0.02,rounding_size=0.02", 
                                       linewidth=2, edgecolor=c_prod_stroke, facecolor=c_prod_bg, zorder=3)
    ax.add_patch(rect_prod)
    
    ax.text(0.71, 0.32, "Production & Distribution", ha='center', va='center', fontsize=11, weight='bold', zorder=4)
    ax.text(0.71, 0.25, r"$Y_t = A \cdot \Phi(I, C, E)$", ha='center', va='center', fontsize=10, zorder=4)
    ax.text(0.71, 0.19, "Compute Revenues & Taxes\nCalc Capabilities (HFI)", ha='center', va='center', fontsize=9, zorder=4)

    # --- EDGES / ARROWS ---
    
    style_arrow = dict(arrowstyle="->", lw=2, color='#37474F')
    style_arrow_dashed = dict(arrowstyle="->", lw=2, color='#37474F', ls='--')

    # Mechanism (Down)
    # Adjusted y-coordinates to route cleanly through the gap
    ax.annotate("", xy=(0.29, 0.37), xytext=(0.29, 0.64), arrowprops=dict(arrowstyle="simple", facecolor='black'), zorder=2)
    # Placed in the gap (y=0.60)
    ax.text(0.31, 0.60, r"Mechanism $\phi$" + "\n(Tax rates, Divs)", ha='left', va='center', fontsize=10, weight='bold', zorder=4, backgroundcolor='white')

    # Meta-Return (Up)
    ax.annotate("", xy=(0.71, 0.64), xytext=(0.71, 0.37), arrowprops=dict(arrowstyle="simple", facecolor='black'), zorder=2)
    # Placed in the gap (y=0.60)
    ax.text(0.69, 0.60, "Meta-Return J\n(Cumulative HFI)", ha='right', va='center', fontsize=10, weight='bold', zorder=4, backgroundcolor='white')

    # Inner Loop A: Agents -> Production (Actions)
    ax.annotate("", xy=(0.57, 0.25), xytext=(0.43, 0.25), arrowprops=style_arrow, zorder=3)
    ax.text(0.50, 0.27, "Actions $a_t$", ha='center', va='bottom', fontsize=9, zorder=4)
    
    # Inner Loop B: Production -> Agents (States/Rewards)
    ax.annotate("", xy=(0.43, 0.19), xytext=(0.57, 0.19), arrowprops=style_arrow_dashed, zorder=3)
    ax.text(0.50, 0.17, "State $s_{t+1}$, Reward $r_t$", ha='center', va='top', fontsize=9, zorder=4)

    plt.tight_layout()
    plt.savefig('fig_csc_arch.pdf', format='pdf', bbox_inches='tight', dpi=300)
    print("Optimization complete: fig_csc_arch.pdf generated.")

if __name__ == "__main__":
    create_architecture_diagram()
