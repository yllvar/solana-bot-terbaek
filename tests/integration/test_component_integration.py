"""
Integration tests for component interactions
"""
import pytest
from unittest.mock import Mock, AsyncMock
from solana_bot.config import BotConfig
from solana_bot.security import SecurityAnalyzer
from solana_bot.monitor import PoolMonitor
from solana_bot.triggers import TradeTriggers


class TestComponentIntegration:
    """Test integration between bot components."""

    def test_config_to_security_integration(self, bot_config, mock_solana_client):
        """Test that config properly flows to SecurityAnalyzer."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Verify config values are accessible
        assert analyzer.config.max_supply == bot_config.max_supply
        assert analyzer.config.min_holders == bot_config.min_holders
        assert analyzer.config.max_top_holder_percent == bot_config.max_top_holder_percent
        assert analyzer.config.contract_verified == bot_config.contract_verified
        assert analyzer.config.renounced_ownership == bot_config.renounced_ownership

    def test_config_to_monitor_integration(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test that config properly flows to PoolMonitor."""
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

        # Verify config values are accessible
        assert monitor.config.max_trades_per_hour == bot_config.max_trades_per_hour
        assert monitor.config.cooldown_after_sell == bot_config.cooldown_after_sell
        assert monitor.config.min_volume_24h == bot_config.min_volume_24h

    def test_config_to_triggers_integration(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test that config properly flows to TradeTriggers."""
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        # Verify config values are accessible
        assert triggers.config.take_profit == bot_config.take_profit
        assert triggers.config.stop_loss == bot_config.stop_loss
        assert triggers.config.enable_trailing_stop == bot_config.enable_trailing_stop
        assert triggers.config.trailing_stop_percentage == bot_config.trailing_stop_percentage
        assert triggers.config.max_hold_time_hours == bot_config.max_hold_time_hours

    def test_security_monitor_integration(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test SecurityAnalyzer integration with PoolMonitor."""
        # Create monitor with security analyzer
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

        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)
        monitor.security_analyzer = analyzer

        # Mock successful token analysis
        analyzer.check_token_filters = AsyncMock(return_value={
            'passed': True,
            'supply_check': {'passed': True},
            'holders_check': {'passed': True},
            'contract_check': {'passed': True},
            'ownership_check': {'passed': True}
        })

        token_mint = "SAFE_TOKEN_123"
        import asyncio
        result = asyncio.run(monitor._check_token_filters(token_mint))

        assert result == True
        analyzer.check_token_filters.assert_called_once_with(token_mint)

    def test_full_buy_workflow_integration(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test complete buy workflow from pool detection to execution."""
        # Create all components
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

        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)
        monitor.security_analyzer = analyzer

        # Mock all checks to pass
        analyzer.check_token_filters = AsyncMock(return_value={'passed': True})

        with AsyncMock() as mock_buy_tx:
            mock_transaction_builder.build_buy_transaction = mock_buy_tx
            mock_buy_tx.return_value = Mock()

            # Mock rate limiting and volume checks
            monitor._check_rate_limit = Mock(return_value=True)
            monitor._check_token_cooldown = Mock(return_value=True)
            monitor._check_token_volume = AsyncMock(return_value=True)
            monitor._execute_buy_transaction = AsyncMock(return_value=True)

            # Test complete workflow
            pool_data = {
                'pool_address': 'POOL_123',
                'token_mint': 'TOKEN_123',
                'base_mint': 'So11111111111111111111111111111111111111112',
                'quote_mint': 'TOKEN_123',
                'initial_liquidity': 10000.0
            }

            import asyncio
            result = asyncio.run(monitor.execute_auto_buy(pool_data))

            assert result == True

            # Verify all checks were performed
            analyzer.check_token_filters.assert_called_once_with('TOKEN_123')
            monitor._check_rate_limit.assert_called()
            monitor._check_token_cooldown.assert_called_once_with('TOKEN_123')
            monitor._check_token_volume.assert_called_once_with('TOKEN_123')
            monitor._execute_buy_transaction.assert_called_once()

    def test_position_lifecycle_integration(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test complete position lifecycle from open to close."""
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "LIFECYCLE_TOKEN_123"
        entry_price = 1.0
        pool_address = "POOL_123"

        # Open position
        triggers.open_position(token_mint, entry_price, 100, 10.0, pool_address)

        assert token_mint in triggers.positions
        assert triggers.positions[token_mint]['entry_price'] == entry_price

        # Set triggers
        triggers.set_triggers(token_mint, 30.0, 15.0)

        assert token_mint in triggers.triggers
        assert triggers.triggers[token_mint]['take_profit'] == 30.0
        assert triggers.triggers[token_mint]['stop_loss'] == 15.0

        # Simulate price movement and trigger
        mock_transaction_builder.build_sell_transaction = AsyncMock(return_value=Mock())

        # Price reaches take profit
        tp_price = entry_price * 1.35  # 35% profit

        import asyncio
        asyncio.run(triggers.check_triggers(token_mint, tp_price, tp_price))

        # Verify sell was triggered
        mock_transaction_builder.build_sell_transaction.assert_called_once()

        # Position should still exist (would be cleaned up by monitor)
        assert token_mint in triggers.positions

    def test_error_propagation_integration(self, bot_config, mock_solana_client, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test error handling across component boundaries."""
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

        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)
        monitor.security_analyzer = analyzer

        # Mock security analyzer to fail
        analyzer.check_token_filters = AsyncMock(return_value={'passed': False})

        pool_data = {
            'pool_address': 'POOL_123',
            'token_mint': 'RISKY_TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'RISKY_TOKEN_123'
        }

        import asyncio
        result = asyncio.run(monitor.execute_auto_buy(pool_data))

        # Should fail due to security filter
        assert result == False

    def test_configuration_update_integration(self, test_config_file, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test that configuration updates propagate to all components."""
        config = BotConfig()
        config.load_from_file(str(test_config_file))

        # Create components
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            config
        )

        # Verify initial config
        assert triggers.config.take_profit == 30.0

        # Update config
        config.update_setting('bot_settings.take_profit', 50.0)

        # Verify update propagated
        assert triggers.config.take_profit == 50.0

    def test_rate_limiting_integration(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test rate limiting integration across multiple operations."""
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

        # Fill up rate limit
        current_time = 1000000  # Fixed time for testing
        for i in range(bot_config.max_trades_per_hour):
            monitor.last_trade_times.append(current_time - (i * 60))

        monitor.trade_count = bot_config.max_trades_per_hour

        # First attempt should be rate limited
        pool_data = {
            'pool_address': 'POOL_1',
            'token_mint': 'TOKEN_1',
            'base_mint': 'SOL',
            'quote_mint': 'TOKEN_1'
        }

        import asyncio
        result1 = asyncio.run(monitor.execute_auto_buy(pool_data))
        assert result1 == False  # Rate limited

        # Simulate time passing (1 hour)
        monitor.last_trade_times = []  # Clear old trades
        monitor.trade_count = 0

        # Second attempt should succeed (if other checks pass)
        with AsyncMock() as mock_analyzer:
            mock_analyzer.return_value = {'passed': True}
            monitor.security_analyzer = Mock()
            monitor.security_analyzer.check_token_filters = mock_analyzer

            with AsyncMock() as mock_volume:
                mock_volume.return_value = True
                monitor._check_token_volume = mock_volume

                result2 = asyncio.run(monitor.execute_auto_buy(pool_data))
                assert result2 == True  # Should succeed
