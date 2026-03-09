import torch
import torch.nn as nn
import torch.optim as optim
import argparse
import random

# Mock "Agent" for Evolution
class Agent(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(10, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, x):
        return self.net(x)

def evaluate(agent, env_data):
    # Mock evaluation: simple regression task
    with torch.no_grad():
        pred = agent(env_data)
        target = env_data.sum(dim=1, keepdim=True)
        loss = nn.MSELoss()(pred, target)
        return -loss.item() # Fitness = negative loss

def mutate(agent, mutation_rate=0.1):
    for param in agent.parameters():
        if random.random() < mutation_rate:
            noise = torch.randn_like(param) * 0.1
            param.data += noise

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🧬 Evo-Distill Baseline | Device: {device} | Generations: {args.generations}")

    population_size = 10
    population = [Agent().to(device) for _ in range(population_size)]
    
    # Mock Environment Data
    env_data = torch.randn(100, 10).to(device)

    for gen in range(args.generations):
        # 1. Evaluate
        fitness_scores = [(agent, evaluate(agent, env_data)) for agent in population]
        fitness_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_agent, best_score = fitness_scores[0]
        
        print(f"Gen {gen+1}: Best Fitness = {best_score:.4f}")

        # 2. Select & Reproduce (Elitism)
        survivors = fitness_scores[:population_size//2]
        new_population = [agent for agent, _ in survivors]
        
        # Fill rest with mutated clones
        while len(new_population) < population_size:
            parent, _ = random.choice(survivors)
            child = Agent().to(device)
            child.load_state_dict(parent.state_dict())
            mutate(child)
            new_population.append(child)
        
        population = new_population

    print("✅ Evo-Distill Evolution Complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", type=int, default=5)
    args = parser.parse_args()
    train(args)
