
import numpy as np
import pyspiel

class ScriptBot:
    """
    Parametrized Script Bot for Poker-AD.
    Parameters:
    - alpha (float): Aggression Factor [0, 1]. Prob of Bet/Raise.
    - beta (float): Loose/Tight Factor [0, 1]. Range of hands played.
    - gamma (float): Bluff Frequency [0, 1]. Prob of betting weak hands.
    - delta (float): Call Station Tendency [0, 1]. Prob of calling vs folding.
    """
    def __init__(self, alpha=0.5, beta=0.5, gamma=0.1, delta=0.5, rng=None):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.rng = rng or np.random.RandomState()

    def step(self, state):
        """
        Returns an action index based on the state and bot parameters.
        This is a simplified logic for Leduc/FHP.
        """
        legal_actions = state.legal_actions()
        if not legal_actions:
            return None
        
        # Parse State (Simplified for Leduc)
        # In Leduc: 3 cards (J, Q, K). 2 rounds.
        # We need to know our card.
        # OpenSpiel state string or information state tensor needed.
        # For this script, we assume access to 'state' object methods.
        
        # Simple Logic:
        # 1. Evaluate Hand Strength
        #    (In Leduc, pair > high card)
        # 2. Decide Action based on Strength vs Params
        
        # Placeholder random action for now until OpenSpiel logic is fully mapped
        # In real implementation:
        # rank = get_hand_rank(state)
        # if rank > threshold(beta): play_aggressive(alpha)
        # else: bluff(gamma) or fold/call(delta)
        
        # Logic:
        # If 'Bet'/ 'Raise' in legal:
        #   Prob(Bet) = alpha * Strength + gamma * (1-Strength)
        # If 'Call' in legal:
        #   Prob(Call) = delta * Strength + (1-beta) * (1-Strength)
        
        # Determining action usually requires probability distribution
        return self.rng.choice(legal_actions)

def make_bot_zoo(n=100):
    """Generates N diverse bots."""
    bots = []
    rng = np.random.RandomState(42)
    for _ in range(n):
        params = rng.rand(4) # alpha, beta, gamma, delta
        bots.append(ScriptBot(*params, rng=rng))
    return bots
