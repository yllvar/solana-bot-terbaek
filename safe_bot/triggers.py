"""
Modul pengurusan trigger dagangan (Take Profit / Stop Loss)
"""
import logging
import asyncio
import time
from typing import Dict, Optional, Any
from .price_tracker import PriceTracker
from .raydium.swap import RaydiumSwap

logger = logging.getLogger(__name__)

class TradeTriggers:
    """Kelas untuk menguruskan Take Profit dan Stop Loss"""
    
    def __init__(
        self,
        price_tracker: PriceTracker,
        raydium_swap: RaydiumSwap
    ):
        self.price_tracker = price_tracker
        self.raydium = raydium_swap
        self.positions: Dict[str, Dict[str, Any]] = {} # Info posisi aktif
        self.triggers: Dict[str, Dict[str, Any]] = {}  # Tetapan trigger
        
    def open_position(
        self,
        token_mint: str,
        entry_price: float,
        amount_token: float,
        cost_sol: float
    ):
        """
        Rekod posisi baharu
        
        Args:
            token_mint: Alamat mint token
            entry_price: Harga beli (SOL)
            amount_token: Jumlah token
            cost_sol: Kos total dalam SOL
        """
        self.positions[token_mint] = {
            'entry_price': entry_price,
            'amount': amount_token,
            'cost_sol': cost_sol,
            'entry_time': time.time(),
            'highest_price': entry_price # Untuk trailing stop (future)
        }
        logger.info(f"📈 Posisi dibuka: {token_mint} @ {entry_price:.6f} SOL")
        
    def set_triggers(
        self,
        token_mint: str,
        take_profit_pct: float,
        stop_loss_pct: float
    ):
        """
        Tetapkan trigger TP/SL
        
        Args:
            token_mint: Token mint
            take_profit_pct: Peratus keuntungan (cth: 100.0 = 2x)
            stop_loss_pct: Peratus kerugian (cth: 50.0 = -50%)
        """
        self.triggers[token_mint] = {
            'take_profit': take_profit_pct,
            'stop_loss': stop_loss_pct,
            'enabled': True
        }
        logger.info(f"🎯 Triggers set: TP +{take_profit_pct}%, SL -{stop_loss_pct}%")
        
        # Daftar callback ke price tracker
        self.price_tracker.register_callback(token_mint, self.check_triggers)

    async def check_triggers(self, token_mint: str, current_price: float, old_price: float):
        """
        Semak jika trigger perlu dilaksanakan
        """
        if token_mint not in self.positions or token_mint not in self.triggers:
            return
            
        position = self.positions[token_mint]
        triggers = self.triggers[token_mint]
        
        if not triggers['enabled']:
            return
            
        # Update highest price (untuk kegunaan masa depan)
        if current_price > position['highest_price']:
            position['highest_price'] = current_price
            
        # Kira P&L
        entry_price = position['entry_price']
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Log status (sekali-sekala)
        # logger.debug(f"P&L {token_mint}: {pnl_pct:.2f}% (Harga: {current_price:.6f})")
        
        # Check Take Profit
        if pnl_pct >= triggers['take_profit']:
            logger.info(f"🚀 TAKE PROFIT DICAPAI! P&L: +{pnl_pct:.2f}%")
            await self.execute_sell(token_mint, "TAKE_PROFIT", current_price)
            return
            
        # Check Stop Loss
        if pnl_pct <= -triggers['stop_loss']:
            logger.warning(f"🛑 STOP LOSS DICAPAI! P&L: {pnl_pct:.2f}%")
            await self.execute_sell(token_mint, "STOP_LOSS", current_price)
            return

    async def execute_sell(self, token_mint: str, reason: str, price: float):
        """
        Laksanakan jualan automatik
        """
        logger.info(f"💸 Melaksanakan jualan automatik ({reason})...")
        
        # Matikan trigger supaya tak execute dua kali
        if token_mint in self.triggers:
            self.triggers[token_mint]['enabled'] = False
            
        # TODO: Panggil fungsi swap sell sebenar
        # await self.raydium.execute_sell(...)
        
        # Simulasi kejayaan
        logger.info(f"✅ Jualan berjaya! ({reason}) @ {price:.6f} SOL")
        
        # Tutup posisi
        if token_mint in self.positions:
            del self.positions[token_mint]
        
        # Hentikan price tracking
        self.price_tracker.stop_tracking(token_mint)
