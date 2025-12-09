"""
End-to-end tests for token analysis pipeline
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from solana_bot.security import SecurityAnalyzer
from solana_bot.config import BotConfig


class TestTokenAnalysisE2E:
    """End-to-end tests for token analysis pipeline."""

    @pytest.fixture
    def mock_solana_client(self):
        """Create mock Solana client."""
        client = AsyncMock()
        # Mock account info responses
        client.get_account_info = AsyncMock()
        client.get_account_info.return_value = Mock()
        client.get_account_info.return_value.value = Mock()
        client.get_account_info.return_value.value.data = b"mock_data"
        return client

    def test_token_analysis_pipeline_initialization(self, bot_config, mock_solana_client):
        """Test SecurityAnalyzer initialization for token analysis."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        assert analyzer.client == mock_solana_client
        assert analyzer.config == bot_config
        assert analyzer.min_liquidity_sol == 5.0
        assert analyzer.max_top_holder_pct == 20.0

    @pytest.mark.asyncio
    async def test_complete_token_analysis_safe_token(self, bot_config, mock_solana_client):
        """Test complete token analysis pipeline with safe token."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock analysis methods to return safe results
        with patch.object(analyzer, '_check_token_supply', return_value={'passed': True, 'supply': 500000000}), \
             patch.object(analyzer, '_check_holder_distribution', return_value={'passed': True, 'holder_count': 150}), \
             patch.object(analyzer, '_check_contract_verification', return_value={'passed': True, 'verified': True}), \
             patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': True, 'renounced': True}):

            token_mint = 'SAFE_TOKEN_123'
            result = await analyzer.check_token_filters(token_mint)

            # Verify complete analysis result
            assert result['passed'] == True
            assert result['filters']['supply']['passed'] == True
            assert result['filters']['holders']['passed'] == True
            assert result['filters']['contract_verified']['passed'] == True
            assert result['filters']['ownership_renounced']['passed'] == True

            # Verify all methods were called (can't easily test this with the actual implementation)

    @pytest.mark.asyncio
    async def test_complete_token_analysis_risky_token(self, bot_config, mock_solana_client):
        """Test complete token analysis pipeline with risky token."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock analysis methods to return risky results
        with patch.object(analyzer, '_check_token_supply', return_value={'passed': False, 'supply': 2000000000}), \
             patch.object(analyzer, '_check_holder_distribution', return_value={'passed': False, 'holder_count': 50}), \
             patch.object(analyzer, '_check_contract_verification', return_value={'passed': False, 'verified': False}), \
             patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': False, 'renounced': False}):

            token_mint = 'RISKY_TOKEN_123'
            result = await analyzer.check_token_filters(token_mint)

            # Verify analysis correctly identifies risks
            assert result['passed'] == False
            assert result['filters']['supply']['passed'] == False
            assert result['filters']['holders']['passed'] == False
            assert result['filters']['contract_verified']['passed'] == False
            assert result['filters']['ownership_renounced']['passed'] == False

    @pytest.mark.asyncio
    async def test_token_analysis_with_partial_failures(self, bot_config, mock_solana_client):
        """Test token analysis with some passing and some failing checks."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock mixed results
        with patch.object(analyzer, '_get_token_supply', return_value=800000000), \
             patch.object(analyzer, '_get_holder_count', return_value=80), \
             patch.object(analyzer, '_get_top_holder_percent', return_value=25.0), \
             patch.object(analyzer, '_check_contract_verified', return_value=True), \
             patch.object(analyzer, '_check_ownership_renounced', return_value=True):

            token_mint = 'MIXED_TOKEN_123'
            result = await analyzer.check_token_filters(token_mint)

            # Should fail due to holders and top holder checks
            assert result['passed'] == False
            assert result['supply_check']['passed'] == True    # Supply OK
            assert result['holders_check']['passed'] == False  # Too few holders
            assert result['top_holder_check']['passed'] == False # Concentration too high
            assert result['contract_check']['passed'] == True   # Contract verified
            assert result['ownership_check']['passed'] == True  # Ownership renounced

    @pytest.mark.asyncio
    async def test_token_analysis_error_handling(self, bot_config, mock_solana_client):
        """Test token analysis error handling and recovery."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock all methods to raise exceptions
        with patch.object(analyzer, '_get_token_supply', side_effect=Exception("RPC Error")), \
             patch.object(analyzer, '_get_holder_count', side_effect=Exception("API Error")), \
             patch.object(analyzer, '_get_top_holder_percent', side_effect=Exception("Network Error")), \
             patch.object(analyzer, '_check_contract_verified', side_effect=Exception("Verification Error")), \
             patch.object(analyzer, '_check_ownership_renounced', side_effect=Exception("Ownership Error")):

            token_mint = 'ERROR_TOKEN_123'
            result = await analyzer.check_token_filters(token_mint)

            # Should handle errors gracefully
            assert result['passed'] == False
            assert 'error' in result['supply_check']
            assert 'error' in result['holders_check']
            assert 'error' in result['top_holder_check']
            assert 'error' in result['contract_check']
            assert 'error' in result['ownership_check']

    @pytest.mark.asyncio
    async def test_token_analysis_performance(self, bot_config, mock_solana_client):
        """Test token analysis performance with multiple tokens."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Mock fast responses
        with patch.object(analyzer, '_get_token_supply', return_value=500000000), \
             patch.object(analyzer, '_get_holder_count', return_value=150), \
             patch.object(analyzer, '_get_top_holder_percent', return_value=15.0), \
             patch.object(analyzer, '_check_contract_verified', return_value=True), \
             patch.object(analyzer, '_check_ownership_renounced', return_value=True):

            import time
            start_time = time.time()

            # Analyze multiple tokens
            tokens = [f'TOKEN_{i}' for i in range(10)]
            results = []

            for token in tokens:
                result = await analyzer.check_token_filters(token)
                results.append(result)

            end_time = time.time()
            duration = end_time - start_time

            # Verify all analyses completed
            assert len(results) == 10
            assert all(result['passed'] == True for result in results)

            # Performance check: should complete within reasonable time
            # Allow 5 seconds for 10 analyses (0.5s per token)
            assert duration < 5.0, f"Analysis took too long: {duration}s"

    @pytest.mark.asyncio
    async def test_supply_validation_edge_cases(self, bot_config, mock_solana_client):
        """Test supply validation with edge cases."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        test_cases = [
            (999999999, True, "Just under limit"),
            (1000000000, True, "At limit"),
            (1000000001, False, "Just over limit"),
            (5000000000, False, "Well over limit")
        ]

        for supply, expected_pass, description in test_cases:
            with patch.object(analyzer, '_get_token_supply', return_value=supply), \
                 patch.object(analyzer, '_get_holder_count', return_value=150), \
                 patch.object(analyzer, '_get_top_holder_percent', return_value=15.0), \
                 patch.object(analyzer, '_check_contract_verified', return_value=True), \
                 patch.object(analyzer, '_check_ownership_renounced', return_value=True):

                result = await analyzer.check_token_filters('TEST_TOKEN')
                assert result['supply_check']['passed'] == expected_pass, f"Failed for {description}"

    @pytest.mark.asyncio
    async def test_holder_validation_edge_cases(self, bot_config, mock_solana_client):
        """Test holder validation with edge cases."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        test_cases = [
            (99, False, "Just under minimum"),
            (100, True, "At minimum"),
            (101, True, "Just over minimum"),
            (500, True, "Well over minimum")
        ]

        for holders, expected_pass, description in test_cases:
            with patch.object(analyzer, '_get_token_supply', return_value=500000000), \
                 patch.object(analyzer, '_get_holder_count', return_value=holders), \
                 patch.object(analyzer, '_get_top_holder_percent', return_value=15.0), \
                 patch.object(analyzer, '_check_contract_verified', return_value=True), \
                 patch.object(analyzer, '_check_ownership_renounced', return_value=True):

                result = await analyzer.check_token_filters('TEST_TOKEN')
                assert result['holders_check']['passed'] == expected_pass, f"Failed for {description}"

    @pytest.mark.asyncio
    async def test_concentration_validation_edge_cases(self, bot_config, mock_solana_client):
        """Test top holder concentration validation with edge cases."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        test_cases = [
            (19.9, True, "Just under limit"),
            (20.0, True, "At limit"),
            (20.1, False, "Just over limit"),
            (50.0, False, "Well over limit")
        ]

        for concentration, expected_pass, description in test_cases:
            with patch.object(analyzer, '_get_token_supply', return_value=500000000), \
                 patch.object(analyzer, '_get_holder_count', return_value=150), \
                 patch.object(analyzer, '_get_top_holder_percent', return_value=concentration), \
                 patch.object(analyzer, '_check_contract_verified', return_value=True), \
                 patch.object(analyzer, '_check_ownership_renounced', return_value=True):

                result = await analyzer.check_token_filters('TEST_TOKEN')
                assert result['top_holder_check']['passed'] == expected_pass, f"Failed for {description}"
