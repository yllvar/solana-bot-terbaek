"""
Jito Bundle Client - MEV protected transaction execution.

Provides Jito block engine integration for:
- Atomic bundle submission (up to 5 transactions)
- Priority transaction execution with tips
- MEV protection by bypassing public mempool
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

import httpx
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.signature import Signature

logger = logging.getLogger(__name__)


class TipUrgency(Enum):
    """Tip urgency levels for transaction priority"""
    LOW = "low"         # Background transaction, not time-sensitive
    MEDIUM = "medium"   # Normal priority
    HIGH = "high"       # Snipe/time-sensitive
    CRITICAL = "critical"  # MEV-sensitive, maximum priority


@dataclass
class BundleResult:
    """Result of bundle submission"""
    success: bool
    bundle_id: Optional[str]
    signatures: List[str]
    error: Optional[str]
    slot: Optional[int]


class JitoClient:
    """
    Client for Jito block engine.
    
    Jito bundles allow atomic execution of up to 5 transactions,
    guaranteed to execute in order or not at all.
    
    Usage:
        jito = JitoClient(keypair)
        result = await jito.send_bundle([tx1, tx2], tip_lamports=10000)
    """
    
    # Jito Block Engine endpoints
    MAINNET_BLOCK_ENGINE = "https://mainnet.block-engine.jito.wtf"
    TESTNET_BLOCK_ENGINE = "https://ny.testnet.block-engine.jito.wtf"
    
    # Default tip amounts (in lamports)
    TIP_AMOUNTS = {
        TipUrgency.LOW: 1000,        # 0.000001 SOL
        TipUrgency.MEDIUM: 10000,    # 0.00001 SOL
        TipUrgency.HIGH: 100000,     # 0.0001 SOL
        TipUrgency.CRITICAL: 500000  # 0.0005 SOL
    }
    
    # Known tip account addresses
    TIP_ACCOUNTS = [
        "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
        "HFqU5x63VTqvQss8hp11i4bVmkdzGZVJKQKQpqjU5u1",
        "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
        "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
        "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
        "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
        "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
        "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"
    ]
    
    def __init__(
        self,
        keypair: Keypair,
        use_mainnet: bool = True,
        endpoint: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Jito client.
        
        Args:
            keypair: Wallet keypair for signing transactions
            use_mainnet: Use mainnet block engine (default True)
            endpoint: Custom block engine endpoint
            timeout: Request timeout in seconds
        """
        self.keypair = keypair
        self.timeout = timeout
        
        if endpoint:
            self.endpoint = endpoint
        elif use_mainnet:
            self.endpoint = self.MAINNET_BLOCK_ENGINE
        else:
            self.endpoint = self.TESTNET_BLOCK_ENGINE
        
        self._client: Optional[httpx.AsyncClient] = None
        self._tip_account_index = 0
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.endpoint,
                timeout=self.timeout
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def get_tip_account(self) -> str:
        """
        Get next tip account address (round-robin).
        
        Returns:
            Tip account public key string
        """
        account = self.TIP_ACCOUNTS[self._tip_account_index]
        self._tip_account_index = (self._tip_account_index + 1) % len(self.TIP_ACCOUNTS)
        return account
    
    async def fetch_tip_accounts(self) -> List[str]:
        """
        Fetch current tip accounts from Jito API.
        
        Returns:
            List of tip account addresses
        """
        try:
            client = await self._get_client()
            response = await client.get("/api/v1/bundles/tip_accounts")
            response.raise_for_status()
            data = response.json()
            return data.get('tip_accounts', self.TIP_ACCOUNTS)
        except Exception as e:
            logger.warning(f"Failed to fetch tip accounts, using defaults: {e}")
            return self.TIP_ACCOUNTS
    
    def calculate_tip(
        self,
        urgency: TipUrgency = TipUrgency.MEDIUM,
        estimated_profit_lamports: Optional[int] = None
    ) -> int:
        """
        Calculate optimal tip amount.
        
        Args:
            urgency: How urgent the transaction is
            estimated_profit_lamports: Expected profit (tip = % of profit)
            
        Returns:
            Tip amount in lamports
        """
        base_tip = self.TIP_AMOUNTS[urgency]
        
        if estimated_profit_lamports:
            # Tip 1-5% of profit based on urgency
            profit_pct = {
                TipUrgency.LOW: 0.01,
                TipUrgency.MEDIUM: 0.02,
                TipUrgency.HIGH: 0.03,
                TipUrgency.CRITICAL: 0.05
            }
            profit_tip = int(estimated_profit_lamports * profit_pct[urgency])
            return max(base_tip, profit_tip)
        
        return base_tip
    
    async def send_bundle(
        self,
        transactions: List[VersionedTransaction],
        tip_lamports: int = 10000
    ) -> BundleResult:
        """
        Submit atomic bundle of transactions.
        
        All transactions in bundle execute in order, or none execute.
        Maximum 5 transactions per bundle.
        
        Args:
            transactions: List of signed transactions (max 5)
            tip_lamports: Tip amount for priority
            
        Returns:
            BundleResult with submission details
        """
        if len(transactions) > 5:
            return BundleResult(
                success=False,
                bundle_id=None,
                signatures=[],
                error="Bundle cannot exceed 5 transactions",
                slot=None
            )
        
        if len(transactions) == 0:
            return BundleResult(
                success=False,
                bundle_id=None,
                signatures=[],
                error="Bundle must contain at least 1 transaction",
                slot=None
            )
        
        try:
            # Serialize transactions to base64
            serialized_txs = []
            signatures = []
            
            for tx in transactions:
                # Get signature
                if hasattr(tx, 'signatures') and tx.signatures:
                    signatures.append(str(tx.signatures[0]))
                
                # Serialize to bytes and encode
                tx_bytes = bytes(tx)
                import base64
                tx_b64 = base64.b64encode(tx_bytes).decode('utf-8')
                serialized_txs.append(tx_b64)
            
            # Build bundle request
            bundle_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "sendBundle",
                "params": [serialized_txs]
            }
            
            logger.info(f"📦 Submitting bundle with {len(transactions)} transactions...")
            logger.info(f"💰 Tip: {tip_lamports / 1e9:.6f} SOL")
            
            client = await self._get_client()
            response = await client.post(
                "/api/v1/bundles",
                json=bundle_request
            )
            
            if response.status_code != 200:
                error_msg = f"Bundle submission failed: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
                
                return BundleResult(
                    success=False,
                    bundle_id=None,
                    signatures=signatures,
                    error=error_msg,
                    slot=None
                )
            
            data = response.json()
            bundle_id = data.get('result')
            
            logger.info(f"✅ Bundle submitted! ID: {bundle_id}")
            
            return BundleResult(
                success=True,
                bundle_id=bundle_id,
                signatures=signatures,
                error=None,
                slot=None
            )
            
        except Exception as e:
            logger.error(f"Bundle submission error: {e}")
            return BundleResult(
                success=False,
                bundle_id=None,
                signatures=[],
                error=str(e),
                slot=None
            )
    
    async def send_transaction(
        self,
        transaction: VersionedTransaction,
        tip_lamports: int = 5000
    ) -> Optional[str]:
        """
        Send single transaction with Jito priority.
        
        Args:
            transaction: Signed transaction
            tip_lamports: Tip amount
            
        Returns:
            Transaction signature if successful
        """
        result = await self.send_bundle([transaction], tip_lamports)
        
        if result.success and result.signatures:
            return result.signatures[0]
        
        if result.error:
            logger.error(f"Transaction failed: {result.error}")
        
        return None
    
    async def get_bundle_status(
        self,
        bundle_id: str
    ) -> Dict[str, Any]:
        """
        Get status of submitted bundle.
        
        Args:
            bundle_id: Bundle ID from send_bundle
            
        Returns:
            Status dictionary with bundle state
        """
        try:
            client = await self._get_client()
            
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBundleStatuses",
                "params": [[bundle_id]]
            }
            
            response = await client.post(
                "/api/v1/bundles",
                json=request
            )
            
            data = response.json()
            statuses = data.get('result', {}).get('value', [])
            
            if statuses:
                return statuses[0]
            
            return {"status": "unknown", "bundle_id": bundle_id}
            
        except Exception as e:
            logger.error(f"Failed to get bundle status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def wait_for_confirmation(
        self,
        bundle_id: str,
        timeout_seconds: float = 30.0,
        poll_interval: float = 0.5
    ) -> bool:
        """
        Wait for bundle confirmation.
        
        Args:
            bundle_id: Bundle ID to wait for
            timeout_seconds: Maximum wait time
            poll_interval: Time between status checks
            
        Returns:
            True if bundle confirmed, False if timeout or failed
        """
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
            status = await self.get_bundle_status(bundle_id)
            
            confirmation_status = status.get('confirmation_status')
            
            if confirmation_status == 'confirmed':
                logger.info(f"✅ Bundle {bundle_id} confirmed!")
                return True
            elif confirmation_status == 'finalized':
                logger.info(f"✅ Bundle {bundle_id} finalized!")
                return True
            elif confirmation_status in ['failed', 'invalid']:
                logger.error(f"❌ Bundle {bundle_id} failed: {status}")
                return False
            
            await asyncio.sleep(poll_interval)
        
        logger.warning(f"⏰ Bundle {bundle_id} confirmation timeout")
        return False


# Factory function
def create_jito_client(
    keypair: Keypair,
    use_mainnet: bool = True
) -> JitoClient:
    """
    Create a Jito client instance.
    
    Args:
        keypair: Wallet keypair
        use_mainnet: Use mainnet or testnet
        
    Returns:
        Configured JitoClient
    """
    return JitoClient(keypair, use_mainnet=use_mainnet)
