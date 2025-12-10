"""
Unit tests for PoolMonitor class enhancements
"""
import pytest
import time
from unittest.mock import Mock, AsyncMock, patch
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig
from src.solana_bot.security import SecurityAnalyzer


class TestPoolMonitorEnhancements:
    """Test enhanced PoolMonitor class with rate limiting and volume checks."""

    def test_pool_monitor_initialization(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test PoolMonitor initialization with enhanced features."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",  # Raydium program ID
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        assert monitor.config == bot_config
        assert monitor.price_tracker == mock_price_tracker
        assert monitor.raydium == mock_raydium_swap
        assert monitor.tx_builder == mock_transaction_builder
        assert monitor.wallet == mock_wallet

        # Check rate limiting variables
        assert hasattr(monitor, 'trade_count')
        assert hasattr(monitor, 'last_trade_times')
        assert hasattr(monitor, 'token_cooldowns')

    def test_rate_limiting_logic(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test rate limiting functionality."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        # Test initial state
        assert monitor.trade_count == 0
        assert len(monitor.last_trade_times) == 0

        # Simulate trades within limit
        current_time = time.time()
        for i in range(bot_config.max_trades_per_hour):
            monitor.last_trade_times.append(current_time - (i * 60))  # Space them out
            monitor.trade_count += 1

        # Should allow trade (at limit)
        assert monitor._check_rate_limit() == True

        # Add one more trade (exceed limit)
        monitor.last_trade_times.append(current_time)
        monitor.trade_count += 1

        # Should deny trade
        assert monitor._check_rate_limit() == False

    def test_token_cooldown_logic(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test token cooldown functionality."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        token_mint = "TEST_TOKEN_123"
        cooldown_seconds = bot_config.cooldown_after_sell

        # Test token not in cooldown
        assert monitor._check_token_cooldown(token_mint) == True

        # Add token to cooldown
        monitor.token_cooldowns[token_mint] = time.time()

        # Should be in cooldown
        assert monitor._check_token_cooldown(token_mint) == False

        # Simulate cooldown expiry
        monitor.token_cooldowns[token_mint] = time.time() - (cooldown_seconds + 1)

        # Should allow trading again
        assert monitor._check_token_cooldown(token_mint) == True

    def test_volume_validation_logic(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test 24h volume validation."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        # Mock volume check method
        with patch.object(monitor, '_get_token_volume_24h') as mock_volume:
            # Test sufficient volume
            mock_volume.return_value = 10000.0  # Above 5000 minimum
            import asyncio
            result = asyncio.run(monitor._check_token_volume("TEST_TOKEN"))
            assert result == True

            # Test insufficient volume
            mock_volume.return_value = 1000.0  # Below 5000 minimum
            import asyncio
            result = asyncio.run(monitor._check_token_volume("TEST_TOKEN"))
            assert result == False

    def test_token_filter_integration(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test token filter integration in auto-buy logic."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        # Mock security analyzer
        mock_analyzer = Mock()
        monitor.security_analyzer = mock_analyzer

        # Test passing filters
        mock_analyzer.check_token_filters = AsyncMock(return_value={
            'passed': True,
            'supply_check': {'passed': True},
            'holders_check': {'passed': True},
            'contract_check': {'passed': True}
        })

        token_mint = "SAFE_TOKEN_123"
        import asyncio
        result = asyncio.run(monitor._check_token_filters(token_mint))
        assert result == True

        # Test failing filters
        mock_analyzer.check_token_filters = AsyncMock(return_value={
            'passed': False,
            'supply_check': {'passed': False},
            'holders_check': {'passed': True},
            'contract_check': {'passed': True}
        })

        import asyncio
        result = asyncio.run(monitor._check_token_filters(token_mint))
        assert result == False

    def test_execute_auto_buy_with_enhancements(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test enhanced execute_auto_buy method with all new checks."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        # Mock security analyzer
        mock_analyzer = Mock()
        monitor.security_analyzer = mock_analyzer

        # Mock all checks to pass
        mock_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})

        with patch.object(monitor, '_check_rate_limit', return_value=True), \
             patch.object(monitor, '_check_token_cooldown', return_value=True), \
             patch.object(monitor, '_check_token_volume', return_value=True), \
             patch.object(monitor, '_execute_buy_transaction') as mock_buy:

            mock_buy.return_value = True

            pool_data = {
                'pool_address': 'POOL_123',
                'token_mint': 'TOKEN_123',
                'base_mint': 'SOL_MINT',
                'quote_mint': 'TOKEN_123'
            }

            import asyncio
            result = asyncio.run(monitor.execute_auto_buy(pool_data))

            # Should succeed with all checks passing
            assert result == True
            mock_buy.assert_called_once()

    def test_execute_auto_buy_rate_limited(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test execute_auto_buy with rate limiting."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        # Exceed rate limit
        monitor.trade_count = bot_config.max_trades_per_hour + 1

        pool_data = {
            'pool_address': 'POOL_123',
            'token_mint': 'TOKEN_123',
            'base_mint': 'SOL_MINT',
            'quote_mint': 'TOKEN_123'
        }

        import asyncio
        result = asyncio.run(monitor.execute_auto_buy(pool_data))

        # Should fail due to rate limiting
        assert result == False

    def test_execute_auto_buy_token_cooldown(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test execute_auto_buy with token cooldown."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        # Put token in cooldown
        token_mint = 'TOKEN_123'
        monitor.token_cooldowns[token_mint] = time.time()

        pool_data = {
            'pool_address': 'POOL_123',
            'token_mint': token_mint,
            'base_mint': 'SOL_MINT',
            'quote_mint': token_mint
        }

        import asyncio
        result = asyncio.run(monitor.execute_auto_buy(pool_data))

        # Should fail due to token cooldown
        assert result == False

    def test_execute_auto_buy_volume_check_fail(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test execute_auto_buy with volume check failure."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjSzt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        with patch.object(monitor, '_check_token_volume', return_value=False):
            pool_data = {
                'pool_address': 'POOL_123',
                'token_mint': 'TOKEN_123',
                'base_mint': 'SOL_MINT',
                'quote_mint': 'TOKEN_123'
            }

            import asyncio
            result = asyncio.run(monitor.execute_auto_buy(pool_data))

            # Should fail due to volume check
            assert result == False

    def test_cooldown_after_sell(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test that cooldown is set after successful sell."""
        monitor = PoolMonitor(
            bot_config.rpc_endpoint,
            bot_config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            bot_config,
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet
        )

        token_mint = "SOLD_TOKEN_123"

        # Initially not in cooldown
        assert monitor._check_token_cooldown(token_mint) == True

        # Simulate sell completion
        monitor._set_token_cooldown(token_mint)

        # Should now be in cooldown
        assert monitor._check_token_cooldown(token_mint) == False

        # Verify cooldown timestamp was set
        assert token_mint in monitor.token_cooldowns
        assert isinstance(monitor.token_cooldowns[token_mint], float)
