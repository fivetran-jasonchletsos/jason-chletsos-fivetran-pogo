"""
Debug script for local testing of the Pokémon Fivetran connector
Uses the Fivetran Connector SDK's built-in debugging tools
"""

import json
from connector import connector

if __name__ == "__main__":
    # Load configuration
    with open('configuration.json', 'r') as f:
        configuration = json.load(f)
    
    print("=" * 80)
    print("POKEMON FIVETRAN CONNECTOR - DEBUG MODE")
    print("=" * 80)
    print("\nConfiguration:")
    print(json.dumps(configuration, indent=2))
    print("\n" + "=" * 80)
    print("Starting connector debug session...")
    print("=" * 80 + "\n")
    
    # Run the connector in debug mode
    # This will simulate a Fivetran sync and output results to console
    connector.debug(configuration=configuration)
