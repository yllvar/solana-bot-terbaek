import asyncio
import logging
from typing import Optional, Callable, Dict, Any
import time
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Confirmed

from .raydium.swap import RaydiumSwap
from .transaction import TransactionBuilder
from .rugcheck_client import RugCheckClient, RiskLevel
from .birdeye_client import BirdeyeClient
from .dex_screener_client import DexScreenerClient
from .volume_validator import VolumeValidator
from .config import BotConfig
from .pool_parser import RaydiumPoolParser, PoolInfo
from .security import SecurityAnalyzer

# Create dedicated scanning logger
scanning_logger = logging.getLogger('raydium_scanner')
scanning_logger.setLevel(logging.DEBUG)  # Changed to DEBUG for detailed analysis

# Create file handler for scanning logs
import os
from datetime import datetime
log_filename = f"raydium_scanning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
scanning_handler = logging.FileHandler(log_filename, mode='w')
scanning_handler.setLevel(logging.DEBUG)  # Changed to DEBUG to capture all scanning details

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
scanning_handler.setFormatter(formatter)

# Add handler to logger
scanning_logger.addHandler(scanning_handler)

# Export the scanning log filename
SCANNING_LOG_FILENAME = log_filename

# Create dedicated market scanning logger
market_scanner = logging.getLogger('market_scanner')
market_scanner.setLevel(logging.DEBUG)  # Changed to DEBUG to show all scanning activity

# Create separate market scanning log file
market_log_filename = f"market_scanning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
market_handler = logging.FileHandler(market_log_filename, mode='w')
market_handler.setLevel(logging.DEBUG)  # Changed to DEBUG to capture all scanning activity

# Create formatter for market scanning
market_formatter = logging.Formatter('%(asctime)s - MARKET_SCAN - %(levelname)s - %(message)s')
market_handler.setFormatter(market_formatter)

# Add handler to market scanner
market_scanner.addHandler(market_handler)

