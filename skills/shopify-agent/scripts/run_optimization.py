#!/usr/bin/env python3
"""Run a single optimization cycle for the Shopify agent."""
import os
import sys

# Add the agents directory to the path
agents_dir = os.path.join(os.path.dirname(__file__), "../../../agents")
sys.path.insert(0, os.path.abspath(agents_dir))

# Import the Shopify agent module
try:
    from Shopify_agent import continuous_optimization
    
    def main() -> int:
        print("Starting Shopify store optimization...")
        try:
            continuous_optimization()
            print("Optimization completed successfully!")
            return 0
        except Exception as e:
            print(f"Error during optimization: {e}", file=sys.stderr)
            return 1
    
    if __name__ == "__main__":
        raise SystemExit(main())
        
except ImportError as e:
    print(f"Error importing Shopify agent: {e}", file=sys.stderr)
    print("Make sure Shopify agent dependencies are installed:", file=sys.stderr)
    print(f"  cd {agents_dir}", file=sys.stderr)
    print("  pip3 install -r requirements.txt", file=sys.stderr)
    sys.exit(1)
