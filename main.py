#!/usr/bin/env python3
"""
Simple entry point for the Solana Trading Bot
Redirects to the full CLI interface
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point - redirects to CLI"""
    cli_path = Path(__file__).parent / "solana_bot_cli.py"
    if cli_path.exists():
        # Run the CLI version
        result = subprocess.run([sys.executable, str(cli_path)] + sys.argv[1:])
        sys.exit(result.returncode)
    else:
        print("Error: solana_bot_cli.py not found")
        sys.exit(1)

if __name__ == "__main__":
    main()
