"""
Modul pengurusan trigger dagangan (Take Profit / Stop Loss)
"""
import logging
import asyncio
import time
from typing import Dict, Optional, Any
from .price_tracker import PriceTracker
from .raydium.swap import RaydiumSwap
from .transaction import TransactionBuilder

logger = logging.getLogger(__name__)

class TradeTriggers:
    """Kelas untuk menguruskan Take Profit dan Stop Loss"""
    
    def __init__(
        self,
        price_tracker: PriceTracker,
        raydium_swap: RaydiumSwap,
        transaction_builder: TransactionBuilder,
        wallet,
        config=None
    ):
        self.price_tracker = price_tracker
        self.raydium = raydium_swap
        self.tx_builder = transaction_builder
        self.wallet = wallet
        self.config = config
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.triggers: Dict[str, Dict[str, Any]] = {}
        
    def open_position(
        self,
        token_mint: str,
        entry_price: float,
        amount_token: float,
        cost_sol: float,
        pool_address: str
    ):
        """Rekod posisi baharu"""
        self.positions[token_mint] = {
            'entry_price': entry_price,
            'amount': amount_token,
            'cost_sol': cost_sol,
            'entry_time': time.time(),
            'highest_price': entry_price,
            'pool_address': pool_address
        }
        logger.info(f"📈 Posisi dibuka: {token_mint} @ {entry_price:.6f} SOL")
        
    def set_triggers(
        self,
        token_mint: str,
        take_profit_pct: float,
        stop_loss_pct: float
    ):
        """Tetapkan trigger TP/SL"""
        self.triggers[token_mint] = {
            'take_profit': take_profit_pct,
            'stop_loss': stop_loss_pct,
            'enabled': True
        }
        logger.info(f"🎯 Triggers set: TP +{take_profit_pct}%, SL -{stop_loss_pct}%")
        self.price_tracker.register_callback(token_mint, self.check_triggers)

    async def check_triggers(self, token_mint: str, current_price: float, old_price: float):
        """Semak jika trigger perlu dilaksanakan"""
        if token_mint not in self.positions or token_mint not in self.triggers:
            return
            
        position = self.positions[token_mint]
        triggers = self.triggers[token_mint]
        
        if not triggers['enabled']:
            return
            
        if current_price > position['highest_price']:
            position['highest_price'] = current_price
            
        entry_price = position['entry_price']
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Check Trailing Stop first (before TP/SL to lock in profits)
        if self.config and self.config.enable_trailing_stop:
            trailing_stop_price = position['highest_price'] * (1 - self.config.trailing_stop_percentage/100)
            if current_price <= trailing_stop_price:
                pnl_from_peak = ((current_price - position['highest_price']) / position['highest_price']) * 100
                logger.info(f"🚀 TRAILING STOP ACTIVATED! Price: {current_price:.6f}, Peak: {position['highest_price']:.6f}, P&L from peak: {pnl_from_peak:.2f}%")
                await self.execute_sell(token_mint, "TRAILING_STOP", current_price)
                return
        
        # Check Max Hold Time
        if self.config and self.config.max_hold_time_hours > 0:
            current_time = time.time()
            hold_hours = (current_time - position['entry_time']) / 3600
            if hold_hours >= self.config.max_hold_time_hours:
                logger.info(f"⏰ MAX HOLD TIME REACHED! Holding for {hold_hours:.2f} hours (max: {self.config.max_hold_time_hours})")
                await self.execute_sell(token_mint, "MAX_HOLD_TIME", current_price)
                return
        
        if pnl_pct >= triggers['take_profit']:
            logger.info(f"🚀 TAKE PROFIT DICAPAI! P&L: +{pnl_pct:.2f}%")
            await self.execute_sell(token_mint, "TAKE_PROFIT", current_price)
            return
            
        if pnl_pct <= -triggers['stop_loss']:
            logger.warning(f"🛑 STOP LOSS DICAPAI! P&L: {pnl_pct:.2f}%")
            await self.execute_sell(token_mint, "STOP_LOSS", current_price)
            return

    async def execute_sell(self, token_mint: str, reason: str, price: float):
        """Laksanakan jualan automatik"""
        logger.info(f"💸 Melaksanakan jualan automatik ({reason})...")
        
        if token_mint in self.triggers:
            self.triggers[token_mint]['enabled'] = False
            
        try:
            position = self.positions.get(token_mint)
            if not position:
                return

            pool_address = position['pool_address']
            amount_in = int(position['amount']) # Jumlah token untuk dijual
            
            # 1. Dapatkan pool keys
            pool_keys = await self.raydium.get_pool_keys(pool_address)
            if not pool_keys:
                logger.error("Gagal mendapatkan pool keys untuk jualan")
                return

            # 2. Kira min amount out (SOL)
            # Fetch reserves dulu untuk kira expected out
            # (Simplified: kita anggap price tracker dah update reserves, atau fetch baru)
            # Untuk sell: Token -> SOL (Base -> Quote atau sebaliknya bergantung pair)
            # Biasanya SOL adalah Quote (WSOL). Jadi Token (Base) -> SOL (Quote).
            
            # Kita perlu tahu yang mana satu token kita.
            # Jika token_mint == base_mint, maka kita jual Base -> Quote.
            # Jika token_mint == quote_mint, maka kita jual Quote -> Base.
            
            is_base_to_quote = True
            if str(pool_keys['quote_mint']) == token_mint:
                is_base_to_quote = False # Quote -> Base (Jual SOL beli Token? Tak logik untuk sell)
                # Biasanya pair adalah Token/SOL. Jadi Token = Base, SOL = Quote.
            
            # Placeholder calculation
            expected_out = int(amount_in * price * 1e9) # Anggaran kasar
            min_amount_out = self.raydium.calculate_min_amount_out(expected_out, 100) # 1% slippage default
            
            # 3. Dapatkan akaun token
            owner = self.wallet.keypair.pubkey()
            token_account_in = self.raydium.get_associated_token_address(owner, pool_keys['base_mint'])
            token_account_out = self.raydium.get_associated_token_address(owner, pool_keys['quote_mint'])
            
            # 4. Bina swap instruction
            swap_ix = self.raydium.build_swap_instruction(
                pool_keys,
                amount_in,
                min_amount_out,
                token_account_in,
                token_account_out,
                owner
            )
            
            # 5. Hantar transaksi
            signature = await self.tx_builder.build_and_send_transaction([swap_ix])
            
            if signature:
                logger.info(f"✅ Jualan berjaya! ({reason}) TX: {signature}")
                # Tutup posisi
                if token_mint in self.positions:
                    del self.positions[token_mint]
                self.price_tracker.stop_tracking(token_mint)
            else:
                logger.error("❌ Jualan gagal (TX failed)")
                self.triggers[token_mint]['enabled'] = True # Re-enable trigger
                
        except Exception as e:
            logger.error(f"❌ Error executing sell: {e}")
            self.triggers[token_mint]['enabled'] = True
