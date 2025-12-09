"""
Unit tests for Birdeye client price history and volatility features
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.solana_bot.birdeye_client import BirdeyeClient


class TestBirdeyePriceHistory:
    """Test Birdeye price history and volatility functionality"""

    @pytest.fixture
    def client(self):
        """Create test client instance"""
        return BirdeyeClient("test_api_key")

    @pytest.mark.asyncio
    async def test_get_price_history_success(self, client):
        """Test successful price history retrieval"""
        mock_data = {
            "success": True,
            "data": {
                "items": [
                    {"unixTime": 1640995200, "value": 100.5},
                    {"unixTime": 1640995260, "value": 101.0},
                    {"unixTime": 1640995320, "value": 100.8}
                ]
            }
        }

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_data

            await client.start()
            result = await client.get_price_history("TEST_TOKEN", "1m", 3)

            assert result == mock_data["data"]["items"]
            mock_request.assert_called_once_with(
                "/defi/history_price",
                {
                    "address": "TEST_TOKEN",
                    "chain": "solana",
                    "type": "1m",
                    "limit": 3
                }
            )

    @pytest.mark.asyncio
    async def test_get_price_history_no_data(self, client):
        """Test price history with no data"""
        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"success": False}

            await client.start()
            result = await client.get_price_history("TEST_TOKEN")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_price_change_24h_success(self, client):
        """Test successful 24h price change calculation"""
        # Mock 25 data points (24 hours + current)
        price_data = []
        base_time = 1640995200  # Start time
        base_price = 100.0

        for i in range(25):
            # Simulate slight price movement
            price = base_price + (i * 0.1)  # Gradual increase
            price_data.append({"unixTime": base_time + (i * 3600), "value": price})

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = price_data

            await client.start()
            result = await client.get_price_change_24h("TEST_TOKEN")

            # Expected: (124.0 - 100.0) / 100.0 * 100 = 24.0%
            expected_change = 24.0
            assert abs(result - expected_change) < 0.1

    @pytest.mark.asyncio
    async def test_get_price_change_24h_insufficient_data(self, client):
        """Test price change with insufficient data"""
        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = [{"unixTime": 1234567890, "value": 100.0}]  # Only 1 point

            await client.start()
            result = await client.get_price_change_24h("TEST_TOKEN")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_price_change_24h_price_decrease(self, client):
        """Test price change with price decrease"""
        price_data = [
            {"unixTime": 1640995200, "value": 100.0},  # 24h ago
            {"unixTime": 1641081600, "value": 95.0}    # Current (5% decrease)
        ]

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = price_data

            await client.start()
            result = await client.get_price_change_24h("TEST_TOKEN")

            assert result == -5.0  # 5% decrease

    @pytest.mark.asyncio
    async def test_calculate_volatility_stable_prices(self, client):
        """Test volatility calculation with stable prices"""
        # Generate stable prices with minimal variation
        prices = [{"unixTime": 1640995200 + i, "value": 100.0 + (i * 0.01)} for i in range(25)]

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = prices

            await client.start()
            result = await client.calculate_volatility("TEST_TOKEN", "1m", 24)

            # Should be very low volatility
            assert result is not None
            assert result < 0.01  # Less than 1%

    @pytest.mark.asyncio
    async def test_calculate_volatility_volatile_prices(self, client):
        """Test volatility calculation with volatile prices"""
        # Generate volatile prices
        import math
        prices = []
        for i in range(25):
            # Sine wave with increasing amplitude (volatility)
            value = 100.0 + 10 * math.sin(i * 0.5) * (i / 24)  # Increasing volatility
            prices.append({"unixTime": 1640995200 + i, "value": value})

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = prices

            await client.start()
            result = await client.calculate_volatility("TEST_TOKEN", "1m", 24)

            # Should be higher volatility
            assert result is not None
            assert result > 0.1  # More than 10%

    @pytest.mark.asyncio
    async def test_calculate_volatility_insufficient_data(self, client):
        """Test volatility with insufficient data"""
        prices = [
            {"unixTime": 1640995200, "value": 100.0},
            {"unixTime": 1640995201, "value": 100.5}  # Only 2 points
        ]

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = prices

            await client.start()
            result = await client.calculate_volatility("TEST_TOKEN", "1m", 24)

            assert result is None

    @pytest.mark.asyncio
    async def test_calculate_volatility_no_variation(self, client):
        """Test volatility with no price variation"""
        prices = [{"unixTime": 1640995200 + i, "value": 100.0} for i in range(25)]  # Constant price

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = prices

            await client.start()
            result = await client.calculate_volatility("TEST_TOKEN", "1m", 24)

            # Should be 0 or very close to 0
            assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculate_volatility_extreme_volatility(self, client):
        """Test volatility calculation with extreme price swings"""
        prices = []
        for i in range(25):
            # Extreme swings: alternate between high and low
            value = 100.0 + (50.0 if i % 2 == 0 else -50.0)
            prices.append({"unixTime": 1640995200 + i, "value": value})

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = prices

            await client.start()
            result = await client.calculate_volatility("TEST_TOKEN", "1m", 24)

            # Should be very high volatility, capped at 1.0
            assert result == 1.0

    @pytest.mark.asyncio
    async def test_calculate_volatility_different_timeframes(self, client):
        """Test volatility calculation with different timeframes"""
        prices = [{"unixTime": 1640995200 + i * 3600, "value": 100.0 + i} for i in range(25)]

        with patch.object(client, 'get_price_history', new_callable=AsyncMock) as mock_history:
            mock_history.return_value = prices

            await client.start()

            # Test different timeframes
            result_1h = await client.calculate_volatility("TEST_TOKEN", "1H", 24)
            result_1d = await client.calculate_volatility("TEST_TOKEN", "1D", 24)

            assert result_1h is not None
            assert result_1d is not None
            # Different timeframes may give different results

    @pytest.mark.asyncio
    async def test_error_handling_price_history(self, client):
        """Test error handling in price history methods"""
        await client.start()

        # Test get_price_history error
        with patch.object(client, '_make_request', side_effect=Exception("API Error")):
            result = await client.get_price_history("TEST_TOKEN")
            assert result is None

        # Test get_price_change_24h with history error
        with patch.object(client, 'get_price_history', side_effect=Exception("History Error")):
            result = await client.get_price_change_24h("TEST_TOKEN")
            assert result is None

        # Test calculate_volatility with history error
        with patch.object(client, 'get_price_history', side_effect=Exception("History Error")):
            result = await client.calculate_volatility("TEST_TOKEN")
            assert result is None

    @pytest.mark.asyncio
    async def test_price_history_parameters(self, client):
        """Test price history with different parameters"""
        mock_data = {
            "success": True,
            "data": {"items": [{"unixTime": 1234567890, "value": 100.0}]}
        }

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_data

            await client.start()

            # Test default parameters
            result1 = await client.get_price_history("TOKEN1")
            assert result1 == mock_data["data"]["items"]

            # Test custom parameters
            result2 = await client.get_price_history("TOKEN2", "5m", 50)
            assert result2 == mock_data["data"]["items"]

            # Verify correct parameters were passed
            assert mock_request.call_count == 2
            calls = mock_request.call_args_list

            # First call (defaults)
            assert calls[0][1]["params"]["type"] == "1D"
            assert calls[0][1]["params"]["limit"] == 24

            # Second call (custom)
            assert calls[1][1]["params"]["type"] == "5m"
            assert calls[1][1]["params"]["limit"] == 50
