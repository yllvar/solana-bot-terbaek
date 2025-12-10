"""
Unit tests for Advanced Holder Analysis functionality
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.solana_bot.security import SecurityAnalyzer


class TestAdvancedHolderAnalysis:
    """Test advanced holder distribution analysis"""

    @pytest.fixture
    def mock_config(self):
        """Create mock config with holder analysis settings"""
        config = MagicMock()
        config.max_top_holder_pct = 20.0
        config.min_holders = 100
        return config

    @pytest.fixture
    def mock_client(self):
        """Create mock RPC client"""
        client = AsyncMock()
        return client

    @pytest.fixture
    def analyzer(self, mock_client, mock_config):
        """Create SecurityAnalyzer instance"""
        return SecurityAnalyzer(mock_client, mock_config)

    @pytest.mark.asyncio
    async def test_holder_analysis_successful_on_chain_data(self, analyzer, mock_client):
        """Test successful holder analysis with real on-chain data"""
        # Mock token mint
        token_mint = MagicMock()

        # Mock supply data
        mock_supply = MagicMock()
        mock_supply.value.amount = 1000000  # 1M total supply
        mock_client.get_token_supply.return_value = mock_supply

        # Mock largest accounts data (top holders)
        mock_accounts = MagicMock()
        mock_accounts.value = [
            MagicMock(amount=200000),  # 20% of supply
            MagicMock(amount=150000),  # 15% of supply
            MagicMock(amount=100000),  # 10% of supply
            MagicMock(amount=50000),   # 5% of supply
            MagicMock(amount=25000),   # 2.5% of supply
        ]
        mock_client.get_token_largest_accounts.return_value = mock_accounts

        result = await analyzer._check_holder_distribution(token_mint)

        assert result['passed'] == False  # Should fail due to high concentration
        assert result['data_source'] == 'on_chain'
        assert result['total_supply'] == 1000000
        assert result['top_holder_percentage'] == 35.0
        assert result['holder_count'] == 10  # 5 accounts * 2 estimation
        assert 'Extreme concentration' in result['message'] or 'High concentration' in result['message']

    @pytest.mark.asyncio
    async def test_holder_analysis_good_distribution(self, analyzer, mock_client):
        """Test holder analysis with good distribution"""
        token_mint = MagicMock()

        # Mock supply
        mock_supply = MagicMock()
        mock_supply.value.amount = 1000000
        mock_client.get_token_supply.return_value = mock_supply

        # Mock well-distributed holders (no single holder > 10%)
        mock_accounts = MagicMock()
        mock_accounts.value = [
            MagicMock(amount=80000),   # 8% of supply
            MagicMock(amount=60000),   # 6% of supply
            MagicMock(amount=50000),   # 5% of supply
            MagicMock(amount=30000),   # 3% of supply
            MagicMock(amount=20000),   # 2% of supply
        ]
        mock_client.get_token_largest_accounts.return_value = mock_accounts

        result = await analyzer._check_holder_distribution(token_mint)

        assert result['passed'] == True
        assert result['top_holder_percentage'] == 8.0
        assert result['concentration_score'] <= 1.0  # All 5 holders are top holders
        assert 'Good distribution' in result['message']

    @pytest.mark.asyncio
    async def test_holder_analysis_extreme_concentration(self, analyzer, mock_client):
        """Test holder analysis with extreme concentration"""
        token_mint = MagicMock()

        # Mock supply
        mock_supply = MagicMock()
        mock_supply.value.amount = 1000000
        mock_client.get_token_supply.return_value = mock_supply

        # Mock extreme concentration (90% in top holder)
        mock_accounts = MagicMock()
        mock_accounts.value = [
            MagicMock(amount=900000),  # 90% of supply
            MagicMock(amount=10000),   # 1% of supply
        ]
        mock_client.get_token_largest_accounts.return_value = mock_accounts

        result = await analyzer._check_holder_distribution(token_mint)

        assert result['passed'] == False
        assert result['top_holder_percentage'] == 90.0
        assert result['concentration_score'] > 0.8  # Extreme concentration
        assert 'High concentration' in result['message']

    @pytest.mark.asyncio
    async def test_holder_analysis_rpc_failure_fallback(self, analyzer, mock_client):
        """Test holder analysis when RPC fails, falls back to estimation"""
        token_mint = MagicMock()

        # Mock RPC failures
        mock_client.get_token_supply.side_effect = Exception("RPC Error")
        mock_client.get_token_largest_accounts.side_effect = Exception("RPC Error")

        # Mock successful mint account parsing
        mock_mint_data = MagicMock()
        mock_mint_data.supply = 500000  # Medium supply
        analyzer._parse_mint_account = AsyncMock(return_value=mock_mint_data)

        result = await analyzer._check_holder_distribution(token_mint)

        assert result['passed'] == True  # Passes with estimation
        assert result['data_source'] == 'estimated'
        assert result['holder_count'] == 50  # Supply 500k < 1M = 50 holders
        assert 'Basic holder estimate' in result['message']

    @pytest.mark.asyncio
    async def test_holder_analysis_empty_accounts(self, analyzer, mock_client):
        """Test holder analysis when no account data is available"""
        token_mint = MagicMock()

        # Mock supply
        mock_supply = MagicMock()
        mock_supply.value.amount = 1000000
        mock_client.get_token_supply.return_value = mock_supply

        # Mock empty accounts
        mock_accounts = MagicMock()
        mock_accounts.value = []
        mock_client.get_token_largest_accounts.return_value = mock_accounts

        result = await analyzer._check_holder_distribution(token_mint)

        assert result['passed'] == False
        assert result['data_source'] == 'failed'
        assert 'Could not analyze' in result['message']

    @pytest.mark.asyncio
    async def test_holder_analysis_concentration_scoring(self, analyzer, mock_client):
        """Test concentration score calculation"""
        token_mint = MagicMock()

        # Mock supply
        mock_supply = MagicMock()
        mock_supply.value.amount = 1000000
        mock_client.get_token_supply.return_value = mock_supply

        # Mock accounts with specific concentration pattern
        mock_accounts = MagicMock()
        mock_accounts.value = [
            MagicMock(amount=500000),  # 50%
            MagicMock(amount=300000),  # 30%
            MagicMock(amount=150000),  # 15%
            MagicMock(amount=50000),   # 5%
        ]
        mock_client.get_token_largest_accounts.return_value = mock_accounts

        result = await analyzer._check_holder_distribution(token_mint)

        # Top 5 concentration: 50% + 30% + 15% + 5% = 100% of top 4
        # But we only have 4 accounts, so concentration should be 1.0
        assert result['concentration_score'] == 1.0
        assert result['passed'] == False  # Too concentrated

    def test_format_holder_message_good_distribution(self, analyzer):
        """Test message formatting for good distribution"""
        message = analyzer._format_holder_message(
            passed=True, top_pct=8.0, concentration=0.4, holder_count=150, max_pct=20.0
        )
        assert "Good distribution" in message
        assert "150 holders" in message

    def test_format_holder_message_high_concentration(self, analyzer):
        """Test message formatting for high concentration"""
        message = analyzer._format_holder_message(
            passed=False, top_pct=35.0, concentration=0.6, holder_count=100, max_pct=20.0
        )
        assert "High concentration" in message
        assert "35.0%" in message

    def test_format_holder_message_extreme_concentration(self, analyzer):
        """Test message formatting for extreme concentration"""
        message = analyzer._format_holder_message(
            passed=False, top_pct=15.0, concentration=0.9, holder_count=50, max_pct=20.0
        )
        assert "Extreme concentration" in message or "High concentration" in message

    @pytest.mark.asyncio
    async def test_integration_with_token_filters(self, analyzer, mock_client):
        """Test that holder analysis integrates properly with token filters"""
        token_mint = "TestToken11111111111111111111111111111111"

        # Mock good holder distribution
        mock_supply = MagicMock()
        mock_supply.value.amount = 1000000
        mock_client.get_token_supply.return_value = mock_supply

        mock_accounts = MagicMock()
        mock_accounts.value = [
            MagicMock(amount=50000),   # 5%
            MagicMock(amount=40000),   # 4%
            MagicMock(amount=30000),   # 3%
        ]
        mock_client.get_token_largest_accounts.return_value = mock_accounts

        # Mock other filter methods to pass - properly mock on analyzer instance
        analyzer._check_token_supply = AsyncMock(return_value={'passed': True, 'message': 'OK'})
        analyzer._check_holder_distribution = AsyncMock(return_value={
            'passed': True, 'message': 'Good distribution', 'data_source': 'on_chain'
        })
        analyzer._check_contract_verification = AsyncMock(return_value={'passed': True, 'message': 'OK'})
        analyzer._check_ownership_renounced = AsyncMock(return_value={'passed': True, 'message': 'OK'})

        result = await analyzer.check_token_filters(token_mint)

        assert 'holders' in result['filters']
        holder_filter = result['filters']['holders']
        assert 'data_source' in holder_filter
        assert 'top_holder_percentage' in holder_filter
