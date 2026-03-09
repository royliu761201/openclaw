import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_rounded_box(ax, xy, width, height, color, label=None, fontsize=9, textcolor="black", alpha=1.0, edgecolor=None):
    box = patches.FancyBboxPatch(
        xy, width, height,
        boxstyle="round,pad=0.1,rounding_size=0.1",
        ec=edgecolor if edgecolor else color,
        fc=color,
        alpha=alpha,
        zorder=10
    )
    ax.add_patch(box)
    if label:
        ax.text(xy[0] + width/2, xy[1] + height/2, label, 
                ha='center', va='center', fontsize=fontsize, color=textcolor, weight='bold', zorder=11)

def draw_architecture():
    # Setup
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Colors (NeurIPS/Scientific Theme)
    c_token_bg = "#E3F2FD" # Light Blue
    c_token_border = "#1E88E5" # Dark Blue
    c_transformer = "#F3E5F5" # Light Purple
    c_transformer_border = "#8E24AA" # Dark Purple
    c_action = "#E8F5E9" # Light Green
    c_action_border = "#43A047" # Dark Green
    c_arrow = "#424242"
    
    # --- Context Window (Left) ---
    # Draw 5 timesteps (t-4 to t)
    token_w = 1.2
    token_h = 3.5
    start_x = 0.5
    gap = 0.2
    
    labels = ["LOB\nFeatures", "Position", "Action", "PnL\nStats"]
    
    # Context Bracket
    ax.annotate("Context Window", xy=(4.0, 6.8), xytext=(4.0, 7.2), ha='center', fontsize=12, weight='bold')
    ax.plot([0.5, 0.5, 7.5, 7.5], [6.5, 6.7, 6.7, 6.5], color='black', lw=1.5)
    
    for i in range(5):
        x = start_x + i * (token_w + gap)
        # Main Token Container
        draw_rounded_box(ax, (x, 2.0), token_w, 4.0, c_token_bg, edgecolor=c_token_border)
        
        # Inner blocks
        sub_h = 0.8
        sub_gap = 0.1
        current_y = 5.0
        
        # Time Label
        t_label = f"Token t-{4-i}" if i < 4 else "Token t"
        ax.text(x + token_w/2, 6.2, t_label, ha='center', fontsize=10)
        
        for lbl in labels:
            draw_rounded_box(ax, (x + 0.1, current_y), token_w - 0.2, sub_h, "white", 
                             label=lbl, fontsize=7, edgecolor=c_token_border)
            current_y -= (sub_h + sub_gap)
            
        # Arrows connecting tokens
        if i < 4:
            ax.arrow(x + token_w, 4.0, gap * 0.8, 0, head_width=0.15, head_length=0.1, fc=c_arrow, ec=c_arrow)

    # --- Causal Transformer (Middle) ---
    trans_x = 9.0
    trans_w = 3.0
    trans_h = 4.0
    
    # Stack effect
    for offset in [0.2, 0.1, 0.0]:
        draw_rounded_box(ax, (trans_x + offset, 2.0 + offset), trans_w, trans_h, c_transformer, edgecolor=c_transformer_border)
    
    ax.text(trans_x + trans_w/2, 5.5, "Causal Transformer\n(Stacked Layers)", ha='center', weight='bold', color=c_transformer_border, zorder=12)
    
    # Internal "Attention" graphic (schematic)
    embed_rect_x = trans_x + 0.5
    embed_rect_y = 3.0
    draw_rounded_box(ax, (embed_rect_x, embed_rect_y), 2.0, 1.5, "white", edgecolor=c_transformer_border)
    ax.arrow(embed_rect_x + 0.2, embed_rect_y + 0.75, 1.4, 0, head_width=0.2, fc=c_transformer_border, ec=c_transformer_border, width=0.05, zorder=11)
    
    # Arrow to Transformer
    ax.arrow(7.8, 4.0, 0.8, 0, head_width=0.3, width=0.08, fc=c_arrow, ec=c_arrow, zorder=11)
    
    # --- Action Distribution (Right) ---
    dist_x = 13.5
    dist_w = 2.0
    dist_h = 3.0
    dist_y = 2.5
    
    # Arrow to Distribution
    ax.arrow(12.3, 4.0, 0.8, 0, head_width=0.3, width=0.08, fc=c_arrow, ec=c_arrow, zorder=11)
    
    draw_rounded_box(ax, (dist_x, dist_y), dist_w, dist_h, c_action, edgecolor=c_action_border)
    ax.text(dist_x + dist_w/2, 4.0, "Action\nDistribution\n(Next Step)", ha='center', weight='bold', color=c_action_border, zorder=12)
    
    # Curve
    x_curve = np.linspace(dist_x + 0.2, dist_x + dist_w - 0.2, 50)
    # Gaussian-ish
    y_curve = 3.0 + 1.5 * np.exp(-0.5 * ((x_curve - (dist_x + 1.0)) / 0.4)**2)
    ax.plot(x_curve, y_curve, color=c_action_border, lw=2, zorder=11)
    ax.fill_between(x_curve, 3.0, y_curve, color=c_action_border, alpha=0.2, zorder=11)
    
    # --- Feedback Loop ---
    # Line from bottom of Dist to bottom of tokens
    ax.plot([dist_x + 1.0, dist_x + 1.0], [2.5, 1.0], color=c_arrow, lw=2) # Down
    ax.plot([dist_x + 1.0, 1.1], [1.0, 1.0], color=c_arrow, lw=2) # Left
    ax.plot([1.1, 1.1], [1.0, 1.9], color=c_arrow, lw=2) # Up
    ax.arrow(1.1, 1.9, 0, 0.1, head_width=0.2, fc=c_arrow, ec=c_arrow) # Arrowhead
    
    draw_rounded_box(ax, (6.0, 0.8), 4.0, 0.4, "white", label="PnL Feedback Loop / Zero-Shot Adaptation", fontsize=10, edgecolor="none")
    
    
    plt.tight_layout()
    plt.savefig("figs/architecture.pdf", bbox_inches='tight', dpi=300)
    plt.savefig("figs/architecture.png", bbox_inches='tight', dpi=300) # Save png too just in case
    plt.close()

if __name__ == "__main__":
    draw_architecture()
