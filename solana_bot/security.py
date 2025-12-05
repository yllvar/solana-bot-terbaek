"""
Modul untuk analisis keselamatan token (rug pull detection)

Enhanced version with:
- Real on-chain SPL Token parsing for mint/freeze authority
- Actual liquidity calculation from pool vaults
- RugCheck API integration for comprehensive analysis
"""
import logging
import struct
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient

from .rugcheck_client import RugCheckClient, TokenReport, RiskLevel

logger = logging.getLogger(__name__)

# SPL Token Mint Layout offsets
# Reference: https://github.com/solana-labs/solana-program-library/blob/master/token/program/src/state.rs
MINT_LAYOUT = {
    'mint_authority_option': 0,      # 4 bytes (COption<Pubkey> tag)
    'mint_authority': 4,             # 32 bytes
    'supply': 36,                    # 8 bytes (u64)
    'decimals': 44,                  # 1 byte
    'is_initialized': 45,            # 1 byte (bool)
    'freeze_authority_option': 46,   # 4 bytes (COption<Pubkey> tag)
    'freeze_authority': 50,          # 32 bytes
}

# WSOL mint address
WSOL_MINT = "So11111111111111111111111111111111111111112"


@dataclass
class TokenAuthorities:
    """Token mint and freeze authority information"""
    mint_authority: Optional[str]
    freeze_authority: Optional[str]
    supply: int
    decimals: int


