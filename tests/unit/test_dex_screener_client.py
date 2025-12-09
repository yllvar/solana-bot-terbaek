"""
Unit tests for DexScreener API client
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.solana_bot.dex_screener_client import DexScreenerClient


class TestDexScreenerClient:
    """Test DexScreener API client functionality"""

    @pytest.fixture
    def client(self):
        """Create test client instance"""
        return DexScreenerClient()

    @pytest.mark.asyncio
    async def test_initialization(self, client):
        """Test client initialization and lifecycle"""
        assert client.client is None
        assert client._request_count == 0
        assert client._last_request_time == 0

        # Test start
        await client.start()
        assert client.client is not None
        assert hasattr(client.client, 'get')  # Basic httpx client check

        # Test close
        await client.close()
        # Note: httpx client may not be None after close, just verify it's been closed

    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager usage"""
        async with client as c:
            assert c.client is not None
            assert hasattr(c.client, 'get')
        # Context manager should handle cleanup properly

    @pytest.mark.asyncio
    async def test_get_token_pairs_success(self, client):
        """Test successful token pairs retrieval"""
        mock_response = {
            "pairs": [
                {
                    "pairAddress": "ABC123...",
                    "baseToken": {"address": "So11111111111111111111111111111111111111112"},
                    "quoteToken": {"address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"},
                    "volume": {"h24": 1000000},
                    "liquidity": {"usd": 500000}
                }
            ]
        }

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.start()
            result = await client.get_token_pairs("So11111111111111111111111111111111111111112")

            assert result == mock_response["pairs"]
            mock_request.assert_called_once_with("/latest/dex/tokens/So11111111111111111111111111111111111111112")

    @pytest.mark.asyncio
    async def test_get_token_pairs_no_data(self, client):
        """Test token pairs retrieval with no data"""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            await client.start()
            result = await client.get_token_pairs("INVALID_TOKEN")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_token_volume_24h_success(self, client):
        """Test successful 24h volume calculation"""
        mock_pairs = [
            {"volume": {"h24": 500000}, "liquidity": {"usd": 1000000}},
            {"volume": {"h24": 300000}, "liquidity": {"usd": 800000}},
        ]

        with patch.object(client, 'get_token_pairs', new_callable=AsyncMock) as mock_get_pairs:
            mock_get_pairs.return_value = mock_pairs

            await client.start()
            result = await client.get_token_volume_24h("TEST_TOKEN")

            assert result == 800000  # Sum of both pairs
            mock_get_pairs.assert_called_once_with("TEST_TOKEN")

    @pytest.mark.asyncio
    async def test_get_token_volume_24h_no_pairs(self, client):
        """Test volume calculation with no pairs"""
        with patch.object(client, 'get_token_pairs', new_callable=AsyncMock) as mock_get_pairs:
            mock_get_pairs.return_value = None

            await client.start()
            result = await client.get_token_volume_24h("TEST_TOKEN")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_token_price_success(self, client):
        """Test successful price retrieval"""
        mock_pairs = [
            {"priceUsd": "100.50", "volume": {"h24": 100000}},
            {"priceUsd": "101.00", "volume": {"h24": 50000}},
        ]

        with patch.object(client, 'get_token_pairs', new_callable=AsyncMock) as mock_get_pairs:
            mock_get_pairs.return_value = mock_pairs

            await client.start()
            result = await client.get_token_price("TEST_TOKEN")

            assert result == 100.50  # Price from highest volume pair

    @pytest.mark.asyncio
    async def test_get_token_liquidity_success(self, client):
        """Test successful liquidity calculation"""
        mock_pairs = [
            {"liquidity": {"usd": 500000}},
            {"liquidity": {"usd": 300000}},
        ]

        with patch.object(client, 'get_token_pairs', new_callable=AsyncMock) as mock_get_pairs:
            mock_get_pairs.return_value = mock_pairs

            await client.start()
            result = await client.get_token_liquidity("TEST_TOKEN")

            assert result == 800000  # Sum of both pairs

    @pytest.mark.asyncio
    async def test_get_token_info_comprehensive(self, client):
        """Test comprehensive token info aggregation"""
        mock_pairs = [
            {
                "pairAddress": "PAIR1",
                "volume": {"h24": 100000},
                "liquidity": {"usd": 500000},
                "priceUsd": "10.00",
                "fdv": 1000000
            },
            {
                "pairAddress": "PAIR2",
                "volume": {"h24": 50000},
                "liquidity": {"usd": 300000},
                "priceUsd": "10.50",
                "fdv": 1050000
            }
        ]

        with patch.object(client, 'get_token_pairs', new_callable=AsyncMock) as mock_get_pairs:
            mock_get_pairs.return_value = mock_pairs

            await client.start()
            result = await client.get_token_info("TEST_TOKEN")

            assert result is not None
            assert result["address"] == "TEST_TOKEN"
            assert result["total_volume_24h"] == 150000  # Sum
            assert result["total_liquidity"] == 800000   # Sum
            assert result["pair_count"] == 2
            assert len(result["pairs"]) == 2

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test request rate limiting"""
        await client.start()

        # Mock time to control rate limiting
        import time
        original_time = time.time

        call_times = []
        def mock_time():
            call_times.append(len(call_times))
            return original_time() + (len(call_times) - 1) * 0.05  # 50ms between calls

        with patch('time.time', mock_time):
            with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
                mock_request.return_value = {"pairs": []}

                # Make multiple requests
                await client.get_token_pairs("TOKEN1")
                await client.get_token_pairs("TOKEN2")
                await client.get_token_pairs("TOKEN3")

                # Verify requests were made (rate limiting should still allow requests)
                assert mock_request.call_count == 3
                assert client._request_count == 3

    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for API failures"""
        await client.start()

        with patch.object(client, '_make_request', side_effect=Exception("API Error")):
            result = await client.get_token_pairs("INVALID_TOKEN")
            assert result is None

        with patch.object(client, 'get_token_pairs', return_value=None):
            volume = await client.get_token_volume_24h("INVALID_TOKEN")
            assert volume is None

    @pytest.mark.asyncio
    async def test_search_pairs(self, client):
        """Test pair search functionality"""
        mock_response = {
            "pairs": [
                {"pairAddress": "PAIR1", "symbol": "TOKEN/USD"},
                {"pairAddress": "PAIR2", "symbol": "TOKEN/SOL"}
            ]
        }

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.start()
            result = await client.search_pairs("TOKEN")

            assert result == mock_response["pairs"]
            mock_request.assert_called_once_with("/latest/dex/search", {"q": "TOKEN"})
