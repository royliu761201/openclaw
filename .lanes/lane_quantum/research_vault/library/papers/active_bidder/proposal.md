# Temporal Active Bidder: Calibration via World Models (v2)
**(Project: Active-Bidder-Dreamer)**

## 1. The Paradigm Shift (v2)
Static Active Inference (v1) assumes user preferences are constant. Real users are **Dynamic Systems** with evolving states (fatigue, interest drift).
We propose **Temporal Active Inference**: Treating the user trajectory as a POMDP (Partially Observable Markov Decision Process).
The Ad System builds a **World Model** (RSSM) of the user's internal state evolution and bids to minimize *future* surprisal.

## 2. Mathematical Formulation (Temporal VFE)
We minimize the **Expected Free Energy (G)** over a future horizon $H$:

$$ G(\pi) = \sum_{\tau=t}^{t+H} \underbrace{D_{KL}(Q(s_\tau|\pi) || P(s_\tau))}_{\text{Risk (State Divergence)}} - \underbrace{\mathbb{E}_{Q}[\ln P(o_\tau|s_\tau)]}_{\text{Ambiguity (Epistemic Value)}} $$

-   **Risk**: Don't drive the user into unknown/negative states (Churn).
-   **Ambiguity**: Explore ads that resolve uncertainty about user interests.

## 3. Cognitive Architecture (RSSM)
We replace the Dual-Tower with a **Recurrent State Space Model**:
1.  **Encoder**: $o_t \to e_t$ (Embed Ad/Click)
2.  **Recurrent Model (Deterministic)**: $h_t = f(h_{t-1}, s_{t-1}, a_{t-1})$
3.  **Transition Model (Stochastic)**: $\hat{s}_t \sim P(s_t | h_t)$ (Prior) vs $Q(s_t | h_t, e_t)$ (Posterior)
4.  **Action Head**: Predicts Bid $b_t$.

## 4. Hardware Implementation
-   **BPTT**: Backpropagation Through Time requires sequence batching (User Session Replay).
-   **FlashAttention**: Used for long-context user history.

## 5. Proposed Experiments
1.  **Sequential Dataset**: Alibaba Display Ad Dataset (User Behavior Sequences).
2.  **Baselines**: `GRU4Rec` (RNN), `DreamerV3` (RL), `Active-Bidder-v1`.
3.  **Metric**: Long-term Retention & Conversion (Trajectory optimization).
