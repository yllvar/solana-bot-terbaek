"""
Modul untuk monitor pool baharu di Raydium dan Auto Buy
"""
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Confirmed

from .raydium.swap import RaydiumSwap
from .transaction import TransactionBuilder
from .config import BotConfig

logger = logging.getLogger(__name__)

class PoolMonitor:
    """Kelas untuk monitor pool baharu di Raydium"""
    
    def __init__(
        self,
        rpc_endpoint: str,
        ws_endpoint: str,
        raydium_program_id: Pubkey,
        config: BotConfig,
        wallet_manager,
        callback: Optional[Callable] = None
    ):
        self.rpc_endpoint = rpc_endpoint
        self.ws_endpoint = ws_endpoint
        self.raydium_program_id = raydium_program_id
        self.config = config
        self.wallet = wallet_manager
        self.callback = callback
        self.client = AsyncClient(rpc_endpoint)
        self.is_monitoring = False
        
        self.raydium_swap = RaydiumSwap(self.client, self.wallet)
        self.tx_builder = TransactionBuilder(self.client, self.wallet)
        
    async def start_monitoring(self):
        """Mula monitor pool baharu"""
        self.is_monitoring = True
        logger.info("🔍 Memulakan pemantauan pool baharu...")
        
        try:
            async with connect(self.ws_endpoint) as websocket:
                await websocket.logs_subscribe(
                    filter_=RpcTransactionLogsFilterMentions(self.raydium_program_id),
                    commitment=Confirmed
                )
                logger.info("✅ Berjaya subscribe ke Raydium program")
                
                async for notification in websocket:
                    if not self.is_monitoring:
                        break
                    try:
                        await self._process_notification(notification)
                    except Exception as e:
                        logger.error(f"❌ Error memproses notifikasi: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error dalam monitoring: {e}")
        finally:
            self.is_monitoring = False
            logger.info("⏹️  Pemantauan dihentikan")
    
    async def _process_notification(self, notification):
        """Proses notifikasi dari WebSocket"""
        if hasattr(notification, 'result'):
            result = notification.result
            
            if self._is_new_pool(result):
                pool_info = await self._extract_pool_info(result)
                
                if pool_info:
                    logger.info(f"🆕 Pool baharu dijumpai: {pool_info.get('token_address')}")
                    
                    if self.callback:
                        await self.callback(pool_info)
                    
                    if self.config.buy_amount > 0:
                        await self.execute_auto_buy(pool_info)
    
    async def execute_auto_buy(self, pool_info: Dict[str, Any]):
        """Laksanakan pembelian automatik"""
        logger.info(f"🤖 Memulakan Auto Buy untuk {pool_info.get('token_address')}...")
        
        try:
            if hasattr(self.config, 'buy_delay') and self.config.buy_delay > 0:
                logger.info(f"⏳ Menunggu {self.config.buy_delay} saat...")
                await asyncio.sleep(self.config.buy_delay)
            
            pool_address = pool_info.get('pool_address')
            if not pool_address:
                logger.warning("Alamat pool tidak dijumpai, membatalkan auto buy")
                return

            # 1. Dapatkan pool keys lengkap
            logger.info(f"🔄 Fetching pool keys: {pool_address}")
            pool_keys = await self.raydium_swap.get_pool_keys(pool_address)
            
            if not pool_keys:
                logger.error("❌ Gagal mendapatkan pool keys")
                return

            # 2. Kira jumlah
            amount_in = int(self.config.buy_amount * 1e9) # SOL to Lamports
            # Anggaran kasar min out (sepatutnya fetch reserves dulu)
            min_amount_out = 1 # Slippage protection minimal untuk sniping pantas
            
            # 3. Dapatkan akaun token
            owner = self.wallet.keypair.pubkey()
            # WSOL (Base) -> Token (Quote) atau sebaliknya.
            # Biasanya pair baru adalah Token/SOL.
            # Kita perlu swap SOL -> Token.
            # SOL input account adalah WSOL account (atau native SOL handling).
            # Raydium swap perlukan WSOL account.
            # Untuk simplifikasi, kita anggap pengguna ada WSOL atau kita wrap SOL (perlu implementasi wrap).
            # Atau guna akaun SOL native jika disokong (Raydium biasanya perlu WSOL).
            
            # Placeholder: Kita perlukan WSOL ATA dan Token ATA
            token_account_in = self.raydium_swap.get_associated_token_address(owner, pool_keys['base_mint'])
            token_account_out = self.raydium_swap.get_associated_token_address(owner, pool_keys['quote_mint'])
            
            # 4. Bina swap instruction
            swap_ix = self.raydium_swap.build_swap_instruction(
                pool_keys,
                amount_in,
                min_amount_out,
                token_account_in,
                token_account_out,
                owner
            )
            
            # 5. Hantar transaksi
            signature = await self.tx_builder.build_and_send_transaction([swap_ix], skip_preflight=True)
            
            if signature:
                logger.info(f"✅ Auto Buy BERJAYA! TX: {signature}")
            else:
                logger.error("❌ Auto Buy GAGAL (TX failed)")
            
        except Exception as e:
            logger.error(f"❌ Auto Buy gagal: {e}")

    def _is_new_pool(self, result) -> bool:
        """Check jika result adalah pool baharu"""
        if hasattr(result, 'value') and result.value:
            logs = result.value.logs if hasattr(result.value, 'logs') else []
            for log in logs:
                if 'initialize' in log.lower() or 'create' in log.lower():
                    return True
        return False
    
    async def _extract_pool_info(self, result) -> Optional[Dict[str, Any]]:
        """Extract maklumat pool dari result"""
        # TODO: Implementasi parsing log yang sebenar untuk extract pool address
        # Ini memerlukan decoding log data Raydium
        # Placeholder untuk demo
        return {
            'token_address': 'Unknown',
            'pool_address': 'Unknown', # Perlu parsing log sebenar
            'timestamp': asyncio.get_event_loop().time()
        }
    
    async def stop_monitoring(self):
        """Hentikan monitoring"""
        self.is_monitoring = False
        await self.client.close()
