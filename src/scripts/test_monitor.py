#!/usr/bin/env python3
"""
Simple test script to check CPMM pool detection
"""
import asyncio
import logging
from solana_bot.monitor import PoolMonitor
from solana_bot.config import BotConfig

async def test_monitoring():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create config with CPMM program
    config = BotConfig()
    from solders.pubkey import Pubkey
    config.config['raydium_program_id'] = 'CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C'
    
    # Create a dummy wallet manager
    class DummyWallet:
        pass
    
    wallet = DummyWallet()
    
    # Create monitor
    monitor = PoolMonitor(
        rpc_endpoint=config.rpc_endpoint,
        ws_endpoint=config.websocket_endpoint,
        raydium_program_id=config.raydium_program_id,
        config=config,
        wallet_manager=wallet,
        callback=lambda x: print(f"Pool detected: {x}")
    )
    
    print("Starting CPMM monitoring test...")
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(test_monitoring())
