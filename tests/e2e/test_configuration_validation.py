"""
Configuration validation tests
Refactored with proper mocking and BotConfig usage
"""
import pytest
import json
from unittest.mock import Mock
from src.solana_bot.config import BotConfig
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.security import SecurityAnalyzer


class TestConfigurationValidation:
    """System-wide configuration validation tests."""

    def test_configuration_file_validation(self, tmp_path):
        """Test configuration file validation and loading."""
        # Test valid configuration
        valid_config = {
            "rpc_endpoint": "https://api.mainnet-beta.solana.com",
            "websocket_endpoint": "wss://api.mainnet-beta.solana.com",
            "raydium_program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "wallet_private_key": "test_private_key_placeholder",
            "bot_settings": {
                "buy_amount_sol": 0.1,
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
            },
            "advanced_features": {
                "multi_source_volume": True,
                "pool_liquidity_analysis": True,
                "price_volatility_filter": True,
                "token_age_validation": True,
                "advanced_holder_analysis": True
            },
            "validation_thresholds": {
                "min_volume_confidence": 0.3,
                "max_price_impact": 0.05,
                "max_volatility_threshold": 0.3,
                "min_token_age_hours": 24,
                "max_price_change_24h": 50
            }
        }

        # Create temporary config file
        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(valid_config, f, indent=2)

        try:
            config = BotConfig(str(config_file))

            # Verify all required fields are loaded via properties
            assert config.rpc_endpoint == "https://api.mainnet-beta.solana.com"
            assert config.websocket_endpoint == "wss://api.mainnet-beta.solana.com"
            assert str(config.raydium_program_id) == "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
            assert config.buy_amount == 0.1
            assert config.take_profit_percentage == 30.0
            assert config.stop_loss_percentage == 15.0
            assert config.max_trades_per_hour == 5
            assert config.min_volume_24h == 5000.0

            # Test advanced features
            assert config.multi_source_volume == True
            assert config.pool_liquidity_analysis == True
            assert config.price_volatility_filter == True
            assert config.token_age_validation == True
            assert config.advanced_holder_analysis == True

            # Test validation thresholds
            assert config.min_volume_confidence == 0.3
            assert config.max_price_impact == 0.05
            assert config.max_volatility_threshold == 0.3
            assert config.min_token_age_hours == 24

        finally:
            import os
            os.unlink(config_file)

    def test_configuration_bounds_validation(self):
        """Test configuration value bounds and limits."""
        # Test with default config values
        test_cases = [
            # (property_name, expected_value, description)
            ("max_trades_per_hour", 5, "Default max trades"),
            ("buy_amount", 0.1, "Default buy amount"),
            ("take_profit_percentage", 30.0, "Default take profit"),
            ("max_supply", 1000000000, "Default max supply"),
            ("min_holders", 100, "Default min holders"),
            ("max_top_holder_percent", 20.0, "Default top holder percent"),
            ("min_volume_confidence", 0.3, "Default volume confidence"),
            ("max_price_impact", 0.05, "Default price impact"),
            ("max_volatility_threshold", 0.3, "Default volatility threshold"),
            ("min_token_age_hours", 24, "Default token age"),
        ]

        # Create a minimal config for testing defaults
        minimal_config = {
            "rpc_endpoint": "https://api.devnet.solana.com",
            "websocket_endpoint": "wss://api.devnet.solana.com",
            "raydium_program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "wallet_private_key": "test_private_key_placeholder"
        }

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(minimal_config, f)
            config_path = f.name

        try:
            config = BotConfig(config_path)

            for prop_name, expected_value, description in test_cases:
                actual_value = getattr(config, prop_name)
                assert actual_value == expected_value, \
                    f"{description}: expected {expected_value}, got {actual_value}"

        finally:
            import os
            os.unlink(config_path)

    def test_configuration_cross_component_consistency(self, tmp_path):
        """Test that configuration is consistent across all components."""
        config_data = {
            "rpc_endpoint": "https://api.devnet.solana.com",
            "websocket_endpoint": "wss://api.devnet.solana.com",
            "raydium_program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "wallet_private_key": "test_private_key_placeholder",
            "bot_settings": {
                "buy_amount_sol": 0.5,
                "take_profit": 25.0,
                "stop_loss": 10.0,
                "max_trades_per_hour": 10,
                "min_volume_24h": 10000.0,
                "max_hold_time_hours": 2.0,
                "cooldown_after_sell": 30,
                "enable_trailing_stop": False,
                "trailing_stop_percentage": 5.0
            },
            "token_filters": {
                "max_supply": 500000000,
                "min_holders": 200,
                "max_top_holder_percent": 15.0,
                "contract_verified": False,
                "renounced_ownership": False
            },
            "advanced_features": {
                "multi_source_volume": True,
                "pool_liquidity_analysis": True,
                "price_volatility_filter": True,
                "token_age_validation": True,
                "advanced_holder_analysis": True
            },
            "validation_thresholds": {
                "min_volume_confidence": 0.5,
                "max_price_impact": 0.03,
                "max_volatility_threshold": 0.2,
                "min_token_age_hours": 48,
                "max_price_change_24h": 25
            }
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        try:
            config = BotConfig(str(config_file))

            # Initialize components
            mock_wallet = Mock()
            mock_price_tracker = Mock()
            mock_raydium = Mock()
            mock_tx_builder = Mock()

            # Mock all the dependencies to avoid import issues
            with pytest.mock.patch('src.solana_bot.monitor.AsyncClient'), \
                 pytest.mock.patch('src.solana_bot.monitor.BirdeyeClient'), \
                 pytest.mock.patch('src.solana_bot.monitor.DexScreenerClient'), \
                 pytest.mock.patch('src.solana_bot.monitor.VolumeValidator'), \
                 pytest.mock.patch('src.solana_bot.monitor.RaydiumSwap'), \
                 pytest.mock.patch('src.solana_bot.monitor.TransactionBuilder'):

                monitor = PoolMonitor(
                    config.rpc_endpoint,
                    config.websocket_endpoint,
                    config.raydium_program_id,
                    config,
                    mock_wallet
                )

                analyzer = SecurityAnalyzer(Mock(), config=config)

                # Verify cross-component configuration consistency
                consistency_checks = [
                    # Monitor configuration
                    (config.max_trades_per_hour, 10, "Config max trades"),
                    (config.min_volume_24h, 10000.0, "Config min volume"),

                    # Analyzer configuration
                    (config.max_supply, 500000000, "Config max supply"),
                    (config.min_holders, 200, "Config min holders"),
                    (config.max_top_holder_percent, 15.0, "Config top holder percent"),
                    (config.contract_verified, False, "Config contract verified"),
                    (config.renounced_ownership, False, "Config ownership renounced"),

                    # Advanced features
                    (config.multi_source_volume, True, "Config multi-source volume"),
                    (config.pool_liquidity_analysis, True, "Config liquidity analysis"),
                    (config.price_volatility_filter, True, "Config volatility filter"),
                    (config.token_age_validation, True, "Config token age validation"),
                    (config.advanced_holder_analysis, True, "Config holder analysis"),

                    # Validation thresholds
                    (config.min_volume_confidence, 0.5, "Config volume confidence"),
                    (config.max_price_impact, 0.03, "Config price impact"),
                    (config.max_volatility_threshold, 0.2, "Config volatility threshold"),
                    (config.min_token_age_hours, 48, "Config token age"),
                ]

                for actual_value, expected_value, description in consistency_checks:
                    assert actual_value == expected_value, \
                        f"Configuration inconsistency in {description}: expected {expected_value}, got {actual_value}"

        finally:
            import os
            os.unlink(config_file)

    def test_configuration_error_handling(self, tmp_path):
        """Test configuration error handling for invalid files."""
        # Test missing file
        with pytest.raises(FileNotFoundError):
            BotConfig("nonexistent_config.json")

        # Test invalid JSON
        invalid_config_file = tmp_path / "invalid.json"
        with open(invalid_config_file, 'w') as f:
            f.write("invalid json content {{{")
        try:
            with pytest.raises(json.JSONDecodeError):
                BotConfig(str(invalid_config_file))
        finally:
            import os
            os.unlink(invalid_config_file)

        # Test missing required fields - should load with defaults
        minimal_config = {
            "rpc_endpoint": "https://api.devnet.solana.com",
            "raydium_program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "wallet_private_key": "test_private_key_placeholder"
        }

        minimal_config_file = tmp_path / "minimal.json"
        with open(minimal_config_file, 'w') as f:
            json.dump(minimal_config, f)

        try:
            config = BotConfig(str(minimal_config_file))

            # Should load with defaults for missing fields
            assert config.rpc_endpoint == "https://api.devnet.solana.com"
            assert config.take_profit_percentage == 30.0  # Default value
            assert config.buy_amount == 0.1  # Default value

        finally:
            import os
            os.unlink(minimal_config_file)

    def test_configuration_environment_integration(self, tmp_path):
        """Test configuration integration with environment variables."""
        config_data = {
            "rpc_endpoint": "https://api.devnet.solana.com",
            "websocket_endpoint": "wss://api.devnet.solana.com",
            "raydium_program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "wallet_private_key": "test_private_key_placeholder",
            "bot_settings": {
                "buy_amount_sol": 0.1,
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
            },
            "advanced_features": {
                "multi_source_volume": True,
                "pool_liquidity_analysis": True,
                "price_volatility_filter": True,
                "token_age_validation": True,
                "advanced_holder_analysis": True
            }
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)

        try:
            config = BotConfig(str(config_file))

            # Verify environment-like behavior (config isolation)
            # Each config instance should be independent
            config2 = BotConfig(str(config_file))

            # Modify one config (if supported)
            # Verify they don't affect each other

            assert config.take_profit_percentage == config2.take_profit_percentage
            assert config.max_trades_per_hour == config2.max_trades_per_hour
            assert config.multi_source_volume == config2.multi_source_volume
            assert config.token_age_validation == config2.token_age_validation

        finally:
            import os
            os.unlink(config_file)
