"""
Shared test configuration and fixtures for Solana trading bot tests
"""
import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from solana_bot.config import BotConfig


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config_file(tmp_path):
    """Create a temporary test configuration file."""
    config_data = {
        "rpc_endpoint": "https://api.devnet.solana.com",
        "websocket_endpoint": "wss://api.devnet.solana.com",
        "wallet_private_key": "test_private_key_placeholder",
        "bot_settings": {
            "take_profit": 30.0,
            "stop_loss": 15.0,
            "max_trades_per_hour": 5,
            "min_volume_24h": 5000.0,
            "max_hold_time_hours": 4.0,
            "cooldown_after_sell": 60,
            "enable_trailing_stop": True,
            "trailing_stop_percentage": 10.0
        },
        "token_filters": {
            "max_supply": 1000000000,
            "min_holders": 100,
            "max_top_holder_percent": 20.0,
            "contract_verified": True,
            "renounced_ownership": True
        }
    }

    config_file = tmp_path / "test_bot_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    return config_file


@pytest.fixture
def bot_config(test_config_file):
    """Create a BotConfig instance with test configuration."""
    config = BotConfig()
    config.load_from_file(str(test_config_file))
    return config


@pytest.fixture
def mock_solana_client():
    """Create a mock Solana AsyncClient for testing."""
    mock_client = AsyncMock()
    mock_client.get_account_info.return_value = Mock()
    mock_client.get_account_info.return_value.value = Mock()
    mock_client.get_account_info.return_value.value.data = b"mock_data"
    return mock_client


@pytest.fixture
def mock_wallet():
    """Create a mock wallet for testing."""
    mock_wallet = Mock()
    mock_wallet.public_key = "11111111111111111111111111111112"
    mock_wallet.sign_transaction = Mock(return_value=Mock())
    return mock_wallet


@pytest.fixture
def mock_price_tracker():
    """Create a mock PriceTracker for testing."""
    mock_tracker = Mock()
    mock_tracker.register_callback = Mock()
    mock_tracker.unregister_callback = Mock()
    mock_tracker.get_price = AsyncMock(return_value=1.0)
    return mock_tracker


@pytest.fixture
def mock_raydium_swap():
    """Create a mock RaydiumSwap for testing."""
    mock_swap = Mock()
    mock_swap.get_pool_info = AsyncMock(return_value={
        'pool_address': '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',
        'token_address': 'So11111111111111111111111111111111111111112',
        'liquidity': 10000.0
    })
    return mock_swap


@pytest.fixture
def mock_transaction_builder():
    """Create a mock TransactionBuilder for testing."""
    mock_builder = Mock()
    mock_builder.build_buy_transaction = AsyncMock(return_value=Mock())
    mock_builder.build_sell_transaction = AsyncMock(return_value=Mock())
    return mock_builder


@pytest.fixture
def sample_token_data():
    """Sample token data for testing."""
    return {
        'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
        'symbol': 'USDC',
        'name': 'USD Coin',
        'decimals': 6,
        'supply': 1000000000,
        'holder_count': 150,
        'top_holder_percent': 15.0,
        'is_verified': True,
        'ownership_renounced': True,
        'volume_24h': 10000.0
    }


@pytest.fixture
def risky_token_data():
    """Sample risky token data for testing filters."""
    return {
        'address': 'RiskyToken11111111111111111111111111111111',
        'symbol': 'RISK',
        'name': 'Risky Token',
        'decimals': 9,
        'supply': 2000000000,  # > 1B
        'holder_count': 50,     # < 100
        'top_holder_percent': 35.0,  # > 20%
        'is_verified': False,
        'ownership_renounced': False,
        'volume_24h': 1000.0   # < 5000
    }


@pytest.fixture
def mock_pool_transaction():
    """Mock Raydium pool creation transaction data."""
    return {
        'pool_address': '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',
        'token_mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        'base_mint': 'So11111111111111111111111111111111111111112',
        'quote_mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
        'initial_liquidity': 10000.0,
        'timestamp': 1640995200,
        'creator': 'CreatorAddress111111111111111111111111111111'
    }
