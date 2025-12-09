"""
Unit tests for SecurityAnalyzer class enhancements
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from solana_bot.security import SecurityAnalyzer
from solana_bot.config import BotConfig


class TestSecurityAnalyzerEnhancements:
    """Test enhanced SecurityAnalyzer class with comprehensive token filtering."""

    def test_security_analyzer_initialization(self, bot_config, mock_solana_client):
        """Test SecurityAnalyzer initialization with config."""
        analyzer = SecurityAnalyzer(
            mock_solana_client,
            config=bot_config
        )

        assert analyzer.client == mock_solana_client
        assert analyzer.config == bot_config
        assert analyzer.min_liquidity_sol == 5.0
        assert analyzer.max_top_holder_pct == 20.0
        assert analyzer.max_risk_score == 50

    def test_token_filter_checks_safe_token(self, bot_config, mock_solana_client, sample_token_data):
        """Test token filter checks with safe token data."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock successful responses for all checks
        with patch.object(analyzer, '_get_token_supply', return_value=sample_token_data['supply']), \
             patch.object(analyzer, '_get_holder_count', return_value=sample_token_data['holder_count']), \
             patch.object(analyzer, '_get_top_holder_percent', return_value=sample_token_data['top_holder_percent']), \
             patch.object(analyzer, '_check_contract_verified', return_value=sample_token_data['is_verified']), \
             patch.object(analyzer, '_check_ownership_renounced', return_value=sample_token_data['ownership_renounced']):

            import asyncio
            result = asyncio.run(analyzer.check_token_filters(sample_token_data['address']))

            # Should pass all filters
            assert result['passed'] == True
            assert result['supply_check']['passed'] == True
            assert result['holders_check']['passed'] == True
            assert result['top_holder_check']['passed'] == True
            assert result['contract_check']['passed'] == True
            assert result['ownership_check']['passed'] == True

    def test_token_filter_checks_risky_token(self, bot_config, mock_solana_client, risky_token_data):
        """Test token filter checks with risky token data."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock responses that fail filters
        with patch.object(analyzer, '_get_token_supply', return_value=risky_token_data['supply']), \
             patch.object(analyzer, '_get_holder_count', return_value=risky_token_data['holder_count']), \
             patch.object(analyzer, '_get_top_holder_percent', return_value=risky_token_data['top_holder_percent']), \
             patch.object(analyzer, '_check_contract_verified', return_value=risky_token_data['is_verified']), \
             patch.object(analyzer, '_check_ownership_renounced', return_value=risky_token_data['ownership_renounced']):

            import asyncio
            result = asyncio.run(analyzer.check_token_filters(risky_token_data['address']))

            # Should fail multiple filters
            assert result['passed'] == False
            assert result['supply_check']['passed'] == False  # Supply too high
            assert result['holders_check']['passed'] == False  # Too few holders
            assert result['top_holder_check']['passed'] == False  # Top holder too high
            assert result['contract_check']['passed'] == False  # Not verified
            assert result['ownership_check']['passed'] == False  # Ownership not renounced

    def test_supply_filter_logic(self, bot_config, mock_solana_client):
        """Test supply filter logic specifically."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Test within limit
        with patch.object(analyzer, '_get_token_supply', return_value=500000000):
            import asyncio
            result = asyncio.run(analyzer._check_supply_filter("TEST_TOKEN"))
            assert result['passed'] == True
            assert result['supply'] == 500000000

        # Test exceeding limit
        with patch.object(analyzer, '_get_token_supply', return_value=2000000000):
            import asyncio
            result = asyncio.run(analyzer._check_supply_filter("TEST_TOKEN"))
            assert result['passed'] == False
            assert result['supply'] == 2000000000

    def test_holder_filter_logic(self, bot_config, mock_solana_client):
        """Test holder filter logic specifically."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Test sufficient holders
        with patch.object(analyzer, '_get_holder_count', return_value=150):
            import asyncio
            result = asyncio.run(analyzer._check_holder_filter("TEST_TOKEN"))
            assert result['passed'] == True
            assert result['holder_count'] == 150

        # Test insufficient holders
        with patch.object(analyzer, '_get_holder_count', return_value=50):
            import asyncio
            result = asyncio.run(analyzer._check_holder_filter("TEST_TOKEN"))
            assert result['passed'] == False
            assert result['holder_count'] == 50

    def test_top_holder_filter_logic(self, bot_config, mock_solana_client):
        """Test top holder concentration filter logic."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Test acceptable concentration
        with patch.object(analyzer, '_get_top_holder_percent', return_value=15.0):
            import asyncio
            result = asyncio.run(analyzer._check_top_holder_filter("TEST_TOKEN"))
            assert result['passed'] == True
            assert result['top_holder_percent'] == 15.0

        # Test excessive concentration
        with patch.object(analyzer, '_get_top_holder_percent', return_value=35.0):
            import asyncio
            result = asyncio.run(analyzer._check_top_holder_filter("TEST_TOKEN"))
            assert result['passed'] == False
            assert result['top_holder_percent'] == 35.0

    def test_contract_verification_logic(self, bot_config, mock_solana_client):
        """Test contract verification logic."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Test verified contract
        with patch.object(analyzer, '_check_contract_verified', return_value=True):
            import asyncio
            result = asyncio.run(analyzer._check_contract_filter("TEST_TOKEN"))
            assert result['passed'] == True
            assert result['verified'] == True

        # Test unverified contract
        with patch.object(analyzer, '_check_contract_verified', return_value=False):
            import asyncio
            result = asyncio.run(analyzer._check_contract_filter("TEST_TOKEN"))
            assert result['passed'] == False
            assert result['verified'] == False

    def test_ownership_renouncement_logic(self, bot_config, mock_solana_client):
        """Test ownership renouncement logic."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Test renounced ownership
        with patch.object(analyzer, '_check_ownership_renounced', return_value=True):
            import asyncio
            result = asyncio.run(analyzer._check_ownership_filter("TEST_TOKEN"))
            assert result['passed'] == True
            assert result['renounced'] == True

        # Test retained ownership
        with patch.object(analyzer, '_check_ownership_renounced', return_value=False):
            import asyncio
            result = asyncio.run(analyzer._check_ownership_filter("TEST_TOKEN"))
            assert result['passed'] == False
            assert result['renounced'] == False

    def test_error_handling(self, bot_config, mock_solana_client):
        """Test error handling in token filter checks."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock all methods to raise exceptions
        with patch.object(analyzer, '_get_token_supply', side_effect=Exception("RPC Error")), \
             patch.object(analyzer, '_get_holder_count', side_effect=Exception("API Error")), \
             patch.object(analyzer, '_get_top_holder_percent', side_effect=Exception("Network Error")), \
             patch.object(analyzer, '_check_contract_verified', side_effect=Exception("Verification Error")), \
             patch.object(analyzer, '_check_ownership_renounced', side_effect=Exception("Ownership Error")):

            import asyncio
            result = asyncio.run(analyzer.check_token_filters("ERROR_TOKEN"))

            # Should handle errors gracefully and return failed checks
            assert result['passed'] == False
            assert 'error' in result['supply_check']
            assert 'error' in result['holders_check']
            assert 'error' in result['top_holder_check']
            assert 'error' in result['contract_check']
            assert 'error' in result['ownership_check']

    def test_config_parameter_usage(self, mock_solana_client):
        """Test that config parameters are properly used."""
        # Create custom config
        custom_config = BotConfig()
        custom_config.config = {
            'token_filters': {
                'max_supply': 500000000,  # Lower limit
                'min_holders': 200,       # Higher requirement
                'max_top_holder_percent': 10.0,  # Stricter limit
                'contract_verified': False,      # Allow unverified
                'renounced_ownership': False     # Allow retained ownership
            }
        }

        analyzer = SecurityAnalyzer(mock_solana_client, config=custom_config)

        # Test that custom limits are used
        assert analyzer.config.max_supply == 500000000
        assert analyzer.config.min_holders == 200
        assert analyzer.config.max_top_holder_percent == 10.0
        assert analyzer.config.contract_verified == False
        assert analyzer.config.renounced_ownership == False

    def test_empty_config_fallback(self, mock_solana_client):
        """Test fallback behavior when config is not provided."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=None)

        # Should use default values
        assert analyzer.config is None
        # Would need to test that default values are used in actual checks
