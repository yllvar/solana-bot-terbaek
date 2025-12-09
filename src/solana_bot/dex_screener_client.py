"""
DexScreener API client for Solana DEX data and trading analytics
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class DexScreenerClient:
    """Client for DexScreener Solana DEX data API"""

    BASE_URL = "https://api.dexscreener.com"

    def __init__(self):
        """
        Initialize DexScreener client
        DexScreener is free and doesn't require API keys
        """
        self.client: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        self._last_request_time = 0
        self._rate_limit_delay = 0.1  # 10 requests per second max

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
                "User-Agent": "Solana-Bot/1.0"
            }
        )

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with rate limiting

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            JSON response data or None if failed
        """
        if not self.client:
            logger.error("DexScreener client not initialized")
            return None

        try:
            # Rate limiting
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._rate_limit_delay:
                await asyncio.sleep(self._rate_limit_delay - time_since_last)

            self._request_count += 1
            self._last_request_time = current_time

            url = f"{self.BASE_URL}{endpoint}"
            logger.debug(f"🔍 DexScreener API call: {url}")

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"✅ DexScreener response received")
            return data

        except httpx.HTTPStatusError as e:
            logger.warning(f"⚠️ DexScreener API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"❌ DexScreener request failed: {e}")
            return None

    async def get_token_pairs(self, token_address: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get all trading pairs for a token

        Args:
            token_address: Solana token mint address

        Returns:
            List of trading pairs or None if failed
        """
        endpoint = f"/latest/dex/tokens/{token_address}"
        data = await self._make_request(endpoint)

        if data and "pairs" in data:
            pairs = data["pairs"]
            logger.debug(f"📊 Found {len(pairs)} pairs for {token_address[:8]}...")
            return pairs
        return None

    async def get_pair_info(self, pair_address: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific trading pair

        Args:
            pair_address: DEX pair address

        Returns:
            Pair information or None if failed
        """
        endpoint = f"/latest/dex/pairs/solana/{pair_address}"
        data = await self._make_request(endpoint)

        if data and "pair" in data:
            return data["pair"]
        return None

    async def get_token_volume_24h(self, token_address: str) -> Optional[float]:
        """
        Get 24-hour trading volume for a token from DexScreener

        Args:
            token_address: Solana token mint address

        Returns:
            24h volume in USD or None if failed
        """
        try:
            pairs = await self.get_token_pairs(token_address)
            if not pairs:
                logger.debug(f"ℹ️ No pairs found for {token_address[:8]}...")
                return None

            # Sum volume across all pairs for this token
            total_volume = 0.0
            pair_count = 0

            for pair in pairs:
                volume_24h = pair.get("volume", {}).get("h24", 0)
                if volume_24h and volume_24h > 0:
                    total_volume += volume_24h
                    pair_count += 1

            if pair_count > 0:
                logger.debug(f"📊 DexScreener volume for {token_address[:8]}...: ${total_volume:,.0f} ({pair_count} pairs)")
                return total_volume
            else:
                logger.debug(f"ℹ️ No volume data found for {token_address[:8]}...")
                return None

        except Exception as e:
            logger.error(f"❌ Error getting DexScreener volume for {token_address}: {e}")
            return None

    async def get_token_price(self, token_address: str) -> Optional[float]:
        """
        Get current token price from DexScreener

        Args:
            token_address: Solana token mint address

        Returns:
            Current price in USD or None if failed
        """
        try:
            pairs = await self.get_token_pairs(token_address)
            if not pairs:
                return None

            # Get price from the highest volume pair
            best_pair = None
            max_volume = 0

            for pair in pairs:
                volume_24h = pair.get("volume", {}).get("h24", 0)
                if volume_24h > max_volume:
                    max_volume = volume_24h
                    best_pair = pair

            if best_pair and "priceUsd" in best_pair:
                price = float(best_pair["priceUsd"])
                logger.debug(f"💰 DexScreener price for {token_address[:8]}...: ${price:.6f}")
                return price

            return None

        except Exception as e:
            logger.error(f"❌ Error getting DexScreener price for {token_address}: {e}")
            return None

    async def get_token_liquidity(self, token_address: str) -> Optional[float]:
        """
        Get token liquidity from DexScreener

        Args:
            token_address: Solana token mint address

        Returns:
            Total liquidity in USD or None if failed
        """
        try:
            pairs = await self.get_token_pairs(token_address)
            if not pairs:
                return None

            # Sum liquidity across all pairs
            total_liquidity = 0.0
            pair_count = 0

            for pair in pairs:
                liquidity = pair.get("liquidity", {}).get("usd", 0)
                if liquidity and liquidity > 0:
                    total_liquidity += liquidity
                    pair_count += 1

            if pair_count > 0:
                logger.debug(f"💧 DexScreener liquidity for {token_address[:8]}...: ${total_liquidity:,.0f}")
                return total_liquidity

            return None

        except Exception as e:
            logger.error(f"❌ Error getting DexScreener liquidity for {token_address}: {e}")
            return None

    async def search_pairs(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Search for trading pairs

        Args:
            query: Search query (token symbol, name, or address)

        Returns:
            List of matching pairs or None if failed
        """
        endpoint = "/latest/dex/search"
        params = {"q": query}

        data = await self._make_request(endpoint, params)
        if data and "pairs" in data:
            return data["pairs"]
        return None

    async def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive token information from DexScreener

        Args:
            token_address: Solana token mint address

        Returns:
            Token info dict or None if failed
        """
        try:
            pairs = await self.get_token_pairs(token_address)
            if not pairs:
                return None

            # Aggregate data from all pairs
            token_info = {
                "address": token_address,
                "total_volume_24h": 0.0,
                "total_liquidity": 0.0,
                "pair_count": len(pairs),
                "pairs": pairs[:5],  # Top 5 pairs for analysis
                "price_usd": None,
                "market_cap": None
            }

            for pair in pairs:
                # Volume
                volume_24h = pair.get("volume", {}).get("h24", 0)
                if volume_24h:
                    token_info["total_volume_24h"] += volume_24h

                # Liquidity
                liquidity = pair.get("liquidity", {}).get("usd", 0)
                if liquidity:
                    token_info["total_liquidity"] += liquidity

                # Price (from highest volume pair)
                if not token_info["price_usd"] and pair.get("priceUsd"):
                    token_info["price_usd"] = float(pair["priceUsd"])

                # Market cap
                if not token_info["market_cap"] and pair.get("fdv"):
                    token_info["market_cap"] = float(pair["fdv"])

            logger.debug(f"📊 DexScreener token info for {token_address[:8]}...: {token_info['pair_count']} pairs")
            return token_info

        except Exception as e:
            logger.error(f"❌ Error getting DexScreener token info for {token_address}: {e}")
            return None
