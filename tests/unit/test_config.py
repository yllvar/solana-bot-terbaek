"""
Unit tests for BotConfig class enhancements
"""
import pytest
import json
from src.solana_bot.config import BotConfig


class TestBotConfigEnhancements:
    """Test enhanced BotConfig class with new trading parameters and token filters."""

    def test_trading_parameters(self, test_config_file):
        """Test all new trading parameter properties."""
        config = BotConfig()
        config.load_from_file(str(test_config_file))

        # Test basic trading parameters
        assert config.take_profit == 30.0
        assert config.stop_loss == 15.0

        # Test rate limiting parameters
        assert config.max_trades_per_hour == 5
        assert config.cooldown_after_sell == 60

        # Test position management parameters
        assert config.max_hold_time_hours == 4.0
        assert config.min_volume_24h == 5000.0

        # Test trailing stop parameters
        assert config.enable_trailing_stop == True
        assert config.trailing_stop_percentage == 10.0

    def test_token_filters(self, test_config_file):
        """Test all new token filter properties."""
        config = BotConfig()
        config.load_from_file(str(test_config_file))

        # Test supply filters
        assert config.max_supply == 1000000000

        # Test holder filters
        assert config.min_holders == 100
        assert config.max_top_holder_percent == 20.0

        # Test contract filters
        assert config.contract_verified == True
        assert config.renounced_ownership == True

    def test_config_defaults(self):
        """Test configuration defaults when values are missing."""
        config = BotConfig()

        # Test with minimal config
        minimal_config = {
            "rpc_endpoint": "https://api.mainnet.solana.com",
            "websocket_endpoint": "wss://api.mainnet.solana.com",
            "wallet_private_key": "test_key"
        }

        config.config = minimal_config

        # Should use defaults for missing values
        assert config.take_profit == 100.0  # default
        assert config.stop_loss == 50.0    # default
        assert config.max_trades_per_hour == 5  # default
        assert config.max_supply == 1000000000  # default
        assert config.min_holders == 100  # default

    def test_config_validation(self, test_config_file):
        """Test configuration value validation."""
        config = BotConfig()
        config.load_from_file(str(test_config_file))

        # Test that values are within reasonable ranges
        assert config.take_profit > 0 and config.take_profit <= 1000
        assert config.stop_loss > 0 and config.stop_loss < config.take_profit
        assert config.max_trades_per_hour > 0 and config.max_trades_per_hour <= 100
        assert config.max_hold_time_hours > 0 and config.max_hold_time_hours <= 168  # 1 week
        assert config.min_volume_24h >= 0
        assert config.trailing_stop_percentage > 0 and config.trailing_stop_percentage <= 50

    def test_token_filter_validation(self, test_config_file):
        """Test token filter value validation."""
        config = BotConfig()
        config.load_from_file(str(test_config_file))

        # Test supply limits
        assert config.max_supply > 0

        # Test holder requirements
        assert config.min_holders > 0
        assert config.max_top_holder_percent > 0 and config.max_top_holder_percent <= 100

        # Test boolean filters
        assert isinstance(config.contract_verified, bool)
        assert isinstance(config.renounced_ownership, bool)

    def test_update_setting_functionality(self, test_config_file):
        """Test the update_setting method works correctly."""
        config = BotConfig()
        config.load_from_file(str(test_config_file))

        # Test updating trading parameters
        config.update_setting('bot_settings.take_profit', 50.0)
        assert config.take_profit == 50.0

        config.update_setting('bot_settings.max_trades_per_hour', 10)
        assert config.max_trades_per_hour == 10

        # Test updating token filters
        config.update_setting('token_filters.max_supply', 2000000000)
        assert config.max_supply == 2000000000

        config.update_setting('token_filters.contract_verified', False)
        assert config.contract_verified == False

    def test_config_persistence(self, test_config_file, tmp_path):
        """Test that configuration changes can be saved and reloaded."""
        config = BotConfig()
        config.load_from_file(str(test_config_file))

        # Modify some settings
        original_tp = config.take_profit
        config.update_setting('bot_settings.take_profit', 75.0)
        config.update_setting('token_filters.max_supply', 500000000)

        # Save to new file
        new_config_file = tmp_path / "modified_config.json"
        with open(new_config_file, 'w') as f:
            json.dump(config.config, f, indent=2)

        # Load into new config instance
        new_config = BotConfig()
        new_config.load_from_file(str(new_config_file))

        # Verify changes persisted
        assert new_config.take_profit == 75.0
        assert new_config.max_supply == 500000000

        # Verify original config unchanged
        config.load_from_file(str(test_config_file))
        assert config.take_profit == original_tp
