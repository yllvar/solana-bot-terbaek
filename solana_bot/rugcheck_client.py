"""
RugCheck API Client - Token security analysis integration.

Provides programmatic access to RugCheck.xyz API for:
- Token risk scoring
- Mint/freeze authority verification  
- LP lock status checks
- Top holder analysis
"""
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Token risk classification"""
    GOOD = "Good"
    CAUTION = "Caution"
    DANGER = "Danger"
    UNKNOWN = "Unknown"


@dataclass
class TokenRisk:
    """Individual risk indicator"""
    name: str
    value: str
    description: str
    score: int  # Risk contribution (0-100)
    level: RiskLevel


@dataclass
class LPLocker:
    """LP token locker information"""
    locker_name: str
    locker_address: str
    locked_amount: float
    locked_percentage: float
    unlock_time: Optional[int]  # Unix timestamp, None if permanent
    is_permanent: bool


@dataclass
class TokenReport:
    """Comprehensive token security report"""
    mint: str
    symbol: str
    name: str
    
    # Risk scoring
    risk_score: int  # 0-100, higher = more risky
    risk_level: RiskLevel
    
    # Authority status
    mint_authority: Optional[str]  # None if renounced
    freeze_authority: Optional[str]  # None if renounced
    
    # Holder analysis
    top_holders: List[Dict[str, Any]]
    creator_balance_percentage: float
    
    # Liquidity
    total_liquidity_usd: float
    lp_locked_percentage: float
    lp_lockers: List[LPLocker]
    
    # Risks identified
    risks: List[TokenRisk]
    
    # Metadata
    verified: bool
    rugged: bool
    
    def is_safe(self, max_risk_score: int = 50) -> bool:
        """Check if token passes safety threshold"""
        return self.risk_score < max_risk_score and not self.rugged
    
    def has_renounced_mint(self) -> bool:
        """Check if mint authority is renounced"""
        return self.mint_authority is None
    
    def has_renounced_freeze(self) -> bool:
        """Check if freeze authority is renounced"""
        return self.freeze_authority is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'mint': self.mint,
            'symbol': self.symbol,
            'name': self.name,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level.value,
            'mint_authority': self.mint_authority,
            'freeze_authority': self.freeze_authority,
            'top_holders': self.top_holders,
            'creator_balance_percentage': self.creator_balance_percentage,
            'total_liquidity_usd': self.total_liquidity_usd,
            'lp_locked_percentage': self.lp_locked_percentage,
            'verified': self.verified,
            'rugged': self.rugged,
            'is_safe': self.is_safe(),
            'risks': [
                {'name': r.name, 'description': r.description, 'level': r.level.value}
                for r in self.risks
            ]
        }


@dataclass
class TokenSummary:
    """Lightweight token security summary"""
    mint: str
    risk_score: int
    risk_level: RiskLevel
    is_safe: bool
    has_mint_authority: bool
    has_freeze_authority: bool
    lp_locked: bool


class RugCheckClient:
    """
    Client for RugCheck.xyz API.
    
    API Documentation: https://api.rugcheck.xyz/swagger/index.html
    
    Usage:
        client = RugCheckClient(api_key="your_api_key")
        report = await client.get_token_report("token_mint_address")
        if report.is_safe():
            print("Token appears safe!")
    """
    
    BASE_URL = "https://api.rugcheck.xyz"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        """
        Initialize RugCheck client.
        
        Args:
            api_key: Optional API key for authenticated requests
            timeout: Request timeout in seconds
            max_retries: Max retry attempts for failed requests
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=headers,
                timeout=self.timeout
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request with retry logic"""
        client = await self._get_client()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, endpoint, **kwargs)
                
                if response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = min(2 ** attempt, 10)
                    logger.warning(f"Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(f"HTTP error {e.response.status_code}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    
            except httpx.RequestError as e:
                last_error = e
                logger.warning(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
        
        raise last_error or Exception("Request failed after retries")
    
    async def get_token_report(self, mint: str) -> Optional[TokenReport]:
        """
        Get comprehensive token security report.
        
        Endpoint: GET /v1/tokens/{mint}/report
        
        Args:
            mint: Token mint address
            
        Returns:
            TokenReport with full security analysis
        """
        try:
            logger.info(f"🔍 Fetching RugCheck report for {mint[:8]}...")
            
            data = await self._request("GET", f"/v1/tokens/{mint}/report")
            
            return self._parse_report(data)
            
        except Exception as e:
            logger.error(f"Failed to get token report: {e}")
            return None
    
    async def get_lp_lockers(self, mint: str) -> List[LPLocker]:
        """
        Get LP token locker information.
        
        Endpoint: GET /v1/tokens/{mint}/lockers
        
        Args:
            mint: Token mint address
            
        Returns:
            List of LP locker details
        """
        try:
            data = await self._request("GET", f"/v1/tokens/{mint}/lockers")
            
            lockers = []
            for item in data.get('lockers', []):
                locker = LPLocker(
                    locker_name=item.get('name', 'Unknown'),
                    locker_address=item.get('address', ''),
                    locked_amount=float(item.get('amount', 0)),
                    locked_percentage=float(item.get('percentage', 0)),
                    unlock_time=item.get('unlockTime'),
                    is_permanent=item.get('isPermanent', False)
                )
                lockers.append(locker)
            
            return lockers
            
        except Exception as e:
            logger.error(f"Failed to get LP lockers: {e}")
            return []
    
    async def bulk_check(
        self,
        mints: List[str]
    ) -> Dict[str, TokenSummary]:
        """
        Batch check multiple tokens.
        
        Endpoint: POST /v1/bulk/tokens/summary
        
        Args:
            mints: List of token mint addresses
            
        Returns:
            Dictionary mapping mint -> TokenSummary
        """
        try:
            data = await self._request(
                "POST",
                "/v1/bulk/tokens/summary",
                json={"mints": mints}
            )
            
            results = {}
            for item in data.get('tokens', []):
                mint = item.get('mint', '')
                summary = TokenSummary(
                    mint=mint,
                    risk_score=item.get('riskScore', 100),
                    risk_level=self._parse_risk_level(item.get('riskLevel', 'Unknown')),
                    is_safe=item.get('riskScore', 100) < 50,
                    has_mint_authority=item.get('hasMintAuthority', True),
                    has_freeze_authority=item.get('hasFreezeAuthority', True),
                    lp_locked=item.get('lpLocked', False)
                )
                results[mint] = summary
            
            return results
            
        except Exception as e:
            logger.error(f"Failed bulk check: {e}")
            return {}
    
    async def check_is_safe(
        self,
        mint: str,
        max_risk_score: int = 50,
        require_renounced_mint: bool = True,
        require_renounced_freeze: bool = False,
        min_liquidity_usd: float = 1000.0
    ) -> tuple[bool, Optional[TokenReport], List[str]]:
        """
        Quick safety check with configurable thresholds.
        
        Args:
            mint: Token mint address
            max_risk_score: Maximum acceptable risk score
            require_renounced_mint: Require mint authority renounced
            require_renounced_freeze: Require freeze authority renounced
            min_liquidity_usd: Minimum liquidity in USD
            
        Returns:
            Tuple of (is_safe, report, warnings)
        """
        warnings = []
        
        report = await self.get_token_report(mint)
        if not report:
            return False, None, ["Failed to fetch token report"]
        
        # Check risk score
        if report.risk_score > max_risk_score:
            warnings.append(f"High risk score: {report.risk_score}/100")
        
        # Check if rugged
        if report.rugged:
            warnings.append("⚠️ Token marked as RUGGED")
            return False, report, warnings
        
        # Check mint authority
        if require_renounced_mint and not report.has_renounced_mint():
            warnings.append(f"Mint authority active: {report.mint_authority[:8]}...")
        
        # Check freeze authority
        if require_renounced_freeze and not report.has_renounced_freeze():
            warnings.append(f"Freeze authority active: {report.freeze_authority[:8]}...")
        
        # Check liquidity
        if report.total_liquidity_usd < min_liquidity_usd:
            warnings.append(f"Low liquidity: ${report.total_liquidity_usd:.2f}")
        
        # Add individual risk warnings
        for risk in report.risks:
            if risk.level == RiskLevel.DANGER:
                warnings.append(f"🚨 {risk.name}: {risk.description}")
        
        is_safe = len([w for w in warnings if w.startswith("🚨") or w.startswith("⚠️")]) == 0
        is_safe = is_safe and report.risk_score <= max_risk_score
        
        return is_safe, report, warnings
    
    def _parse_report(self, data: Dict[str, Any]) -> TokenReport:
        """Parse API response into TokenReport"""
        
        # Parse risks
        risks = []
        for risk_data in data.get('risks', []):
            risk = TokenRisk(
                name=risk_data.get('name', 'Unknown'),
                value=risk_data.get('value', ''),
                description=risk_data.get('description', ''),
                score=risk_data.get('score', 0),
                level=self._parse_risk_level(risk_data.get('level', 'Unknown'))
            )
            risks.append(risk)
        
        # Parse top holders
        top_holders = data.get('topHolders', [])
        
        # Parse LP lockers
        lp_lockers = []
        for locker_data in data.get('lpLockers', []):
            locker = LPLocker(
                locker_name=locker_data.get('name', 'Unknown'),
                locker_address=locker_data.get('address', ''),
                locked_amount=float(locker_data.get('amount', 0)),
                locked_percentage=float(locker_data.get('percentage', 0)),
                unlock_time=locker_data.get('unlockTime'),
                is_permanent=locker_data.get('isPermanent', False)
            )
            lp_lockers.append(locker)
        
        return TokenReport(
            mint=data.get('mint', ''),
            symbol=data.get('tokenMeta', {}).get('symbol', ''),
            name=data.get('tokenMeta', {}).get('name', ''),
            risk_score=data.get('score', 100),
            risk_level=self._parse_risk_level(data.get('riskLevel', 'Unknown')),
            mint_authority=data.get('mintAuthority') if data.get('mintAuthority') else None,
            freeze_authority=data.get('freezeAuthority') if data.get('freezeAuthority') else None,
            top_holders=top_holders,
            creator_balance_percentage=float(data.get('creatorBalance', 0)),
            total_liquidity_usd=float(data.get('totalLiquidityUsd', 0)),
            lp_locked_percentage=float(data.get('lpLockedPct', 0)),
            lp_lockers=lp_lockers,
            risks=risks,
            verified=data.get('verified', False),
            rugged=data.get('rugged', False)
        )
    
    def _parse_risk_level(self, level: str) -> RiskLevel:
        """Parse risk level string to enum"""
        level_map = {
            'good': RiskLevel.GOOD,
            'caution': RiskLevel.CAUTION,
            'warn': RiskLevel.CAUTION,
            'danger': RiskLevel.DANGER,
            'high': RiskLevel.DANGER,
        }
        return level_map.get(level.lower(), RiskLevel.UNKNOWN)


# Convenience function for quick checks
async def quick_check(mint: str, api_key: Optional[str] = None) -> bool:
    """
    Quick safety check for a token.
    
    Usage:
        is_safe = await quick_check("token_mint_address")
    """
    client = RugCheckClient(api_key=api_key)
    try:
        is_safe, _, warnings = await client.check_is_safe(mint)
        if warnings:
            logger.info(f"Warnings for {mint[:8]}...: {warnings}")
        return is_safe
    finally:
        await client.close()