class SecurityAnalyzer:
    """
    Enhanced token security analyzer.
    
    Performs real on-chain checks and optionally integrates with RugCheck API.
    """
    
    def __init__(
        self,
        rpc_client: AsyncClient,
        rugcheck_api_key: Optional[str] = None,
        min_liquidity_sol: float = 5.0,
        max_top_holder_pct: float = 20.0,
        max_risk_score: int = 50
    ):
        """
        Initialize security analyzer.
        
        Args:
            rpc_client: Solana RPC client
            rugcheck_api_key: Optional RugCheck API key for enhanced checks
            min_liquidity_sol: Minimum acceptable liquidity in SOL
            max_top_holder_pct: Maximum acceptable top holder percentage
            max_risk_score: Maximum acceptable RugCheck risk score
        """
        self.client = rpc_client
        self.rugcheck_api_key = rugcheck_api_key
        self.min_liquidity_sol = min_liquidity_sol
        self.max_top_holder_pct = max_top_holder_pct
        self.max_risk_score = max_risk_score
        
        self._rugcheck: Optional[RugCheckClient] = None
    
    async def _get_rugcheck(self) -> RugCheckClient:
        """Get or create RugCheck client"""
        if self._rugcheck is None:
            self._rugcheck = RugCheckClient(api_key=self.rugcheck_api_key)
        return self._rugcheck
    
    async def close(self):
        """Cleanup resources"""
        if self._rugcheck:
            await self._rugcheck.close()
    
    async def analyze_token(
        self,
        token_mint: Pubkey,
        pool_address: Pubkey,
        use_rugcheck: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive token security analysis.
        
        Args:
            token_mint: Token mint address
            pool_address: Pool/AMM address
            use_rugcheck: Whether to use RugCheck API for additional checks
            
        Returns:
            Analysis results with risk score and warnings
        """
        logger.info(f"🔍 Analyzing token security: {token_mint}")
        
        results = {
            'is_safe': True,
            'risk_score': 0,
            'warnings': [],
            'checks': {},
            'rugcheck_report': None
        }
        
        # 1. On-chain authority checks
        mint_check = await self._check_mint_authority(token_mint)
        results['checks']['mint_authority'] = mint_check
        if not mint_check['passed']:
            results['warnings'].append(mint_check['message'])
            results['risk_score'] += 30
        
        freeze_check = await self._check_freeze_authority(token_mint)
        results['checks']['freeze_authority'] = freeze_check
        if not freeze_check['passed']:
            results['warnings'].append(freeze_check['message'])
            results['risk_score'] += 20
        
        # 2. Liquidity check
        liquidity_check = await self._check_liquidity(pool_address)
        results['checks']['liquidity'] = liquidity_check
        if not liquidity_check['passed']:
            results['warnings'].append(liquidity_check['message'])
            results['risk_score'] += 25
        
        # 3. RugCheck API analysis (if enabled)
        if use_rugcheck:
            rugcheck_result = await self._check_rugcheck(str(token_mint))
            results['checks']['rugcheck'] = rugcheck_result
            results['rugcheck_report'] = rugcheck_result.get('report')
            
            if not rugcheck_result['passed']:
                results['warnings'].extend(rugcheck_result.get('warnings', []))
                results['risk_score'] += rugcheck_result.get('risk_contribution', 0)
        
        # 4. Top holders check (from RugCheck or on-chain)
        holders_check = await self._check_top_holders(
            token_mint,
            results.get('rugcheck_report')
        )
        results['checks']['top_holders'] = holders_check
        if not holders_check['passed']:
            results['warnings'].append(holders_check['message'])
            results['risk_score'] += 25
        
        # Final safety determination
        results['risk_score'] = min(results['risk_score'], 100)
        results['is_safe'] = results['risk_score'] < self.max_risk_score
        
        if results['is_safe']:
            logger.info(f"✅ Token appears safe (Risk Score: {results['risk_score']})")
        else:
            logger.warning(f"⚠️  Token is risky! (Risk Score: {results['risk_score']})")
            for warning in results['warnings']:
                logger.warning(f"   - {warning}")
        
        return results
    
    async def quick_check(
        self,
        token_mint: str,
        pool_address: Optional[str] = None
    ) -> tuple[bool, List[str]]:
        """
        Quick safety check with minimal overhead.
        
        Args:
            token_mint: Token mint address string
            pool_address: Optional pool address
            
        Returns:
            Tuple of (is_safe, warnings)
        """
        warnings = []
        
        # Parse addresses
        try:
            mint_pubkey = Pubkey.from_string(token_mint)
        except Exception as e:
            return False, [f"Invalid mint address: {e}"]
        
        # Check authorities
        authorities = await self._parse_mint_account(mint_pubkey)
        if authorities:
            if authorities.mint_authority:
                warnings.append(f"⚠️ Mint authority active: {authorities.mint_authority[:8]}...")
            if authorities.freeze_authority:
                warnings.append(f"⚠️ Freeze authority active: {authorities.freeze_authority[:8]}...")
        else:
            warnings.append("❌ Could not parse mint account")
        
        # RugCheck quick check
        try:
            rugcheck = await self._get_rugcheck()
            is_safe, report, rc_warnings = await rugcheck.check_is_safe(
                token_mint,
                max_risk_score=self.max_risk_score
            )
            warnings.extend(rc_warnings)
        except Exception as e:
            logger.warning(f"RugCheck unavailable: {e}")
        
        is_safe = len([w for w in warnings if w.startswith("⚠️") or w.startswith("❌") or w.startswith("🚨")]) == 0
        return is_safe, warnings
    
    async def _parse_mint_account(self, mint: Pubkey) -> Optional[TokenAuthorities]:
        """
        Parse SPL Token Mint account to extract authorities.
        
        Args:
            mint: Mint pubkey
            
        Returns:
            TokenAuthorities or None if parsing fails
        """
        try:
            account_info = await self.client.get_account_info(mint)
            
            if not account_info.value:
                logger.warning(f"Mint account not found: {mint}")
                return None
            
            data = bytes(account_info.value.data)
            
            if len(data) < 82:  # Minimum size for SPL Token Mint
                logger.warning(f"Invalid mint data length: {len(data)}")
                return None
            
            # Parse mint authority (COption<Pubkey>)
            mint_auth_option = struct.unpack_from('<I', data, MINT_LAYOUT['mint_authority_option'])[0]
            mint_authority = None
            if mint_auth_option == 1:  # Some
                mint_auth_bytes = data[MINT_LAYOUT['mint_authority']:MINT_LAYOUT['mint_authority']+32]
                mint_authority = str(Pubkey.from_bytes(mint_auth_bytes))
            
            # Parse supply
            supply = struct.unpack_from('<Q', data, MINT_LAYOUT['supply'])[0]
            
            # Parse decimals
            decimals = data[MINT_LAYOUT['decimals']]
            
            # Parse freeze authority (COption<Pubkey>)
            freeze_auth_option = struct.unpack_from('<I', data, MINT_LAYOUT['freeze_authority_option'])[0]
            freeze_authority = None
            if freeze_auth_option == 1:  # Some
                freeze_auth_bytes = data[MINT_LAYOUT['freeze_authority']:MINT_LAYOUT['freeze_authority']+32]
                freeze_authority = str(Pubkey.from_bytes(freeze_auth_bytes))
            
            return TokenAuthorities(
                mint_authority=mint_authority,
                freeze_authority=freeze_authority,
                supply=supply,
                decimals=decimals
            )
            
        except Exception as e:
            logger.error(f"Error parsing mint account: {e}")
            return None
    
    async def _check_mint_authority(self, token_mint: Pubkey) -> Dict[str, Any]:
        """
        Check if mint authority has been renounced.
        
        Parses actual SPL Token Mint account data.
        """
        try:
            authorities = await self._parse_mint_account(token_mint)
            
            if not authorities:
                return {
                    'passed': False,
                    'message': '❌ Could not parse mint account',
                    'authority': None
                }
            
            if authorities.mint_authority:
                return {
                    'passed': False,
                    'message': f'⚠️ Mint authority active: {authorities.mint_authority[:16]}...',
                    'authority': authorities.mint_authority
                }
            else:
                return {
                    'passed': True,
                    'message': '✅ Mint authority renounced',
                    'authority': None
                }
                
        except Exception as e:
            logger.error(f"Error checking mint authority: {e}")
            return {
                'passed': False,
                'message': f'❌ Error: {str(e)}',
                'authority': None
            }
    
    async def _check_freeze_authority(self, token_mint: Pubkey) -> Dict[str, Any]:
        """
        Check if freeze authority has been renounced.
        
        Freeze authority allows token issuer to freeze any holder's tokens.
        """
        try:
            authorities = await self._parse_mint_account(token_mint)
            
            if not authorities:
                return {
                    'passed': False,
                    'message': '❌ Could not parse mint account',
                    'authority': None
                }
            
            if authorities.freeze_authority:
                return {
                    'passed': False,
                    'message': f'⚠️ Freeze authority active: {authorities.freeze_authority[:16]}...',
                    'authority': authorities.freeze_authority
                }
            else:
                return {
                    'passed': True,
                    'message': '✅ Freeze authority renounced',
                    'authority': None
                }
                
        except Exception as e:
            logger.error(f"Error checking freeze authority: {e}")
            return {
                'passed': False,
                'message': f'❌ Error: {str(e)}',
                'authority': None
            }
    
    async def _check_liquidity(self, pool_address: Pubkey) -> Dict[str, Any]:
        """
        Check pool liquidity by fetching vault balances.
        
        For Raydium pools, reads the WSOL vault to determine SOL liquidity.
        """
        try:
            # Import here to avoid circular dependency
            from .raydium.layouts import AMM_INFO_LAYOUT_V4
            
            # Fetch pool account
            pool_info = await self.client.get_account_info(pool_address)
            
            if not pool_info.value:
                return {
                    'passed': False,
                    'message': '❌ Pool account not found',
                    'liquidity_sol': 0
                }
            
            # Parse pool data to get vault addresses
            data = bytes(pool_info.value.data)
            parsed = AMM_INFO_LAYOUT_V4.parse(data)
            
            # Get base and quote vault pubkeys
            base_vault = Pubkey.from_bytes(parsed.base_vault)
            quote_vault = Pubkey.from_bytes(parsed.quote_vault)
            
            # Fetch vault balances
            # Quote vault is usually WSOL
            quote_balance = await self.client.get_token_account_balance(quote_vault)
            
            if not quote_balance.value:
                return {
                    'passed': False,
                    'message': '❌ Could not fetch vault balance',
                    'liquidity_sol': 0
                }
            
            # Convert lamports to SOL
            liquidity_sol = float(quote_balance.value.amount) / 1e9
            
            if liquidity_sol < self.min_liquidity_sol:
                return {
                    'passed': False,
                    'message': f'⚠️ Low liquidity: {liquidity_sol:.2f} SOL (min: {self.min_liquidity_sol} SOL)',
                    'liquidity_sol': liquidity_sol
                }
            else:
                return {
                    'passed': True,
                    'message': f'✅ Sufficient liquidity: {liquidity_sol:.2f} SOL',
                    'liquidity_sol': liquidity_sol
                }
                
        except Exception as e:
            logger.error(f"Error checking liquidity: {e}")
            return {
                'passed': False,
                'message': f'❌ Error: {str(e)}',
                'liquidity_sol': 0
            }
    
    async def _check_rugcheck(self, token_mint: str) -> Dict[str, Any]:
        """
        Fetch and analyze RugCheck report.
        
        Integrates with RugCheck API for comprehensive security analysis.
        """
        try:
            rugcheck = await self._get_rugcheck()
            
            is_safe, report, warnings = await rugcheck.check_is_safe(
                token_mint,
                max_risk_score=self.max_risk_score,
                require_renounced_mint=True,
                require_renounced_freeze=False,
                min_liquidity_usd=1000.0
            )
            
            if not report:
                return {
                    'passed': True,  # Don't fail if API unavailable
                    'message': '⚠️ RugCheck API unavailable',
                    'warnings': [],
                    'risk_contribution': 0,
                    'report': None
                }
            
            risk_contribution = 0
            if report.rugged:
                risk_contribution = 50
            elif report.risk_score > self.max_risk_score:
                risk_contribution = min(30, (report.risk_score - self.max_risk_score))
            
            return {
                'passed': is_safe and not report.rugged,
                'message': f'RugCheck Score: {report.risk_score}/100 ({report.risk_level.value})',
                'warnings': warnings,
                'risk_contribution': risk_contribution,
                'report': report
            }
            
        except Exception as e:
            logger.warning(f"RugCheck check failed: {e}")
            return {
                'passed': True,  # Don't fail if API unavailable
                'message': f'⚠️ RugCheck unavailable: {str(e)}',
                'warnings': [],
                'risk_contribution': 0,
                'report': None
            }
    
    async def _check_top_holders(
        self,
        token_mint: Pubkey,
        rugcheck_report: Optional[TokenReport] = None
    ) -> Dict[str, Any]:
        """
        Check token holder concentration.
        
        Uses RugCheck data if available, otherwise returns unknown.
        On-chain top holder check requires getTokenLargestAccounts which
        may not be available on all RPC providers.
        """
        try:
            # Use RugCheck data if available
            if rugcheck_report and rugcheck_report.top_holders:
                top_holder = rugcheck_report.top_holders[0] if rugcheck_report.top_holders else {}
                top_holder_pct = float(top_holder.get('percentage', 0))
                
                if top_holder_pct > self.max_top_holder_pct:
                    return {
                        'passed': False,
                        'message': f'⚠️ Top holder has {top_holder_pct:.1f}% (max: {self.max_top_holder_pct}%)',
                        'top_holder_percentage': top_holder_pct
                    }
                else:
                    return {
                        'passed': True,
                        'message': f'✅ Good distribution (top holder: {top_holder_pct:.1f}%)',
                        'top_holder_percentage': top_holder_pct
                    }
            
            # Try on-chain check (may not be available on all RPCs)
            try:
                largest = await self.client.get_token_largest_accounts(token_mint)
                if largest.value:
                    total_supply = sum(int(acc.amount) for acc in largest.value)
                    if total_supply > 0 and largest.value:
                        top_amount = int(largest.value[0].amount)
                        top_pct = (top_amount / total_supply) * 100
                        
                        if top_pct > self.max_top_holder_pct:
                            return {
                                'passed': False,
                                'message': f'⚠️ Top holder has {top_pct:.1f}%',
                                'top_holder_percentage': top_pct
                            }
                        else:
                            return {
                                'passed': True,
                                'message': f'✅ Good distribution (top holder: {top_pct:.1f}%)',
                                'top_holder_percentage': top_pct
                            }
            except Exception:
                pass  # RPC method may not be available
            
            # Default: pass with unknown status
            return {
                'passed': True,
                'message': 'ℹ️ Top holder data unavailable',
                'top_holder_percentage': None
            }
            
        except Exception as e:
            logger.error(f"Error checking top holders: {e}")
            return {
                'passed': True,  # Don't fail on error
                'message': f'ℹ️ Could not check top holders: {str(e)}',
                'top_holder_percentage': None
            }
