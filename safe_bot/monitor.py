"""
Modul untuk monitor pool baharu di Raydium dan Auto Buy
"""
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from solders.pubkey import Pubkey
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
        """
        Inisialisasi pool monitor
        """
        self.rpc_endpoint = rpc_endpoint
        self.ws_endpoint = ws_endpoint
        self.raydium_program_id = raydium_program_id
        self.config = config
        self.wallet = wallet_manager
        self.callback = callback
        self.client = AsyncClient(rpc_endpoint)
        self.is_monitoring = False
        
        # Inisialisasi komponen trading
        self.raydium_swap = RaydiumSwap(self.client, self.wallet)
        self.tx_builder = TransactionBuilder(self.client, self.wallet)
        
    async def start_monitoring(self):
        """Mula monitor pool baharu"""
        self.is_monitoring = True
        logger.info("🔍 Memulakan pemantauan pool baharu...")
        
        try:
            async with connect(self.ws_endpoint) as websocket:
                await websocket.logs_subscribe(
                    filter_={"mentions": [str(self.raydium_program_id)]},
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
                    
                    # Jalankan callback (untuk UI/Log)
                    if self.callback:
                        await self.callback(pool_info)
                    
                    # AUTO BUY LOGIC
                    if self.config.buy_amount > 0:
                        await self.execute_auto_buy(pool_info)
    
    async def execute_auto_buy(self, pool_info: Dict[str, Any]):
        """
        Laksanakan pembelian automatik
        """
        logger.info(f"🤖 Memulakan Auto Buy untuk {pool_info.get('token_address')}...")
        
        try:
            # 1. Delay (jika ada)
            if hasattr(self.config, 'buy_delay') and self.config.buy_delay > 0:
                logger.info(f"⏳ Menunggu {self.config.buy_delay} saat...")
                await asyncio.sleep(self.config.buy_delay)
            
            # 2. Dapatkan pool keys lengkap
            # Nota: pool_info dari websocket mungkin tak lengkap, perlu fetch on-chain
            pool_address = pool_info.get('pool_address')
            # pool_keys = await self.raydium_swap.get_pool_keys(pool_address)
            
            # Placeholder pool keys (sepatutnya dari get_pool_keys)
            # Untuk demo, kita skip jika tiada keys
            # if not pool_keys:
            #    logger.error("Gagal mendapatkan pool keys")
            #    return

            logger.info("⚠️  Auto Buy: Menunggu implementasi penuh get_pool_keys...")
            # Di sini kita akan panggil:
            # 1. amount_in = self.config.buy_amount * 1e9
            # 2. min_out = calc_min_out(...)
            # 3. ix = build_swap_instruction(...)
            # 4. sig = build_and_send_transaction([ix])
            
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
        # Simplified extraction
        return {
            'token_address': 'Unknown (Parsing needed)',
            'pool_address': 'Unknown (Parsing needed)',
            'timestamp': asyncio.get_event_loop().time()
        }
    
    async def stop_monitoring(self):
        """Hentikan monitoring"""
        self.is_monitoring = False
        await self.client.close()
