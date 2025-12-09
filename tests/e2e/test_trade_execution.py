"""
End-to-end tests for trade execution simulation
"""
import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from solana_bot.triggers import TradeTriggers
from solana_bot.monitor import PoolMonitor
from solana_bot.config import BotConfig


class TestTradeExecutionE2E:
    """End-to-end tests for trade execution simulation."""

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
            }
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return config_file

    @pytest.fixture
    def mock_components(self):
        """Create mock components for trade execution."""
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

    def test_trade_execution_setup(self, test_config, mock_components):
        """Test trade execution component setup."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        # Test PoolMonitor setup
        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            config,
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet']
        )

        # Test TradeTriggers setup
        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        assert monitor.config == config
        assert triggers.config == config

    @pytest.mark.asyncio
    async def test_complete_buy_execution_workflow(self, test_config, mock_components):
        """Test complete buy execution workflow."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            config,
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet']
        )

        # Mock security analyzer
        mock_analyzer = Mock()
        mock_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})
        monitor.security_analyzer = mock_analyzer

        # Mock successful buy transaction
        mock_components['transaction_builder'].build_buy_transaction = AsyncMock(return_value=Mock())

        # Mock all validation checks
        with patch.object(monitor, '_check_rate_limit', return_value=True), \
             patch.object(monitor, '_check_token_cooldown', return_value=True), \
             patch.object(monitor, '_check_token_volume', return_value=True), \
             patch.object(monitor, '_execute_buy_transaction', return_value=True):

            pool_data = {
                'pool_address': 'POOL_123',
                'token_mint': 'TOKEN_123',
                'base_mint': 'So11111111111111111111111111111111111111112',
                'quote_mint': 'TOKEN_123',
                'initial_liquidity': 10000.0
            }

            # Execute buy
            result = await monitor.execute_auto_buy(pool_data)

            assert result == True
            mock_analyzer.check_token_filters.assert_called_once_with('TOKEN_123')
            monitor._execute_buy_transaction.assert_called_once()

    def test_position_management_setup(self, test_config, mock_components):
        """Test position management setup after buy."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Simulate position opening (normally done by monitor)
        token_mint = 'TOKEN_123'
        entry_price = 1.0
        amount = 100
        pool_address = 'POOL_123'

        triggers.open_position(token_mint, entry_price, amount, 10.0, pool_address)

        # Verify position was created
        assert token_mint in triggers.positions
        position = triggers.positions[token_mint]
        assert position['entry_price'] == entry_price
        assert position['amount'] == amount
        assert position['highest_price'] == entry_price
        assert 'entry_time' in position
        assert position['pool_address'] == pool_address

    @pytest.mark.asyncio
    async def test_take_profit_execution(self, test_config, mock_components):
        """Test take profit trigger execution."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Setup position
        token_mint = 'TOKEN_123'
        entry_price = 1.0
        triggers.open_position(token_mint, entry_price, 100, 10.0, 'POOL_123')
        triggers.set_triggers(token_mint, 30.0, 15.0)  # 30% take profit

        # Mock sell transaction
        mock_components['transaction_builder'].build_sell_transaction = AsyncMock(return_value=Mock())

        # Simulate price reaching take profit level
        tp_price = entry_price * 1.35  # 35% profit

        await triggers.check_triggers(token_mint, tp_price, tp_price)

        # Verify sell was triggered
        mock_components['transaction_builder'].build_sell_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_loss_execution(self, test_config, mock_components):
        """Test stop loss trigger execution."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Setup position
        token_mint = 'TOKEN_123'
        entry_price = 1.0
        triggers.open_position(token_mint, entry_price, 100, 10.0, 'POOL_123')
        triggers.set_triggers(token_mint, 30.0, 15.0)  # 15% stop loss

        # Mock sell transaction
        mock_components['transaction_builder'].build_sell_transaction = AsyncMock(return_value=Mock())

        # Simulate price dropping to stop loss level
        sl_price = entry_price * 0.82  # 18% loss

        await triggers.check_triggers(token_mint, sl_price, sl_price)

        # Verify sell was triggered
        mock_components['transaction_builder'].build_sell_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_trailing_stop_execution(self, test_config, mock_components):
        """Test trailing stop trigger execution."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Setup position
        token_mint = 'TOKEN_123'
        entry_price = 1.0
        triggers.open_position(token_mint, entry_price, 100, 10.0, 'POOL_123')
        triggers.set_triggers(token_mint, 30.0, 15.0)

        # Mock sell transaction
        mock_components['transaction_builder'].build_sell_transaction = AsyncMock(return_value=Mock())

        # Simulate price increase then drop below trailing stop
        high_price = 1.5  # 50% profit
        triggers.positions[token_mint]['highest_price'] = high_price

        # Calculate trailing stop price
        trailing_stop = high_price * (1 - config.trailing_stop_percentage / 100)
        current_price = trailing_stop * 0.95  # Below trailing stop

        await triggers.check_triggers(token_mint, current_price, high_price)

        # Verify sell was triggered
        mock_components['transaction_builder'].build_sell_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_max_hold_time_execution(self, test_config, mock_components):
        """Test max hold time trigger execution."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Setup position
        token_mint = 'TOKEN_123'
        entry_price = 1.0
        triggers.open_position(token_mint, entry_price, 100, 10.0, 'POOL_123')
        triggers.set_triggers(token_mint, 30.0, 15.0)

        # Mock sell transaction
        mock_components['transaction_builder'].build_sell_transaction = AsyncMock(return_value=Mock())

        # Simulate position being held too long
        max_hold_seconds = config.max_hold_time_hours * 3600
        old_entry_time = time.time() - (max_hold_seconds + 60)  # Past limit
        triggers.positions[token_mint]['entry_time'] = old_entry_time

        # Check triggers with current price
        await triggers.check_triggers(token_mint, entry_price, entry_price)

        # Verify sell was triggered due to timeout
        mock_components['transaction_builder'].build_sell_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_trade_lifecycle_e2e(self, test_config, mock_components):
        """Test complete trade lifecycle: buy -> monitor -> sell."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        # Setup components
        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            config,
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet']
        )

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Phase 1: Buy execution
        pool_data = {
            'pool_address': 'POOL_123',
            'token_mint': 'TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'TOKEN_123'
        }

        # Mock successful buy
        mock_analyzer = Mock()
        mock_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})
        monitor.security_analyzer = mock_analyzer

        with patch.object(monitor, '_check_rate_limit', return_value=True), \
             patch.object(monitor, '_check_token_cooldown', return_value=True), \
             patch.object(monitor, '_check_token_volume', return_value=True), \
             patch.object(monitor, '_execute_buy_transaction', return_value=True):

            buy_result = await monitor.execute_auto_buy(pool_data)
            assert buy_result == True

        # Phase 2: Position monitoring setup
        token_mint = 'TOKEN_123'
        entry_price = 1.0
        triggers.open_position(token_mint, entry_price, 100, 10.0, 'POOL_123')
        triggers.set_triggers(token_mint, 30.0, 15.0)

        # Phase 3: Profit taking
        mock_components['transaction_builder'].build_sell_transaction = AsyncMock(return_value=Mock())

        # Price reaches take profit
        tp_price = entry_price * 1.35
        await triggers.check_triggers(token_mint, tp_price, tp_price)

        # Verify complete lifecycle
        assert buy_result == True
        mock_components['transaction_builder'].build_sell_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_positions_management(self, test_config, mock_components):
        """Test managing multiple positions simultaneously."""
        config = BotConfig()
        config.load_from_file(str(test_config))

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Create multiple positions
        positions = [
            ('TOKEN_1', 1.0, 100),
            ('TOKEN_2', 2.0, 50),
            ('TOKEN_3', 0.5, 200)
        ]

        for token_mint, entry_price, amount in positions:
            triggers.open_position(token_mint, entry_price, amount, 10.0, f'POOL_{token_mint}')
            triggers.set_triggers(token_mint, 30.0, 15.0)

        # Verify all positions exist
        assert len(triggers.positions) == 3
        assert len(triggers.triggers) == 3

        # Mock sell transaction
        mock_components['transaction_builder'].build_sell_transaction = AsyncMock(return_value=Mock())

        # Trigger sell for first token
        tp_price = 1.0 * 1.35  # 35% profit
        await triggers.check_triggers('TOKEN_1', tp_price, tp_price)

        # Verify only first position was sold
        assert mock_components['transaction_builder'].build_sell_transaction.call_count == 1
        assert 'TOKEN_1' in triggers.positions  # Position still exists until cleanup
