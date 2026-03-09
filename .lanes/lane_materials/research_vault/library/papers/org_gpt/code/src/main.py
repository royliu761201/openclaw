
import argparse
from .environment import Organization
from .agent import OrganizationConfig

def main():
    parser = argparse.ArgumentParser(description="Org-GPT Simulation")
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--width", type=int, default=2)
    parser.add_argument("--policy", type=str, default="Reduce admin burden by 30%")
    args = parser.parse_args()
    
    print("🏗️ Initializing Organization...")
    config = OrganizationConfig(depth=args.depth, width_per_node=args.width)
    org = Organization(config)
    print(f"✅ Created Org with {len(org.agents)} agents.")
    
    print("\n🚀 Starting Policy Propagation...")
    org.propagate_policy(args.policy)
    
    print("\n✅ Simulation Complete.")

if __name__ == "__main__":
    main()
