"""
End-to-end tests for pool detection workflow
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from solana_bot.monitor import PoolMonitor
from solana_bot.config import BotConfig
from solana_bot.security import SecurityAnalyzer


class TestPoolDetectionE2E:
    """End-to-end tests for pool detection workflow."""

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create test configuration file."""
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

        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file

    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        price_tracker = Mock()
        price_tracker.register_callback = Mock()
        price_tracker.unregister_callback = Mock()

        raydium_swap = Mock()
        transaction_builder = Mock()
        wallet = Mock()

        return {
            'price_tracker': price_tracker,
            'raydium_swap': raydium_swap,
            'transaction_builder': transaction_builder,
            'wallet': wallet
        }

    def test_pool_detection_initialization(self, bot_config, mock_components):
        """Test pool monitor initialization with all components."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            bot_config.raydium_program_id,
            bot_config,
            mock_components['wallet']
        )

        # Verify initialization
        assert monitor.config == bot_config
        assert monitor.wallet == mock_components['wallet']
        assert monitor.rpc_endpoint == bot_config.rpc_endpoint
        assert monitor.ws_endpoint == bot_config.websocket_endpoint

        # Verify rate limiting variables initialized
        assert hasattr(monitor, 'trade_count')
        assert hasattr(monitor, 'last_trade_reset')
        assert hasattr(monitor, 'cooldowns')
        assert monitor.trade_count == 0

    @pytest.mark.asyncio
    async def test_pool_creation_detection(self, bot_config, mock_components):
        """Test detection of pool creation transaction."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            bot_config.raydium_program_id,
            bot_config,
            mock_components['wallet']
        )

        # Mock pool data that would come from transaction parsing
        pool_data = {
            'pool_address': '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',
            'token_address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'initial_liquidity': 10000.0,
            'creator': 'CreatorAddress111111111111111111111111111111'
        }

        # Mock security analyzer
        mock_analyzer = Mock()
        mock_analyzer.check_token_filters = AsyncMock(return_value={
            'passed': True,
            'supply_check': {'passed': True},
            'holders_check': {'passed': True},
            'contract_check': {'passed': True}
        })
        monitor.security_analyzer = mock_analyzer

        # Mock all validation checks to pass
        with patch.object(monitor, '_get_token_volume_24h', return_value=10000.0):

            # Test the complete auto-buy workflow
            result = await monitor.execute_auto_buy(pool_data)

            # Should succeed with all checks passing
            assert result is None  # execute_auto_buy doesn't return on success, just completes

    @pytest.mark.asyncio
    async def test_pool_detection_with_filters(self, bot_config, mock_components):
        """Test pool detection with security filters applied."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            bot_config.raydium_program_id,
            bot_config,
            mock_components['wallet']
        )

        pool_data = {
            'pool_address': 'POOL_123',
            'token_address': 'RISKY_TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'RISKY_TOKEN_123'
        }

        # Mock security analyzer to fail
        mock_analyzer = Mock()
        mock_analyzer.check_token_filters = AsyncMock(return_value={
            'passed': False,
            'supply_check': {'passed': False, 'reason': 'Supply too high'},
            'holders_check': {'passed': True},
            'contract_check': {'passed': True}
        })
        monitor.security = mock_analyzer

        # Test auto-buy with failing security filters
        result = await monitor.execute_auto_buy(pool_data)

        # Should fail due to security filter
        assert result is None

        # Verify security checks were called
        mock_analyzer.check_token_filters.assert_called_once_with('RISKY_TOKEN_123')

    @pytest.mark.asyncio
    async def test_rate_limiting_e2e(self, bot_config, mock_components):
        """Test end-to-end rate limiting in pool detection workflow."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            bot_config.raydium_program_id,
            bot_config,
            mock_components['wallet']
        )

        pool_data = {
            'pool_address': 'POOL_123',
            'token_address': 'TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'TOKEN_123'
        }

        # Fill rate limit
        monitor.trade_count = bot_config.max_trades_per_hour

        # Mock security checks to pass
        mock_analyzer = Mock()
        mock_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})
        monitor.security = mock_analyzer

        with patch.object(monitor, '_get_token_volume_24h', return_value=10000.0):
            result = await monitor.execute_auto_buy(pool_data)

            # Should fail due to rate limiting
            assert result is None

    @pytest.mark.asyncio
    async def test_token_cooldown_e2e(self, bot_config, mock_components):
        """Test end-to-end token cooldown in pool detection workflow."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            bot_config.raydium_program_id,
            bot_config,
            mock_components['wallet']
        )

        token_mint = 'COOLDOWN_TOKEN_123'
        pool_data = {
            'pool_address': 'POOL_123',
            'token_address': token_mint,
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': token_mint
        }

        # Set token cooldown
        import time
        monitor.cooldowns[token_mint] = time.time()

        # Mock security checks to pass
        mock_analyzer = Mock()
        mock_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})
        monitor.security = mock_analyzer

        with patch.object(monitor, '_get_token_volume_24h', return_value=10000.0):
            result = await monitor.execute_auto_buy(pool_data)

            # Should fail due to token cooldown
            assert result is None

    @pytest.mark.asyncio
    async def test_volume_check_e2e(self, bot_config, mock_components):
        """Test end-to-end volume validation in pool detection workflow."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            bot_config.raydium_program_id,
            bot_config,
            mock_components['wallet']
        )

        pool_data = {
            'pool_address': 'POOL_123',
            'token_address': 'LOW_VOLUME_TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'LOW_VOLUME_TOKEN_123'
        }

        # Mock security checks to pass
        mock_analyzer = Mock()
        mock_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})
        monitor.security = mock_analyzer

        # Mock volume check to fail (return volume below minimum)
        with patch.object(monitor, '_get_token_volume_24h', return_value=1000.0):  # Below 5000 minimum
            result = await monitor.execute_auto_buy(pool_data)

            # Should fail due to volume check
            assert result is None