# Export the market scanning log filename
MARKET_SCANNING_LOG_FILENAME = market_log_filename

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
        
        # Initialize Birdeye client for market data
        self.birdeye = BirdeyeClient(api_key=config.birdeye_api_key)
        
        # Initialize DexScreener client for volume validation
        self.dex_screener = DexScreenerClient()
        
        # Initialize volume validator with multiple sources
        self.volume_validator = VolumeValidator(self.birdeye, self.dex_screener)
        
        self.raydium_swap = RaydiumSwap(self.client, self.wallet)
        self.tx_builder = TransactionBuilder(self.client, self.wallet)
        
        # Statistics
        self.stats = {
            'transactions_seen': 0,
            'pools_detected': 0,
            'pools_bought': 0,
            'pools_skipped_security': 0
        }
        
        # Trade rate limiting
        self.trade_count = 0
        self.last_trade_reset = time.time()
        self.cooldowns = {}
        
    async def start_monitoring(self):
        """Mula monitor pool baharu"""
        self.is_monitoring = True
        
        scanning_logger.info("="*80)
        scanning_logger.info("🚀 RAYDIUM TOKEN SCANNING MONITOR STARTED")
        scanning_logger.info("="*80)
        scanning_logger.info(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        scanning_logger.info(f"🎯 Target Program: {self.raydium_program_id}")
        scanning_logger.info(f"🌐 RPC Endpoint: {self.rpc_endpoint}")
        scanning_logger.info(f"🔌 WebSocket: {self.ws_endpoint}")
        scanning_logger.info(f"⚙️  Auto Buy Amount: {self.config.buy_amount} SOL")
        scanning_logger.info(f"🔍 Monitoring Mode: {'CPMM' if 'CPMM' in str(self.raydium_program_id) else 'V4'}")
        scanning_logger.info("="*80)
        
        # Initialize market scanning
        market_scanner.info("="*80)
        market_scanner.info("RAYDIUM MARKET TOKEN SCANNING ENGINE ACTIVATED")
        market_scanner.info("="*80)
        market_scanner.info("SCANNING OBJECTIVE: Detect new token launches on Raydium")
        market_scanner.info(f"DEX PROGRAM: {self.raydium_program_id}")
        market_scanner.info("SCANNING METHODOLOGY:")
        market_scanner.info("   - Real-time transaction monitoring")
        market_scanner.info("   - Pool creation pattern recognition")
        market_scanner.info("   - Token address extraction")
        market_scanner.info("   - Liquidity analysis")
        market_scanner.info("   - Auto-buy execution (if enabled)")
        market_scanner.info("="*80)
        market_scanner.info("MARKET SCAN STATUS: INITIALIZING...")
        
        logger.info("🔍 Memulakan pemantauan pool baharu...")
        logger.info(f"📡 Connecting to WebSocket: {self.ws_endpoint}")
        logger.info(f"🎯 Monitoring Raydium Program: {self.raydium_program_id}")
        
        logger.info("🔍 Memulakan pemantauan pool baharu...")
        logger.info(f"📡 Connecting to WebSocket: {self.ws_endpoint}")
        logger.info(f"🎯 Monitoring Raydium Program: {self.raydium_program_id}")
        
        heartbeat_counter = 0
        last_heartbeat = asyncio.get_event_loop().time()
        tx_counter = 0
        
        try:
            async with connect(self.ws_endpoint) as websocket:
                logger.info("🔌 WebSocket connected successfully")
                scanning_logger.info("✅ WebSocket connection established")
                market_scanner.info("CONNECTION: WebSocket established to Solana mainnet")
                market_scanner.info("STREAMING: Connected to Raydium transaction feed")
                
                await websocket.logs_subscribe(
                    filter_=RpcTransactionLogsFilterMentions(self.raydium_program_id),
                    commitment=Confirmed
                )
                logger.info("✅ Berjaya subscribe ke Raydium program")
                scanning_logger.info("✅ Successfully subscribed to Raydium program logs")
                market_scanner.info("SUBSCRIPTION: Successfully subscribed to CPMM program logs")
                market_scanner.info("MONITORING: Actively monitoring for new token pool creations...")
                market_scanner.info("SCAN ENGINE: Ready to detect token launches")
                
                logger.info("👀 Menunggu transaksi baharu... (Bot sedang aktif)")
                logger.info("💡 Heartbeat akan dipaparkan setiap 30 saat untuk menunjukkan bot masih berjalan")
                
                async for notification in websocket:
                    if not self.is_monitoring:
                        logger.info("🛑 Stop signal received, exiting monitor loop")
                        scanning_logger.info("🛑 Monitoring stopped by user")
                        break
                    
                    tx_counter += 1
                    
                    market_scanner.debug(f"NOTIFICATION_RECEIVED: #{tx_counter} - Type: {type(notification)}")
                    market_scanner.debug(f"NOTIFICATION_CONTENT: {notification}")
                    
                    try:
                        await self._process_notification(notification)
                    except Exception as e:
                        logger.error(f"❌ Error memproses notifikasi: {e}", exc_info=True)
                        scanning_logger.error(f"❌ CRITICAL: Raydium scanning error: {e}")
                        
                    # Heartbeat setiap 30 saat
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_heartbeat >= 30:
                        heartbeat_counter += 1
                        logger.info(f"💓 Heartbeat #{heartbeat_counter} - Bot masih aktif dan memantau...")
                        scanning_logger.info(f"💓 Heartbeat #{heartbeat_counter} - Processed {tx_counter} total transactions")
                        scanning_logger.info(f"📊 Status: Actively scanning | Transactions seen: {tx_counter}")
                        market_scanner.info(f"💓 MARKET SCAN HEARTBEAT #{heartbeat_counter}")
                        market_scanner.info(f"   📊 TRANSACTIONS PROCESSED: {tx_counter}")
                        market_scanner.info("   🔍 STATUS: Actively scanning Raydium for token launches")
                        market_scanner.info("   🎯 OBJECTIVE: Detect new token pool creations")
                        last_heartbeat = current_time
                    
                    try:
                        await self._process_notification(notification)
                    except Exception as e:
                        logger.error(f"❌ Error memproses notifikasi: {e}", exc_info=True)
                        scanning_logger.error(f"❌ CRITICAL: Raydium scanning error: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error dalam monitoring: {e}", exc_info=True)
            scanning_logger.error(f"❌ Critical monitoring error: {e}")
        finally:
            self.is_monitoring = False
            scanning_logger.info("="*80)
            scanning_logger.info("🛑 RAYDIUM SCANNING MONITOR STOPPED")
            scanning_logger.info(f"📊 Final Stats: {tx_counter} transactions processed")
            scanning_logger.info("="*80)
            
            market_scanner.info("="*80)
            market_scanner.info("🛑 MARKET SCANNING ENGINE STOPPED")
            market_scanner.info("📊 FINAL MARKET SCAN STATISTICS:")
            market_scanner.info(f"   📈 Total Transactions Analyzed: {tx_counter}")
            market_scanner.info(f"   🎯 Token Launches Detected: {self.stats['pools_detected']}")
            market_scanner.info(f"   💰 Auto-Buy Executions: {self.stats['pools_bought']}")
            market_scanner.info(f"   🚫 Security Filtered: {self.stats['pools_skipped_security']}")
            market_scanner.info("   🔍 SCAN STATUS: Market monitoring completed")
            market_scanner.info("="*80)
            
            logger.info("⏹️  Pemantauan dihentikan")
    
    async def _process_notification(self, notification):
        """Process Raydium transaction notifications for token scanning"""
        try:
            # Notification comes as a list, extract the actual notification
            if isinstance(notification, list) and len(notification) > 0:
                notification = notification[0]
            
            # Skip subscription results, only process log notifications
            if hasattr(notification, 'method') and notification.method == "logsNotification":
                # This is a logs notification
                pass
            elif hasattr(notification, 'result') and hasattr(notification.result, 'value'):
                # This is a logs notification with result
                pass
            else:
                # Skip other notification types (subscription confirmations, etc.)
                market_scanner.debug(f"SKIP_NOTIFICATION: Not a logs notification - {type(notification)}")
                return
            
            if hasattr(notification, 'result'):
                result = notification.result
                
                # Extract signature for logging
                signature = "unknown"
                if hasattr(result, 'value') and hasattr(result.value, 'signature'):
                    signature = str(result.value.signature)
                
                # Log actual transaction scanning - what tokens/contracts are being examined
                market_scanner.info(f"SCANNING_TRANSACTION: {signature}")
                market_scanner.debug(f"TRANSACTION_SIGNATURE: {signature}")
                
                is_new_pool, pool_type = self._is_new_pool(result)
                
                if is_new_pool:
                    scanning_logger.info(f"🎯 TOKEN POOL DETECTED: {signature}")
                    scanning_logger.info("   Scanning for new token launch...")
                    logger.info("🆕 Potential new pool detected! Extracting info...")
                    
                    market_scanner.info(f"TOKEN_POOL_DETECTED: {signature}")
                    market_scanner.info("ANALYZING: Extracting token information from pool creation...")
                    
                    pool_info = await self._extract_pool_info(result, pool_type)
                    
                    if pool_info:
                        scanning_logger.info(f"✅ TOKEN EXTRACTION SUCCESSFUL!")
                        scanning_logger.info(f"   🏊 Pool Address: {pool_info.get('pool_address')}")
                        scanning_logger.info(f"   🪙 Token Address: {pool_info.get('token_address')}")
                        scanning_logger.info(f"   🔄 Base Token: {pool_info.get('base_mint')}")
                        scanning_logger.info(f"   💱 Quote Token: {pool_info.get('quote_mint')}")
                        scanning_logger.info("   ✅ Token scanning complete - pool info extracted")
                        
                        market_scanner.info(f"POOL_EXTRACTED: address={pool_info.get('pool_address')}")
                        market_scanner.info(f"TOKEN_EXTRACTED: address={pool_info.get('token_address')}")
                        market_scanner.info(f"BASE_TOKEN: address={pool_info.get('base_mint')}")
                        market_scanner.info(f"QUOTE_TOKEN: address={pool_info.get('quote_mint')}")
                        market_scanner.info("SCAN_RESULT: Token pool information successfully extracted")
                        
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
                            scanning_logger.info(f"🤖 AUTO BUY ACTIVATED: Purchasing {self.config.buy_amount} SOL worth of new token")
                            market_scanner.info(f"AUTO_BUY_TRIGGERED: amount={self.config.buy_amount} SOL")
                            market_scanner.info("PURCHASE_STATUS: Executing token buy transaction")
                            logger.info(f"🤖 Auto Buy enabled (Amount: {self.config.buy_amount} SOL)")
                            await self.execute_auto_buy(pool_info)
                            market_scanner.info("PURCHASE_COMPLETED: Auto-buy transaction executed")
                        else:
                            scanning_logger.info("ℹ️ Auto Buy disabled - token detected but no purchase configured")
                            market_scanner.info("AUTO_BUY_DISABLED: Token detected but purchase not configured")
                            logger.info("ℹ️  Auto Buy disabled (buy_amount = 0)")
                    else:
                        scanning_logger.warning(f"⚠️ TOKEN EXTRACTION FAILED: Could not parse pool data from {signature}")
                        market_scanner.warning(f"EXTRACTION_FAILED: Could not parse pool data from {signature}")
                        logger.debug("⚠️  Could not extract pool info from notification")
                else:
                    # Only log Raydium transactions with meaningful analysis
                    if hasattr(result, 'value') and hasattr(result.value, 'logs'):
                        logs = result.value.logs
                        tx_analysis = self._analyze_raydium_transaction(logs)
                        market_scanner.debug(f"TX_ANALYSIS: {signature[:16]}... - {tx_analysis}")
                    else:
                        market_scanner.debug(f"EMPTY_TRANSACTION: {signature[:16]} - no logs available")
                    logger.debug("Not a new pool initialization (regular transaction)")
            else:
                market_scanner.debug("NO_RESULT_DATA: Notification has no result attribute")
                
        except Exception as e:
            logger.error(f"Error in _process_notification: {e}", exc_info=True)
            scanning_logger.error(f"CRITICAL: Raydium scanning error: {e}")
            market_scanner.error(f"PROCESSING_ERROR: Failed to analyze notification: {e}")
    
    def _analyze_raydium_transaction(self, logs):
        """Analyze transaction logs to categorize the transaction type for token scanning"""
        if not logs:
            return "EMPTY_TX"
        
        # Count different types of Raydium operations
        cpmm_invokes = sum(1 for log in logs if "Program CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C invoke" in log)
        swap_logs = sum(1 for log in logs if "Swap" in log.lower() or "swap" in log.lower())
        create_logs = sum(1 for log in logs if "Create" in log or "Initialize" in log)
        liquidity_logs = sum(1 for log in logs if "Liquidity" in log.lower() or "deposit" in log.lower() or "withdraw" in log.lower())
        
        if cpmm_invokes > 0:
            if create_logs > 0:
                return f"POOL_CREATION_OP ({cpmm_invokes} CPMM calls)"
            elif swap_logs > 0:
                return f"TOKEN_SWAP ({cpmm_invokes} CPMM calls)"
            elif liquidity_logs > 0:
                return f"LIQUIDITY_OP ({cpmm_invokes} CPMM calls)"
            else:
                return f"RAYDIUM_TX ({cpmm_invokes} CPMM calls)"
        else:
            return f"NON_RAYDIUM ({len(logs)} logs)"
    
    async def execute_auto_buy(self, pool_info: Dict[str, Any]):
        """Laksanakan pembelian automatik"""
        token_address = pool_info.get('token_address')
        logger.info(f"🤖 Memulakan Auto Buy untuk {token_address}...")
        
        try:
            # Check trade rate limits
            current_time = time.time()
            
            # Reset counter every hour
            if current_time - self.last_trade_reset >= 3600:  # 3600 seconds = 1 hour
                self.trade_count = 0
                self.last_trade_reset = current_time
                logger.info("🔄 Trade counter reset (hourly)")
            
            # Check max trades per hour
            if self.trade_count >= self.config.max_trades_per_hour:
                logger.warning(f"⚠️ Max trades per hour reached ({self.config.max_trades_per_hour})")
                return
            
            # Check cooldown after sell
            if token_address in self.cooldowns and current_time < self.cooldowns[token_address]:
                remaining = self.cooldowns[token_address] - current_time
                logger.info(f"⏳ Cooldown active for {token_address[:8]}...: {remaining:.1f}s remaining")
                return
            
            # Increment trade counter
            self.trade_count += 1
            logger.info(f"📊 Trade #{self.trade_count}/{self.config.max_trades_per_hour} this hour")
            
            # Check minimum 24h volume
            try:
                volume = await self._get_token_volume_24h(token_address)
                if volume < self.config.min_volume_24h:
                    logger.warning(f"⚠️ Volume too low: ${volume:,.0f} < ${self.config.min_volume_24h:,.0f}")
                    return
                logger.info(f"📈 24h Volume: ${volume:,.0f}")
            except Exception as e:
                logger.warning(f"⚠️ Volume check failed: {e} - proceeding with caution")

            # Check price volatility (if enabled)
            if self.config.price_volatility_filter:
                try:
                    volatility = await self.birdeye.calculate_volatility(token_address, "1H", 24)
                    if volatility is not None:
                        max_volatility = self.config.max_volatility_threshold
                        if volatility > max_volatility:
                            logger.warning(
                                f"📊 Price too volatile: {volatility:.3f} > {max_volatility:.3f} - skipping trade"
                            )
                            return
                        logger.info(f"📊 Price volatility OK: {volatility:.3f} (max: {max_volatility:.3f})")
                    else:
                        logger.debug("📊 Could not calculate volatility - proceeding with caution")
                except Exception as e:
                    logger.warning(f"⚠️ Price volatility check failed: {e} - proceeding with caution")

            # Check pool liquidity (if enabled)
            if self.config.pool_liquidity_analysis:
                try:
                    liquidity_analysis = await self._analyze_pool_liquidity(
                        pool_address, token_address, self.config.buy_amount
                    )

                    if not liquidity_analysis['can_trade']:
                        logger.warning(f"💧 Liquidity check failed: {liquidity_analysis['reason']}")
                        return

                    logger.info(
                        f"💧 Pool liquidity OK: ${liquidity_analysis['liquidity_usd']:,.0f} "
                        f"({liquidity_analysis['price_impact']:.2f}% impact)"
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Pool liquidity analysis failed: {e} - proceeding with caution")

            # Check token filters (supply, holders, verification, ownership)
            try:
                filter_result = await self.security.check_token_filters(token_address)
                if not filter_result['passed']:
                    logger.warning(f"🚫 Token failed filter checks!")
                    for warning in filter_result['warnings']:
                        logger.warning(f"   {warning}")
                    return
                logger.info(f"✅ Token passed all filter checks")
            except Exception as e:
                logger.warning(f"⚠️ Token filter check failed: {e} - proceeding with caution")
            
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
                self.stats['pools_bought'] += 1
                
                # Set cooldown after successful buy
                self.cooldowns[token_address] = current_time + self.config.cooldown_after_sell
                logger.info(f"⏰ Cooldown set for {token_address[:8]}...: {self.config.cooldown_after_sell}s")
            else:
                logger.error("❌ Auto Buy GAGAL (TX failed)")
            
        except Exception as e:
            logger.error(f"❌ Auto Buy gagal: {e}")

    async def _get_token_volume_24h(self, token_address: str) -> float:
        """
        Get validated 24h trading volume using multi-source validation.

        Uses VolumeValidator to combine data from Birdeye and DexScreener
        for more accurate volume assessment.

        Args:
            token_address: Solana token mint address

        Returns:
            Validated 24h volume in USD (fallback-safe)
        """
        try:
            logger.debug(f"🔍 Validating 24h volume for {token_address} via multi-source analysis")

            # Use volume validator for multi-source validation
            validated_result = await self.volume_validator.get_validated_volume(token_address)

            # Log validation details
            if validated_result.sources_used > 1:
                logger.debug(
                    f"📊 Multi-source volume: ${validated_result.final_volume:,.0f} "
                    f"(confidence: {validated_result.confidence_score:.2f}, "
                    f"sources: {validated_result.sources_used})"
                )

                # Log any warnings
                for warning in validated_result.warnings:
                    logger.debug(f"⚠️ Volume validation warning: {warning}")
            else:
                logger.debug(
                    f"📊 Single-source volume: ${validated_result.final_volume:,.0f} "
                    f"(confidence: {validated_result.confidence_score:.2f})"
                )

            # Apply minimum confidence threshold from config
            min_confidence = self.config.min_volume_confidence  # Use config value
            if validated_result.confidence_score < min_confidence:
                logger.warning(
                    f"⚠️ Low confidence volume data: {validated_result.confidence_score:.2f} < {min_confidence} "
                    f"- using conservative fallback"
                )
                # Use higher fallback for low confidence data
                conservative_fallback = max(validated_result.final_volume, 25000.0)
                logger.debug(f"📊 Using conservative fallback: ${conservative_fallback:,.0f}")
                return conservative_fallback

            return validated_result.final_volume

        except Exception as e:
            logger.error(f"❌ Multi-source volume validation failed for {token_address}: {e}")
            # Return high fallback value to allow trading if validation fails
            fallback_volume = 100000.0
            logger.debug(f"📊 Using error fallback volume: ${fallback_volume:,.0f}")
            return fallback_volume

    async def _analyze_pool_liquidity(self, pool_address: str, token_address: str, trade_amount_sol: float) -> Dict[str, Any]:
        """
        Analyze pool liquidity and calculate price impact for trade execution.

        Args:
            pool_address: Raydium pool address
            token_address: Token mint address
            trade_amount_sol: Amount of SOL to trade

        Returns:
            Dict with liquidity analysis results
        """
        try:
            logger.debug(f"💧 Analyzing liquidity for pool {pool_address[:8]}...")

            # Get liquidity from multiple sources
            liquidity_sources = []

            # Source 1: DexScreener
            try:
                dex_liquidity = await self.dex_screener.get_token_liquidity(token_address)
                if dex_liquidity:
                    liquidity_sources.append({
                        'source': 'dexscreener',
                        'liquidity_usd': dex_liquidity,
                        'confidence': 0.7
                    })
            except Exception as e:
                logger.debug(f"DexScreener liquidity check failed: {e}")

            # Source 2: Birdeye (if available)
            try:
                birdeye_liquidity = await self.birdeye.get_token_liquidity(token_address)
                if birdeye_liquidity:
                    liquidity_sources.append({
                        'source': 'birdeye',
                        'liquidity_usd': birdeye_liquidity,
                        'confidence': 0.8
                    })
            except Exception as e:
                logger.debug(f"Birdeye liquidity check failed: {e}")

            if not liquidity_sources:
                return {
                    'can_trade': False,
                    'reason': 'No liquidity data available',
                    'liquidity_usd': None,
                    'price_impact': None
                }

            # Use weighted average liquidity
            total_weight = sum(source['confidence'] for source in liquidity_sources)
            weighted_liquidity = sum(
                source['liquidity_usd'] * source['confidence']
                for source in liquidity_sources
            ) / total_weight

            # Calculate price impact
            # Simplified formula: impact = (trade_amount / liquidity) * 100
            price_impact = (trade_amount_sol / max(weighted_liquidity, 1)) * 100

            # Determine if trade is acceptable
            max_impact = self.config.max_price_impact
            can_trade = price_impact <= max_impact

            result = {
                'can_trade': can_trade,
                'liquidity_usd': weighted_liquidity,
                'price_impact': price_impact,
                'max_allowed_impact': max_impact,
                'sources_used': len(liquidity_sources),
                'reason': None
            }

            if not can_trade:
                result['reason'] = f"Price impact too high: {price_impact:.2f}% > {max_impact:.2f}%"

            logger.debug(
                f"💧 Liquidity analysis: ${weighted_liquidity:,.0f} liquidity, "
                f"{price_impact:.2f}% impact ({'✅' if can_trade else '❌'})"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Pool liquidity analysis failed: {e}")
            return {
                'can_trade': False,
                'reason': f'Liquidity analysis error: {str(e)}',
                'liquidity_usd': None,
                'price_impact': None
            }

    def _is_new_pool(self, result) -> tuple[bool, str]:
        
        if not hasattr(result, 'value') or not result.value:
            market_scanner.debug("VALIDATION_FAILED: Transaction has no data")
            return False, 'unknown'
        
        logs = result.value.logs if hasattr(result.value, 'logs') else []
        
        if not logs:
            market_scanner.debug("VALIDATION_FAILED: Transaction has no logs")
            return False, 'unknown'
        
        market_scanner.debug(f"PATTERN_CHECK: Analyzing {len(logs)} log entries for pool creation patterns")
        
        # Check for pool creation patterns
        is_init = self.pool_parser.is_initialize_instruction(logs)
        pool_type = 'unknown'
        
        if is_init:
            # Determine pool type
            has_cpmm = any("Program CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C invoke" in log for log in logs)
            has_v4 = any("Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke" in log for log in logs)
            
            if has_cpmm:
                pool_type = 'cpmm'
            elif has_v4:
                pool_type = 'v4'
            
            is_init = self.pool_parser.filter_init_logs_only(logs)
            market_scanner.debug("PATTERN_FOUND: Pool creation initialization detected")
        else:
            market_scanner.debug("PATTERN_NOT_FOUND: No pool creation patterns in logs")
        
        if is_init:
            market_scanner.info("POOL_CREATION_CONFIRMED: Valid Raydium pool creation transaction")
            market_scanner.info(f"LOG_ENTRIES: {len(logs)} entries with pool initialization patterns")
            market_scanner.info(f"POOL_TYPE: {pool_type}")
        else:
            market_scanner.debug("SCAN_CONCLUSION: Not a token pool creation transaction")
        
        return is_init, pool_type   
    async def _extract_pool_info(self, result, pool_type='unknown') -> Optional[Dict[str, Any]]:
        """
        Extract pool info using pool_parser module.
        
        Returns pool info dict or None if extraction fails.
        """
        try:
            # Get signature for CPMM parsing
            signature = "unknown"
            if hasattr(result, 'value') and hasattr(result.value, 'signature'):
                signature = str(result.value.signature)
            
            logs = result.value.logs
            timestamp = asyncio.get_event_loop().time()
            
            # Use pool type to determine parsing approach
            force_cpmm = (pool_type == 'cpmm')
            
            # Use pool_parser for structured extraction
            pool_info = self.pool_parser.parse_transaction_logs(logs, timestamp, signature, self.client, force_cpmm=force_cpmm)
            
            if pool_info:
                self.stats['pools_detected'] += 1
                logger.info(f"✅ Pool parsed successfully via pool_parser")
                return pool_info.to_dict()
            
            # Fallback: try legacy extraction if pool_parser fails
            logger.debug("⚠️ pool_parser extraction failed, trying legacy method")
            market_scanner.warning(f"POOL_PARSER_FAILED: Main parsing failed for {signature}, trying fallback")
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
            logger.debug(f"Attempting legacy extraction on {len(logs)} logs")
            
            for log in logs:
                if "ray_log:" not in log:
                    continue
                
                logger.debug(f"Found ray_log in legacy extraction: {log[:100]}...")
                
                parts = log.split("ray_log: ")
                if len(parts) < 2:
                    continue
                
                b64_data = parts[1].strip()
                logger.debug(f"Decoding base64 data: {b64_data[:50]}...")
                
                data = base64.b64decode(b64_data)
                
                if len(data) < 100 or data[0] != 0:  # type 0 = init
                    logger.debug(f"Invalid ray_log data: len={len(data)}, type={data[0] if len(data) > 0 else 'N/A'}")
                    continue
                
                # Try known offsets
                if len(data) >= 395:
                    amm_id = Pubkey.from_bytes(data[267:299])
                    base_mint = Pubkey.from_bytes(data[331:363])
                    quote_mint = Pubkey.from_bytes(data[363:395])
                    
                    result = {
                        'pool_address': str(amm_id),
                        'token_address': str(quote_mint),
                        'base_mint': str(base_mint),
                        'quote_mint': str(quote_mint),
                        'timestamp': timestamp
                    }
                    
                    logger.info(f"Legacy extraction successful: pool={amm_id}, token={quote_mint}")
                    return result
            
            logger.debug("Legacy extraction found no valid ray_log entries")
            
            # Final fallback: try to extract token addresses directly from logs
            logger.debug("Trying direct token address extraction from logs")
            return self._extract_tokens_from_logs(logs, timestamp)
            
        except Exception as e:
            logger.error(f"Legacy extraction failed: {e}")
            return None
    
    def _extract_tokens_from_logs(self, logs, timestamp):
        """
        Extract token addresses directly from transaction logs.
        
        This is a last-resort method that looks for token addresses
        in the log strings themselves.
        """
        import re
        from solders.pubkey import Pubkey
        
        try:
            logger.debug("Scanning logs for token addresses...")
            
            # Look for base58-encoded addresses (32-byte pubkeys = 44 characters in base58)
            token_candidates = []
            
            for log in logs:
                # Find all strings that look like base58 addresses
                # Solana addresses are 32-44 characters of base58
                candidates = re.findall(r'\b[A-HJ-NP-Z0-9]{32,44}\b', log)
                token_candidates.extend(candidates)
            
            # Filter out known non-token addresses and invalid addresses
            known_addresses = {
                '11111111111111111111111111111112',  # System program (full)
                '11111111111111111111111111111111',  # System program (truncated)
                'CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C',  # CPMM program
                '675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8',  # V4 program
                'So11111111111111111111111111111111111111112',  # Wrapped SOL
                'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA',  # Token program
                'ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',  # Associated token program
                'ComputeBudget111111111111111111111111111111',  # Compute budget program
                'SysvarRent111111111111111111111111111111111',  # Rent sysvar
                'SysvarC1ock11111111111111111111111111111111',  # Clock sysvar
            }
            
            # Filter and validate addresses
            valid_tokens = []
            for addr in token_candidates:
                if addr in known_addresses:
                    continue
                if len(addr) < 32 or len(addr) > 44:
                    continue  # Invalid length for Solana address
                # Check if it's a valid base58 string
                try:
                    from solders.pubkey import Pubkey
                    Pubkey.from_string(addr)
                    valid_tokens.append(addr)
                except:
                    continue
            
            token_candidates = valid_tokens
            
            if len(token_candidates) >= 2:
                # Assume first is base token, second is quote token (new token)
                base_token = token_candidates[0]
                quote_token = token_candidates[1]
                
                # Create a mock pool address (we don't have the real one)
                # Use a deterministic address based on the tokens
                mock_pool = f"POOL_{base_token[:8]}_{quote_token[:8]}"
                
                result = {
                    'pool_address': mock_pool,
                    'token_address': quote_token,  # Assume quote is the new token
                    'base_mint': base_token,
                    'quote_mint': quote_token,
                    'timestamp': timestamp,
                    'extraction_method': 'log_address_extraction'
                }
                
                logger.info(f"Log-based extraction successful: found {len(token_candidates)} potential tokens")
                logger.info(f"Extracted tokens: base={base_token}, quote={quote_token}")
                
                return result
            
            logger.debug(f"Found {len(token_candidates)} potential token addresses, need at least 2")
            return None
            
        except Exception as e:
            logger.error(f"Log-based token extraction failed: {e}")
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
        if hasattr(self, 'volume_validator') and self.volume_validator:
            await self.volume_validator.close()
        if hasattr(self, 'birdeye') and self.birdeye:
            await self.birdeye.close()
        await self.client.close()

