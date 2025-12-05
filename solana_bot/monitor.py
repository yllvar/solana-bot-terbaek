"""
Modul untuk monitor pool baharu di Raydium dan Auto Buy

Enhanced with proper pool detection using pool_parser module.
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
from .pool_parser import RaydiumPoolParser, PoolInfo
from .security import SecurityAnalyzer

logger = logging.getLogger(__name__)

class PoolMonitor:
    """Enhanced Raydium pool monitor with proper pool detection"""
    
    def __init__(
        self,
        rpc_endpoint: str,
        ws_endpoint: str,
        raydium_program_id: Pubkey,
        config: BotConfig,
        wallet_manager,
        callback: Optional[Callable] = None,
        security_analyzer: Optional[SecurityAnalyzer] = None
    ):
        self.rpc_endpoint = rpc_endpoint
        self.ws_endpoint = ws_endpoint
        self.raydium_program_id = raydium_program_id
        self.config = config
        self.wallet = wallet_manager
        self.callback = callback
        self.client = AsyncClient(rpc_endpoint)
        self.is_monitoring = False
        
        # Enhanced components
        self.pool_parser = RaydiumPoolParser()
        self.security = security_analyzer
        
        self.raydium_swap = RaydiumSwap(self.client, self.wallet)
        self.tx_builder = TransactionBuilder(self.client, self.wallet)
        
        # Statistics
        self.stats = {
            'transactions_seen': 0,
            'pools_detected': 0,
            'pools_bought': 0,
            'pools_skipped_security': 0
        }
        
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
        """
        Check if result represents a new pool initialization.
        
        Uses pool_parser for accurate detection instead of naive keyword matching.
        """
        self.stats['transactions_seen'] += 1
        
        if not hasattr(result, 'value') or not result.value:
            return False
        
        logs = result.value.logs if hasattr(result.value, 'logs') else []
        
        if not logs:
            return False
        
        # Use pool_parser for accurate detection
        # Check for proper initialize2 instruction, not just keywords
        is_init = self.pool_parser.is_initialize_instruction(logs)
        
        if is_init:
            # Double-check: verify it's actually an init log (type 0)
            is_init = self.pool_parser.filter_init_logs_only(logs)
        
        if is_init:
            logger.debug("✅ Detected pool initialization via pool_parser")
        
        return is_init
    
    async def _extract_pool_info(self, result) -> Optional[Dict[str, Any]]:
        """
        Extract pool info using pool_parser module.
        
        Returns pool info dict or None if extraction fails.
        """
        try:
            if not hasattr(result, 'value'):
                logger.debug("⚠️ Result has no 'value' attribute")
                return None
            
            logs = result.value.logs
            timestamp = asyncio.get_event_loop().time()
            
            # Use pool_parser for structured extraction
            pool_info = self.pool_parser.parse_transaction_logs(logs, timestamp)
            
            if pool_info:
                self.stats['pools_detected'] += 1
                logger.info(f"✅ Pool parsed successfully via pool_parser")
                return pool_info.to_dict()
            
            # Fallback: try legacy extraction if pool_parser fails
            logger.debug("⚠️ pool_parser extraction failed, trying legacy method")
            return await self._extract_pool_info_legacy(logs, timestamp)
            
        except Exception as e:
            logger.error(f"❌ Error extracting pool info: {e}", exc_info=True)
            return None
    
    async def _extract_pool_info_legacy(self, logs, timestamp) -> Optional[Dict[str, Any]]:
        """
        Legacy pool info extraction (fallback).
        
        Kept for compatibility but pool_parser should be preferred.
        """
        import base64
        from solders.pubkey import Pubkey
        
        try:
            for log in logs:
                if "ray_log:" not in log:
                    continue
                
                parts = log.split("ray_log: ")
                if len(parts) < 2:
                    continue
                
                b64_data = parts[1].strip()
                data = base64.b64decode(b64_data)
                
                if len(data) < 100 or data[0] != 0:  # type 0 = init
                    continue
                
                # Try known offsets
                if len(data) >= 395:
                    amm_id = Pubkey.from_bytes(data[267:299])
                    base_mint = Pubkey.from_bytes(data[331:363])
                    quote_mint = Pubkey.from_bytes(data[363:395])
                    
                    return {
                        'pool_address': str(amm_id),
                        'token_address': str(quote_mint),
                        'base_mint': str(base_mint),
                        'quote_mint': str(quote_mint),
                        'timestamp': timestamp
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Legacy extraction failed: {e}")
            return None
    
    async def _run_security_checks(self, pool_info: Dict[str, Any]) -> tuple[bool, list]:
        """
        Run security analysis on detected pool before buying.
        
        Returns (is_safe, warnings)
        """
        if not self.security:
            logger.debug("ℹ️ Security analyzer not configured, skipping checks")
            return True, []
        
        try:
            token_mint = pool_info.get('token_address')
            pool_address = pool_info.get('pool_address')
            
            if not token_mint:
                return False, ["No token address in pool info"]
            
            logger.info(f"🔒 Running security checks for {token_mint[:16]}...")
            
            # Quick check first
            is_safe, warnings = await self.security.quick_check(token_mint, pool_address)
            
            if not is_safe:
                self.stats['pools_skipped_security'] += 1
                logger.warning(f"⚠️ Token failed security check!")
                for w in warnings:
                    logger.warning(f"   {w}")
            else:
                logger.info(f"✅ Token passed security checks")
            
            return is_safe, warnings
            
        except Exception as e:
            logger.error(f"Security check error: {e}")
            return False, [f"Security check failed: {e}"]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        return {
            **self.stats,
            'is_monitoring': self.is_monitoring
        }
    
    async def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.is_monitoring = False
        
        # Log final stats
        logger.info("📊 Monitoring Statistics:")
        logger.info(f"   Transactions seen: {self.stats['transactions_seen']}")
        logger.info(f"   Pools detected: {self.stats['pools_detected']}")
        logger.info(f"   Pools bought: {self.stats['pools_bought']}")
        logger.info(f"   Pools skipped (security): {self.stats['pools_skipped_security']}")
        
        # Cleanup
        if self.security:
            await self.security.close()
        await self.client.close()

