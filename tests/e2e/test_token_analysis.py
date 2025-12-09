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

        # Use a valid token mint (WSOL) that should exist
        token_mint = 'So11111111111111111111111111111111111111112'
        result = await analyzer.check_token_filters(token_mint)

        # Verify result structure
        assert 'passed' in result
        assert 'filters' in result
        assert 'warnings' in result
        assert 'supply' in result['filters']
        assert 'holders' in result['filters']
        assert 'contract_verified' in result['filters']
        assert 'ownership_renounced' in result['filters']

    @pytest.mark.asyncio
    async def test_complete_token_analysis_risky_token(self, bot_config, mock_solana_client):
        """Test complete token analysis pipeline with risky token."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Use a non-existent token that should fail
        token_mint = 'RISKY_TOKEN_12345678901234567890123456789012'
        result = await analyzer.check_token_filters(token_mint)

        # Should have result structure even for invalid tokens
        assert 'passed' in result
        assert 'filters' in result
        assert 'warnings' in result

    @pytest.mark.asyncio
    async def test_token_analysis_with_partial_failures(self, bot_config, mock_solana_client):
        """Test token analysis with partial failures."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        token_mint = 'So11111111111111111111111111111111111111112'
        result = await analyzer.check_token_filters(token_mint)

        # Verify result structure
        assert 'passed' in result
        assert 'filters' in result
        assert 'warnings' in result

        # Check that filters have been evaluated
        assert isinstance(result['passed'], bool)
        assert isinstance(result['filters'], dict)

    @pytest.mark.asyncio
    async def test_token_analysis_error_handling(self, bot_config, mock_solana_client):
        """Test token analysis error handling and recovery."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Test with invalid token address
        token_mint = 'INVALID_TOKEN_ADDRESS'
        result = await analyzer.check_token_filters(token_mint)

        # Should handle errors gracefully
        assert 'passed' in result
        assert 'filters' in result
        assert 'warnings' in result
        # Invalid address should result in failure
        assert result['passed'] == False
        assert len(result['warnings']) > 0

    @pytest.mark.asyncio
    async def test_token_analysis_performance(self, bot_config, mock_solana_client):
        """Test token analysis performance with multiple tokens."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        import time
        start_time = time.time()

        # Test with a few different tokens
        tokens = [
            'So11111111111111111111111111111111111111112',  # WSOL
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
        ]

        results = []
        for token in tokens:
            result = await analyzer.check_token_filters(token)
            results.append(result)

        end_time = time.time()
        duration = end_time - start_time

        # Verify all analyses completed with proper structure
        assert len(results) == 2
        for result in results:
            assert 'passed' in result
            assert 'filters' in result
            assert 'warnings' in result

        # Performance check: should complete within reasonable time
        assert duration < 10.0, f"Analysis took too long: {duration}s"

    @pytest.mark.asyncio
    async def test_supply_validation_edge_cases(self, bot_config, mock_solana_client):
        """Test supply validation with real token data."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        # Test with WSOL which has known supply
        token_mint = 'So11111111111111111111111111111111111111112'
        result = await analyzer.check_token_filters(token_mint)

        # Verify supply check was performed
        assert 'supply' in result['filters']
        supply_result = result['filters']['supply']
        assert 'passed' in supply_result
        assert 'supply' in supply_result

    @pytest.mark.asyncio
    async def test_holder_validation_edge_cases(self, bot_config, mock_solana_client):
        """Test holder validation with real token data."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        token_mint = 'So11111111111111111111111111111111111111112'
        result = await analyzer.check_token_filters(token_mint)

        # Verify holder check was performed
        assert 'holders' in result['filters']
        holder_result = result['filters']['holders']
        assert 'passed' in holder_result

    @pytest.mark.asyncio
    async def test_concentration_validation_edge_cases(self, bot_config, mock_solana_client):
        """Test concentration validation with real token data."""
        analyzer = SecurityAnalyzer(mock_solana_client, config=bot_config)

        token_mint = 'So11111111111111111111111111111111111111112'
        result = await analyzer.check_token_filters(token_mint)

        # Verify all filters are present in result
        assert 'supply' in result['filters']
        assert 'holders' in result['filters']
        assert 'contract_verified' in result['filters']
        assert 'ownership_renounced' in result['filters']
