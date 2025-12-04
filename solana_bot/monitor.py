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
        logger.info(f"📡 Connecting to WebSocket: {self.ws_endpoint}")
        logger.info(f"🎯 Monitoring Raydium Program: {self.raydium_program_id}")
        
        heartbeat_counter = 0
        last_heartbeat = asyncio.get_event_loop().time()
        
        try:
            async with connect(self.ws_endpoint) as websocket:
                logger.info("🔌 WebSocket connected successfully")
                
                await websocket.logs_subscribe(
                    filter_=RpcTransactionLogsFilterMentions(self.raydium_program_id),
                    commitment=Confirmed
                )
                logger.info("✅ Berjaya subscribe ke Raydium program")
                logger.info("👀 Menunggu transaksi baharu... (Bot sedang aktif)")
                logger.info("💡 Heartbeat akan dipaparkan setiap 30 saat untuk menunjukkan bot masih berjalan")
                
                async for notification in websocket:
                    if not self.is_monitoring:
                        logger.info("🛑 Stop signal received, exiting monitor loop")
                        break
                    
                    # Heartbeat setiap 30 saat
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat >= 30:
                        heartbeat_counter += 1
                        logger.info(f"💓 Heartbeat #{heartbeat_counter} - Bot masih aktif dan memantau...")
                        last_heartbeat = current_time
                    
                    try:
                        logger.debug(f"📨 Received notification: {type(notification)}")
                        await self._process_notification(notification)
                    except Exception as e:
                        logger.error(f"❌ Error memproses notifikasi: {e}", exc_info=True)
                        
        except Exception as e:
            logger.error(f"❌ Error dalam monitoring: {e}", exc_info=True)
        finally:
            self.is_monitoring = False
            logger.info("⏹️  Pemantauan dihentikan")
    
    async def _process_notification(self, notification):
        """Proses notifikasi dari WebSocket"""
        try:
            if hasattr(notification, 'result'):
                result = notification.result
                logger.debug(f"📦 Processing result: {result}")
                
                if self._is_new_pool(result):
                    logger.info("🆕 Potential new pool detected! Extracting info...")
                    pool_info = await self._extract_pool_info(result)
                    
                    if pool_info:
                        logger.info(f"✨ Pool baharu dijumpai!")
                        logger.info(f"   Token: {pool_info.get('token_address')}")
                        logger.info(f"   Pool: {pool_info.get('pool_address')}")
                        logger.info(f"   Base Mint: {pool_info.get('base_mint', 'N/A')}")
                        logger.info(f"   Quote Mint: {pool_info.get('quote_mint', 'N/A')}")
                        
                        # Jalankan callback (untuk UI/Log)
                        if self.callback:
                            await self.callback(pool_info)
                        
                        # AUTO BUY LOGIC
                        if self.config.buy_amount > 0:
                            logger.info(f"🤖 Auto Buy enabled (Amount: {self.config.buy_amount} SOL)")
                            await self.execute_auto_buy(pool_info)
                        else:
                            logger.info("ℹ️  Auto Buy disabled (buy_amount = 0)")
                    else:
                        logger.debug("⚠️  Could not extract pool info from notification")
                else:
                    logger.debug("ℹ️  Not a new pool initialization (regular transaction)")
            else:
                logger.debug(f"⚠️  Notification has no result attribute: {notification}")
        except Exception as e:
            logger.error(f"❌ Error in _process_notification: {e}", exc_info=True)
    
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
            logger.debug(f"🔎 Checking {len(logs)} log entries for pool initialization")
            for log in logs:
                if 'initialize' in log.lower() or 'create' in log.lower():
                    logger.debug(f"✅ Found initialization keyword in log: {log[:100]}...")
                    return True
        return False
    
    async def _extract_pool_info(self, result) -> Optional[Dict[str, Any]]:
        """
        Extract maklumat pool dari result log WebSocket
        Cuba cari 'Program log: ray_log: ...' dan decode
        """
        try:
            if not hasattr(result, 'value'):
                logger.debug("⚠️  Result has no 'value' attribute")
                return None
                
            logs = result.value.logs
            logger.debug(f"📋 Scanning {len(logs)} logs for ray_log data")
            
            for i, log in enumerate(logs):
                if "ray_log:" in log:
                    logger.info(f"🎯 Found ray_log in log entry #{i}")
                    # Format: "Program log: ray_log: <BASE64_DATA>"
                    parts = log.split("ray_log: ")
                    if len(parts) < 2:
                        logger.warning(f"⚠️  ray_log format unexpected: {log[:100]}")
                        continue
                        
                    b64_data = parts[1].strip()
                    logger.debug(f"📦 Base64 data length: {len(b64_data)} chars")
                    pool_data = self._decode_ray_log(b64_data)
                    
                    if pool_data:
                        logger.info("✅ Successfully decoded ray_log data!")
                        return pool_data
                    else:
                        logger.warning("⚠️  Failed to decode ray_log data")
            
            logger.debug("ℹ️  No ray_log found in logs")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting pool info: {e}", exc_info=True)
            return None

    def _decode_ray_log(self, b64_data: str) -> Optional[Dict[str, Any]]:
        """
        Decode data ray_log (Base64) untuk dapatkan AMM ID
        """
        import base64
        import struct
        from solders.pubkey import Pubkey
        
        try:
            data = base64.b64decode(b64_data)
            
            # Semak panjang data. Log init biasanya panjang (sekitar 240+ bytes)
            if len(data) < 100:
                return None
                
            # Struktur Log Init (anggaran offset):
            # u8 log_type (offset 0)
            log_type = data[0]
            
            # Log Type 0 = Init
            if log_type == 0:
                # Offsets berdasarkan Raydium Rust SDK:
                # log_type(1) + open_time(8) + quote_dec(1) + base_dec(1) + 
                # quote_lot(8) + base_lot(8) + quote_amt(8) + base_amt(8) = 43 bytes
                # Kemudian Pubkeys (32 bytes each):
                # market(32) -> offset 43
                # open_orders(32) -> offset 75
                # target_orders(32) -> offset 107
                # base_vault(32) -> offset 139
                # quote_vault(32) -> offset 171
                # withdraw_queue(32) -> offset 203
                # lp_vault(32) -> offset 235
                # amm_id(32) -> offset 267 <-- INI YANG KITA MAHU
                # ...
                
                # Nota: Offset mungkin berbeza sedikit bergantung versi, 
                # tapi urutan biasanya konsisten.
                
                # Mari cuba extract AMM ID di offset 267
                amm_id_offset = 267
                if len(data) >= amm_id_offset + 32:
                    amm_id_bytes = data[amm_id_offset:amm_id_offset+32]
                    amm_id = Pubkey.from_bytes(amm_id_bytes)
                    
                    # Extract Token Mints juga
                    # lp_mint(32) -> 299
                    # base_mint(32) -> 331
                    # quote_mint(32) -> 363
                    
                    base_mint = Pubkey.from_bytes(data[331:363])
                    quote_mint = Pubkey.from_bytes(data[363:395])
                    
                    return {
                        'pool_address': str(amm_id),
                        'token_address': str(quote_mint), # Biasanya quote adalah token baru jika pair dengan SOL (Base)
                        'base_mint': str(base_mint),
                        'quote_mint': str(quote_mint),
                        'timestamp': asyncio.get_event_loop().time()
                    }
                    
            return None
            
        except Exception as e:
            logger.error(f"Error decoding ray log: {e}")
            return None
    
    async def stop_monitoring(self):
        """Hentikan monitoring"""
        self.is_monitoring = False
        await self.client.close()
