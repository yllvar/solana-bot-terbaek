"""
Birdeye API client for Solana market data and analytics
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class BirdeyeClient:
    """Client for Birdeye Solana market data API"""

    BASE_URL = "https://public-api.birdeye.so"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Birdeye client

        Args:
            api_key: Birdeye API key (optional, some endpoints work without it)
        """
        self.api_key = api_key
        self.client: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        self._last_request_time = 0
        self._rate_limit_delay = 1.0  # 1 second between requests

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0),
            headers={
                "accept": "application/json",
                "x-chain": "solana"
            }
        )
        if self.api_key:
            self.client.headers["X-API-KEY"] = self.api_key

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _rate_limit_wait(self):
        """Implement rate limiting"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - time_since_last)

        self._last_request_time = asyncio.get_event_loop().time()
        self._request_count += 1

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Make API request with error handling"""
        if not self.client:
            raise RuntimeError("Client not started. Call start() first.")

        await self._rate_limit_wait()

        url = f"{self.BASE_URL}{endpoint}"

        try:
            logger.debug(f"🔍 Birdeye API request: {url}")
            response = await self.client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                logger.debug(f"✅ Birdeye API success: {endpoint}")
                return data
            else:
                logger.warning(f"⚠️ Birdeye API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Birdeye API request failed: {e}")
            return None

    async def get_token_overview(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive token overview including price, volume, liquidity

        Args:
            token_address: Solana token mint address

        Returns:
            Token overview data or None if failed
        """
        endpoint = f"/defi/token_overview"
        params = {"address": token_address}

        data = await self._make_request(endpoint, params)
        if data and data.get("success"):
            return data.get("data")
        return None

    async def get_token_price(self, token_address: str) -> Optional[float]:
        """
        Get current token price

        Args:
            token_address: Solana token mint address

        Returns:
            Current price in USD or None if failed
        """
        overview = await self.get_token_overview(token_address)
        if overview and "price" in overview:
            return float(overview["price"])
        return None

    async def get_token_volume_24h(self, token_address: str) -> Optional[float]:
        """
        Get 24-hour trading volume for token

        Args:
            token_address: Solana token mint address

        Returns:
            24h volume in USD or None if failed
        """
        overview = await self.get_token_overview(token_address)
        if overview and "volume24hUSD" in overview:
            return float(overview["volume24hUSD"])
        return None

    async def get_token_liquidity(self, token_address: str) -> Optional[float]:
        """
        Get token liquidity information

        Args:
            token_address: Solana token mint address

        Returns:
            Liquidity in USD or None if failed
        """
        overview = await self.get_token_overview(token_address)
        if overview and "liquidity" in overview:
            return float(overview["liquidity"])
        return None

    async def get_token_market_cap(self, token_address: str) -> Optional[float]:
        """
        Get token market capitalization

        Args:
            token_address: Solana token mint address

        Returns:
            Market cap in USD or None if failed
        """
        overview = await self.get_token_overview(token_address)
        if overview and "mc" in overview:
            return float(overview["mc"])
        return None

    async def get_token_supply_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token supply information

        Args:
            token_address: Solana token mint address

        Returns:
            Supply info dict or None if failed
        """
        overview = await self.get_token_overview(token_address)
        if overview:
            return {
                "total_supply": overview.get("supply"),
                "circulating_supply": overview.get("circulatingSupply"),
                "max_supply": overview.get("maxSupply")
            }
        return None

    async def get_price_history(self, token_address: str, timeframe: str = "1D") -> Optional[List[Dict[str, Any]]]:
        """
        Get token price history

        Args:
            token_address: Solana token mint address
            timeframe: Timeframe (1m, 5m, 1H, 1D, etc.)

        Returns:
            List of price data points or None if failed
        """
        endpoint = f"/defi/history_price"
        params = {
            "address": token_address,
            "chain": "solana",
            "type": timeframe
        }

        data = await self._make_request(endpoint, params)
        if data and data.get("success"):
            return data.get("data", {}).get("items", [])
        return None

    async def search_pairs(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Search for trading pairs

        Args:
            query: Search query (token symbol, name, or address)

        Returns:
            List of matching pairs or None if failed
        """
        endpoint = "/defi/v3/search"
        params = {"chain": "solana", "keyword": query}

        data = await self._make_request(endpoint, params)
        if data and data.get("success"):
            return data.get("data", [])
        return None

    async def get_pair_overview(self, pair_address: str) -> Optional[Dict[str, Any]]:
        """
        Get trading pair overview

        Args:
            pair_address: AMM pair address

        Returns:
            Pair overview data or None if failed
        """
        endpoint = f"/defi/pair_overview"
        params = {"address": pair_address}

        data = await self._make_request(endpoint, params)
        if data and data.get("success"):
            return data.get("data")
        return None

    async def is_token_valid(self, token_address: str) -> bool:
        """
        Check if token exists and is valid

        Args:
            token_address: Solana token mint address

        Returns:
            True if token is valid and exists
        """
        overview = await self.get_token_overview(token_address)
        return overview is not None

    async def get_bulk_token_info(self, token_addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get information for multiple tokens at once

        Args:
            token_addresses: List of token addresses

        Returns:
            Dict mapping addresses to token info
        """
        results = {}
        for address in token_addresses:
            info = await self.get_token_overview(address)
            if info:
                results[address] = info
            await asyncio.sleep(0.1)  # Small delay between requests

        return results
