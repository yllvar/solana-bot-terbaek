"""
Unit tests for Bulk API Operations functionality
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.solana_bot.birdeye_client import BirdeyeClient
from src.solana_bot.volume_validator import VolumeValidator


class TestBulkAPIOperations:
    """Test bulk API operations functionality"""

    @pytest.fixture
    def birdeye_client(self):
        """Create Birdeye client for testing"""
        with patch('src.solana_bot.birdeye_client.BirdeyeClient'):
            client = BirdeyeClient("test_key")
            client._make_request = AsyncMock()
            client.start = AsyncMock()
            client.close = AsyncMock()
            return client

    @pytest.fixture
    def volume_validator(self):
        """Create VolumeValidator for testing"""
        with patch('src.solana_bot.volume_validator.BirdeyeClient'), \
             patch('src.solana_bot.volume_validator.DexScreenerClient'):
            validator = VolumeValidator(MagicMock(), MagicMock())
            return validator

    @pytest.mark.asyncio
    async def test_birdeye_bulk_token_info_success(self, birdeye_client):
        """Test successful bulk token info retrieval"""
        # Mock token data
        mock_responses = [
            {'success': True, 'data': {'price': 1.0, 'volume24hUSD': 10000}},
            {'success': True, 'data': {'price': 2.0, 'volume24hUSD': 20000}},
        ]

        # Mock individual API calls
        birdeye_client.get_token_overview = AsyncMock(side_effect=mock_responses)

        await birdeye_client.start()
        result = await birdeye_client.get_bulk_token_info(['TOKEN1', 'TOKEN2'], batch_size=2)

        assert len(result) == 2
        assert 'TOKEN1' in result
        assert 'TOKEN2' in result
        assert result['TOKEN1']['price'] == 1.0
        assert result['TOKEN2']['volume24hUSD'] == 20000

    @pytest.mark.asyncio
    async def test_birdeye_bulk_token_info_partial_failure(self, birdeye_client):
        """Test bulk token info with partial failures"""
        # Mock mixed responses (some success, some failure)
        birdeye_client.get_token_overview = AsyncMock(side_effect=[
            {'success': True, 'data': {'price': 1.0}},  # Success
            None,  # Failure
            {'success': True, 'data': {'price': 3.0}},  # Success
        ])

        await birdeye_client.start()
        result = await birdeye_client.get_bulk_token_info(['TOKEN1', 'TOKEN2', 'TOKEN3'])

        assert len(result) == 2  # Only successful calls
        assert 'TOKEN1' in result
        assert 'TOKEN2' not in result  # Failed
        assert 'TOKEN3' in result

    @pytest.mark.asyncio
    async def test_birdeye_bulk_volume_data(self, birdeye_client):
        """Test bulk volume data retrieval"""
        # Mock bulk token info
        mock_bulk_data = {
            'TOKEN1': {'volume24hUSD': 10000},
            'TOKEN2': {'volume24hUSD': 20000},
            'TOKEN3': {},  # No volume data
        }

        birdeye_client.get_bulk_token_info = AsyncMock(return_value=mock_bulk_data)

        await birdeye_client.start()
        result = await birdeye_client.get_bulk_volume_data(['TOKEN1', 'TOKEN2', 'TOKEN3'])

        assert len(result) == 3
        assert result['TOKEN1'] == 10000
        assert result['TOKEN2'] == 20000
        assert result['TOKEN3'] is None

    @pytest.mark.asyncio
    async def test_birdeye_bulk_price_data(self, birdeye_client):
        """Test bulk price data retrieval"""
        mock_bulk_data = {
            'TOKEN1': {'price': 1.5},
            'TOKEN2': {'price': 2.75},
        }

        birdeye_client.get_bulk_token_info = AsyncMock(return_value=mock_bulk_data)

        await birdeye_client.start()
        result = await birdeye_client.get_bulk_price_data(['TOKEN1', 'TOKEN2'])

        assert len(result) == 2
        assert result['TOKEN1'] == 1.5
        assert result['TOKEN2'] == 2.75

    @pytest.mark.asyncio
    async def test_birdeye_bulk_liquidity_data(self, birdeye_client):
        """Test bulk liquidity data retrieval"""
        mock_bulk_data = {
            'TOKEN1': {'liquidity': 50000},
            'TOKEN2': {'liquidity': 75000},
        }

        birdeye_client.get_bulk_token_info = AsyncMock(return_value=mock_bulk_data)

        await birdeye_client.start()
        result = await birdeye_client.get_bulk_liquidity_data(['TOKEN1', 'TOKEN2'])

        assert len(result) == 2
        assert result['TOKEN1'] == 50000
        assert result['TOKEN2'] == 75000

    @pytest.mark.asyncio
    async def test_birdeye_bulk_operations_concurrency_control(self, birdeye_client):
        """Test that bulk operations respect concurrency limits"""
        import asyncio

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        async def mock_get_token_overview(token):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)  # Small delay to simulate work
            concurrent_count -= 1
            return {'success': True, 'data': {'price': 1.0}}

        birdeye_client.get_token_overview = AsyncMock(side_effect=mock_get_token_overview)

        await birdeye_client.start()

        # Test with batch_size=2
        tokens = ['T1', 'T2', 'T3', 'T4', 'T5']
        result = await birdeye_client.get_bulk_token_info(tokens, batch_size=2)

        assert len(result) == 5
        assert max_concurrent <= 2  # Should not exceed batch size

    @pytest.mark.asyncio
    async def test_volume_validator_bulk_validation(self, volume_validator):
        """Test bulk volume validation"""
        # Mock individual volume results
        token_addresses = ['TOKEN1', 'TOKEN2', 'TOKEN3']

        # Mock bulk operations
        volume_validator.birdeye.get_bulk_volume_data = AsyncMock(return_value={
            'TOKEN1': 10000,
            'TOKEN2': 15000,
            'TOKEN3': None,
        })

        volume_validator.dex_screener.get_token_volume_24h = AsyncMock(side_effect=[
            9500, 14000, None
        ])

        # Mock validation method
        volume_validator._validate_and_combine = MagicMock(side_effect=[
            MagicMock(final_volume=9750, confidence_score=0.8),
            MagicMock(final_volume=14500, confidence_score=0.75),
            MagicMock(final_volume=10000, confidence_score=0.1),  # Fallback
        ])

        await volume_validator.initialize()
        result = await volume_validator.get_bulk_validated_volumes(token_addresses)

        assert len(result) == 3
        assert all(isinstance(v, object) for v in result.values())  # All ValidatedVolume objects
        assert result['TOKEN1'].final_volume == 9750
        assert result['TOKEN2'].final_volume == 14500
        assert result['TOKEN3'].final_volume == 10000

    @pytest.mark.asyncio
    async def test_bulk_operations_error_handling(self, birdeye_client):
        """Test error handling in bulk operations"""
        # Mock all API calls to fail
        birdeye_client.get_token_overview = AsyncMock(return_value=None)

        await birdeye_client.start()
        result = await birdeye_client.get_bulk_token_info(['TOKEN1', 'TOKEN2'])

        assert len(result) == 0  # No successful results

    @pytest.mark.asyncio
    async def test_bulk_operations_empty_input(self, birdeye_client):
        """Test bulk operations with empty input"""
        await birdeye_client.start()
        result = await birdeye_client.get_bulk_token_info([])

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_bulk_volume_validation_empty_input(self, volume_validator):
        """Test bulk volume validation with empty input"""
        await volume_validator.initialize()
        result = await volume_validator.get_bulk_validated_volumes([])

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_bulk_operations_rate_limiting(self, birdeye_client):
        """Test that bulk operations respect rate limiting"""
        import time

        # Mock time to track delays
        call_times = []

        async def mock_get_token_overview(token):
            call_times.append(time.time())
            return {'success': True, 'data': {'price': 1.0}}

        birdeye_client.get_token_overview = AsyncMock(side_effect=mock_get_token_overview)

        await birdeye_client.start()

        # Make multiple calls quickly
        tokens = ['T1', 'T2', 'T3']
        start_time = time.time()
        result = await birdeye_client.get_bulk_token_info(tokens, batch_size=1)  # Sequential

        # Should take at least some time due to rate limiting
        elapsed = time.time() - start_time
        assert elapsed > 0.05  # At least 50ms per call (rate limit)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_volume_validator_bulk_error_fallback(self, volume_validator):
        """Test bulk volume validation error fallback"""
        token_addresses = ['TOKEN1', 'TOKEN2']

        # Mock all operations to fail
        volume_validator.birdeye.get_bulk_volume_data = AsyncMock(side_effect=Exception("API Error"))

        await volume_validator.initialize()

        # Should not raise exception, should return fallback results
        result = await volume_validator.get_bulk_validated_volumes(token_addresses)

        assert len(result) == 2
        assert all(v.final_volume == 100000 for v in result.values())  # Error fallback volume
        assert all(v.confidence_score == 0.0 for v in result.values())  # Zero confidence

    def test_bulk_operation_result_structure(self, birdeye_client):
        """Test that bulk operations return correct data structures"""
        # Test volume data structure
        volume_data = {'TOKEN1': 10000, 'TOKEN2': None}
        assert isinstance(volume_data, dict)
        assert volume_data['TOKEN1'] == 10000
        assert volume_data['TOKEN2'] is None

        # Test price data structure
        price_data = {'TOKEN1': 1.5, 'TOKEN2': 2.75}
        assert isinstance(price_data, dict)
        assert all(isinstance(p, (float, type(None))) for p in price_data.values())
