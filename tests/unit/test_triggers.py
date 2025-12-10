"""
Unit tests for TradeTriggers class enhancements
"""
import pytest
import time
from unittest.mock import Mock, AsyncMock
from src.solana_bot.triggers import TradeTriggers
from src.solana_bot.config import BotConfig


class TestTradeTriggersEnhancements:
    """Test enhanced TradeTriggers class with trailing stop and position management."""

    def test_trailing_stop_initialization(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test TradeTriggers initialization with config."""
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        assert triggers.config == bot_config
        assert triggers.positions == {}
        assert triggers.triggers == {}

    def test_position_opening(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test opening positions with proper tracking."""
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        entry_price = 1.0
        amount = 100
        pool_address = "POOL_ADDRESS_123"

        triggers.open_position(token_mint, entry_price, amount, 10.0, pool_address)

        # Verify position was created
        assert token_mint in triggers.positions
        position = triggers.positions[token_mint]

        assert position['entry_price'] == entry_price
        assert position['amount'] == amount
        assert position['highest_price'] == entry_price
        assert 'entry_time' in position
        assert position['pool_address'] == pool_address

    def test_trigger_setting(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test setting triggers for positions."""
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        take_profit = 30.0
        stop_loss = 15.0

        triggers.set_triggers(token_mint, take_profit, stop_loss)

        # Verify triggers were set
        assert token_mint in triggers.triggers
        trigger = triggers.triggers[token_mint]

        assert trigger['take_profit'] == take_profit
        assert trigger['stop_loss'] == stop_loss
        assert trigger['enabled'] == True

    def test_trailing_stop_logic(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test trailing stop functionality."""
        mock_transaction_builder.build_sell_transaction = AsyncMock(return_value=Mock())

        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        entry_price = 1.0

        # Open position and set triggers
        triggers.open_position(token_mint, entry_price, 100, 10.0, "POOL_123")
        triggers.set_triggers(token_mint, 30.0, 15.0)

        # Simulate price increase (highest price should update)
        new_price = 1.5
        triggers.positions[token_mint]['highest_price'] = new_price

        # Calculate trailing stop price
        trailing_stop_price = new_price * (1 - bot_config.trailing_stop_percentage / 100)

        # Price drops below trailing stop - should trigger sell
        current_price = trailing_stop_price * 0.95  # Below trailing stop

        import asyncio
        asyncio.run(triggers.check_triggers(token_mint, current_price, new_price))

        # Verify sell transaction was attempted
        mock_transaction_builder.build_sell_transaction.assert_called_once()

    def test_max_hold_time_logic(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test maximum hold time functionality."""
        mock_transaction_builder.build_sell_transaction = AsyncMock(return_value=Mock())

        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        entry_price = 1.0

        # Open position
        triggers.open_position(token_mint, entry_price, 100, 10.0, "POOL_123")
        triggers.set_triggers(token_mint, 30.0, 15.0)

        # Simulate position older than max hold time
        max_hold_seconds = bot_config.max_hold_time_hours * 3600
        old_entry_time = time.time() - (max_hold_seconds + 60)  # 1 minute past limit
        triggers.positions[token_mint]['entry_time'] = old_entry_time

        import asyncio
        asyncio.run(triggers.check_triggers(token_mint, entry_price, entry_price))

        # Verify sell transaction was attempted due to timeout
        mock_transaction_builder.build_sell_transaction.assert_called_once()

    def test_regular_take_profit_trigger(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test regular take profit trigger without trailing stop."""
        mock_transaction_builder.build_sell_transaction = AsyncMock(return_value=Mock())

        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        entry_price = 1.0

        # Open position and set triggers
        triggers.open_position(token_mint, entry_price, 100, 10.0, "POOL_123")
        triggers.set_triggers(token_mint, 30.0, 15.0)  # 30% take profit

        # Price reaches take profit level
        tp_price = entry_price * 1.35  # 35% profit

        import asyncio
        asyncio.run(triggers.check_triggers(token_mint, tp_price, tp_price))

        # Verify sell transaction was attempted
        mock_transaction_builder.build_sell_transaction.assert_called_once()

    def test_stop_loss_trigger(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test stop loss trigger functionality."""
        mock_transaction_builder.build_sell_transaction = AsyncMock(return_value=Mock())

        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        entry_price = 1.0

        # Open position and set triggers
        triggers.open_position(token_mint, entry_price, 100, 10.0, "POOL_123")
        triggers.set_triggers(token_mint, 30.0, 15.0)  # 15% stop loss

        # Price drops to stop loss level
        sl_price = entry_price * 0.82  # 18% loss

        import asyncio
        asyncio.run(triggers.check_triggers(token_mint, sl_price, sl_price))

        # Verify sell transaction was attempted
        mock_transaction_builder.build_sell_transaction.assert_called_once()

    def test_no_trigger_conditions(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test that no action is taken when trigger conditions aren't met."""
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        entry_price = 1.0

        # Open position and set triggers
        triggers.open_position(token_mint, entry_price, 100, 10.0, "POOL_123")
        triggers.set_triggers(token_mint, 30.0, 15.0)

        # Price stays within normal range
        normal_price = entry_price * 1.10  # 10% profit

        import asyncio
        asyncio.run(triggers.check_triggers(token_mint, normal_price, normal_price))

        # Verify no sell transaction was attempted
        mock_transaction_builder.build_sell_transaction.assert_not_called()

    def test_disabled_triggers(self, bot_config, mock_price_tracker, mock_raydium_swap, mock_transaction_builder, mock_wallet):
        """Test that disabled triggers don't execute."""
        triggers = TradeTriggers(
            mock_price_tracker,
            mock_raydium_swap,
            mock_transaction_builder,
            mock_wallet,
            bot_config
        )

        token_mint = "TEST_TOKEN_123"
        entry_price = 1.0

        # Open position and set disabled triggers
        triggers.open_position(token_mint, entry_price, 100, 10.0, "POOL_123")
        triggers.set_triggers(token_mint, 30.0, 15.0)
        triggers.triggers[token_mint]['enabled'] = False

        # Price reaches take profit level
        tp_price = entry_price * 1.35

        import asyncio
        asyncio.run(triggers.check_triggers(token_mint, tp_price, tp_price))

        # Verify no sell transaction was attempted
        mock_transaction_builder.build_sell_transaction.assert_not_called()
