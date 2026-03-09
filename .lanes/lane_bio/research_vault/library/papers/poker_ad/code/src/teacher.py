
import pyspiel
from open_spiel.python.algorithms import best_response
from open_spiel.python.policy import Policy

class OracleTeacher:
    """
    White-box Oracle Teacher.
    Calculates the Best Response (BR) to a given opponent policy.
    """
    def __init__(self, game, opponent_policy):
        self.game = game
        self.opponent_policy = opponent_policy
        # We need a BR policy for EACH player position the teacher might perform.
        # If the Teacher acts as Player 'i', it needs a BR against the Opponent playing as '1-i'.
        # However, the Opponent Policy usually handles the Logic for whatever player it is assigned to.
        # So we just ask "What is the BR for Player i against this Opponent Policy?"
        self.br_policies = []
        for pid in range(game.num_players()):
            # BestResponsePolicy(game, player_id, policy)
            self.br_policies.append(best_response.BestResponsePolicy(game, pid, opponent_policy))

    def action_probabilities(self, state, player_id=None):
        if player_id is None:
            player_id = state.current_player()
        return self.br_policies[player_id].action_probabilities(state, player_id)

    def get_action(self, state):
        """
        Returns the optimal action for the current state against the pinned opponent.
        """
        pid = state.current_player()
        # BestResponsePolicy returns a policy, so use action_probabilities and pick the best one.
        probs = self.br_policies[pid].action_probabilities(state)
        # It's a best response, so it should be deterministic (mostly).
        return max(probs, key=probs.get)

    def get_policy(self):
        """Returns the full BR policy object for the current player perspective?"""
        # This is ambiguous if we hold multiple. Returning list or ignoring.
        return self.br_policies

def create_teacher(game_name, opponent_bot):
    """
    Wraps a ScriptBot into a Policy and computes BR.
    """
    game = pyspiel.load_game(game_name)
    
    # Wrap ScriptBot as OpenSpiel Policy
    class BotPolicy(Policy):
        def __init__(self, game, bot):
            # Pass all player_ids. OpenSpiel usually expects a list.
            # Assuming 2-player game (Leduc/FHP).
            super().__init__(game, list(range(game.num_players())))
            self.bot = bot
        
        def action_probabilities(self, state, player_id=None):
            # ScriptBots usually are deterministic or sample internal RNG.
            # Convert single action to one-hot prob vs support full support?
            # For BR calculation, we need a fixed policy.
            # If Bot is stochastic, we need its distribution.
            legal = state.legal_actions()
            # Placeholder: Uniform random for now until Bot logic is rigid
            return {a: 1.0/len(legal) for a in legal}

    opp_policy = BotPolicy(game, opponent_bot)
    teacher = OracleTeacher(game, opp_policy)
    return teacher
