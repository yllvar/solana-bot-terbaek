"""
Basic unit tests for BotConfig class - standalone version for testing
"""
import pytest
import json
import tempfile
import os


class BasicBotConfig:
    """Simplified BotConfig for testing without full dependencies."""

    def __init__(self):
        self.config = {}

    def load_from_file(self, file_path):
        """Load configuration from JSON file."""
        with open(file_path, 'r') as f:
            self.config = json.load(f)

    def update_setting(self, key_path, value):
        """Update a nested configuration setting."""
        keys = key_path.split('.')
        current = self.config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the value
        current[keys[-1]] = value

    @property
    def take_profit(self):
        return self.config.get('bot_settings', {}).get('take_profit', 100.0)

    @property
    def stop_loss(self):
        return self.config.get('bot_settings', {}).get('stop_loss', 50.0)

    @property
    def max_trades_per_hour(self):
        return self.config.get('bot_settings', {}).get('max_trades_per_hour', 5)

    @property
    def cooldown_after_sell(self):
        return self.config.get('bot_settings', {}).get('cooldown_after_sell', 60)

    @property
    def max_hold_time_hours(self):
        return self.config.get('bot_settings', {}).get('max_hold_time_hours', 4.0)

    @property
    def min_volume_24h(self):
        return self.config.get('bot_settings', {}).get('min_volume_24h', 5000.0)

    @property
    def enable_trailing_stop(self):
        return self.config.get('bot_settings', {}).get('enable_trailing_stop', True)

    @property
    def trailing_stop_percentage(self):
        return self.config.get('bot_settings', {}).get('trailing_stop_percentage', 10.0)

    @property
    def max_supply(self):
        return self.config.get('token_filters', {}).get('max_supply', 1000000000)

    @property
    def min_holders(self):
        return self.config.get('token_filters', {}).get('min_holders', 100)

    @property
    def max_top_holder_percent(self):
        return self.config.get('token_filters', {}).get('max_top_holder_percent', 20.0)

    @property
    def contract_verified(self):
        return self.config.get('token_filters', {}).get('contract_verified', True)

    @property
    def renounced_ownership(self):
        return self.config.get('token_filters', {}).get('renounced_ownership', True)


class TestBasicBotConfig:
    """Test basic BotConfig functionality without full dependencies."""

    def test_trading_parameters(self):
        """Test all new trading parameter properties."""
        config = BasicBotConfig()

        # Load test configuration
        test_config = {
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

        config.config = test_config

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

    def test_token_filters(self):
        """Test all new token filter properties."""
        config = BasicBotConfig()

        test_config = {
            "token_filters": {
                "max_supply": 1000000000,
                "min_holders": 100,
                "max_top_holder_percent": 20.0,
                "contract_verified": True,
                "renounced_ownership": True
            }
        }

        config.config = test_config

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
        config = BasicBotConfig()

        # Test with minimal config
        minimal_config = {}

        config.config = minimal_config

        # Should use defaults for missing values
        assert config.take_profit == 100.0  # default
        assert config.stop_loss == 50.0    # default
        assert config.max_trades_per_hour == 5  # default
        assert config.max_supply == 1000000000  # default
        assert config.min_holders == 100  # default

    def test_config_validation(self):
        """Test configuration value validation."""
        config = BasicBotConfig()

        test_config = {
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

        config.config = test_config

        # Test that values are within reasonable ranges
        assert config.take_profit > 0 and config.take_profit <= 1000
        assert config.stop_loss > 0 and config.stop_loss < config.take_profit
        assert config.max_trades_per_hour > 0 and config.max_trades_per_hour <= 100
        assert config.max_hold_time_hours > 0 and config.max_hold_time_hours <= 168  # 1 week
        assert config.min_volume_24h >= 0
        assert config.trailing_stop_percentage > 0 and config.trailing_stop_percentage <= 50

    def test_update_setting_functionality(self):
        """Test the update_setting method works correctly."""
        config = BasicBotConfig()

        initial_config = {
            "bot_settings": {
                "take_profit": 30.0
            }
        }

        config.config = initial_config

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

    def test_config_persistence(self):
        """Test that configuration changes can be saved and reloaded."""
        config = BasicBotConfig()

        initial_config = {
            "bot_settings": {
                "take_profit": 30.0
            }
        }

        config.config = initial_config

        # Modify some settings
        original_tp = config.take_profit
        config.update_setting('bot_settings.take_profit', 75.0)
        config.update_setting('token_filters.max_supply', 500000000)

        # Create temporary file to simulate persistence
        import tempfile
        import json

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config.config, f)
            temp_file = f.name

        try:
            # Load into new config instance
            new_config = BasicBotConfig()
            with open(temp_file, 'r') as f:
                new_config.config = json.load(f)

            # Verify changes persisted
            assert new_config.take_profit == 75.0
            assert new_config.max_supply == 500000000

        finally:
            os.unlink(temp_file)
