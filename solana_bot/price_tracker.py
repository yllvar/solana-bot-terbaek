"""
Modul pemantauan harga token secara real-time
"""
import asyncio
import logging
import struct
from typing import Dict, Optional, Callable, List, Any
from solders.pubkey import Pubkey
from .raydium.layouts import AMM_INFO_LAYOUT_V4

logger = logging.getLogger(__name__)

class PriceTracker:
    """Kelas untuk memantau harga token"""
    
    def __init__(self, client, raydium_swap):
        """
        Inisialisasi PriceTracker
        
        Args:
            client: AsyncClient Solana
            raydium_swap: RaydiumSwap instance
        """
        self.client = client
        self.raydium = raydium_swap
        self.prices: Dict[str, float] = {}
        self.tracking: Dict[str, bool] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        
    async def start_tracking(
        self,
        token_mint: str,
        pool_address: str,
        interval: float = 2.0
    ):
        """
        Mula memantau harga token
        """
        if self.tracking.get(token_mint):
            logger.warning(f"Sudah memantau token: {token_mint}")
            return

        self.tracking[token_mint] = True
        logger.info(f"🔍 Mula memantau harga: {token_mint} (Pool: {pool_address})")
        
        pool_pubkey = Pubkey.from_string(pool_address)
        
        while self.tracking.get(token_mint):
            try:
                # 1. Dapatkan data pool & reserves
                pool_data = await self.get_pool_data(pool_pubkey)
                
                if pool_data and 'price' in pool_data:
                    price = pool_data['price']
                    
                    if price > 0:
                        old_price = self.prices.get(token_mint)
                        self.prices[token_mint] = price
                        
                        if old_price is not None and price != old_price:
                            await self.trigger_callbacks(token_mint, price, old_price)
                    else:
                        logger.warning(f"Harga tidak sah untuk {token_mint}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ Error tracking price for {token_mint}: {e}")
                await asyncio.sleep(interval)
    
    def stop_tracking(self, token_mint: str):
        """Hentikan pemantauan harga"""
        if token_mint in self.tracking:
            self.tracking[token_mint] = False
            logger.info(f"⏹️  Berhenti memantau harga: {token_mint}")
    
    def register_callback(self, token_mint: str, callback: Callable):
        """Daftar callback"""
        if token_mint not in self.callbacks:
            self.callbacks[token_mint] = []
        self.callbacks[token_mint].append(callback)
        
    async def trigger_callbacks(self, token_mint: str, new_price: float, old_price: float):
        """Jalankan callbacks"""
        if token_mint in self.callbacks:
            for callback in self.callbacks[token_mint]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(token_mint, new_price, old_price)
                    else:
                        callback(token_mint, new_price, old_price)
                except Exception as e:
                    logger.error(f"Error in price callback: {e}")

    async def get_pool_data(self, pool_pubkey: Pubkey) -> Optional[Dict[str, Any]]:
        """
        Dapatkan data pool dan kira harga dari reserves
        """
        try:
            # 1. Fetch akaun AMM
            resp = await self.client.get_account_info(pool_pubkey)
            if not resp.value:
                return None
                
            data = resp.value.data
            parsed_data = AMM_INFO_LAYOUT_V4.parse(data)
            
            # 2. Extract info penting
            base_decimal = parsed_data.base_decimal
            quote_decimal = parsed_data.quote_decimal
            
            base_vault = Pubkey.from_bytes(parsed_data.base_vault)
            quote_vault = Pubkey.from_bytes(parsed_data.quote_vault)
            
            # Semak jika vault address valid (bukan zero/default)
            if str(base_vault) == "11111111111111111111111111111111" or \
               str(quote_vault) == "11111111111111111111111111111111":
                logger.warning("Alamat vault tidak sah (mungkin ralat layout)")
                return None
            
            # 3. Fetch baki vault (reserves)
            # Kita boleh guna get_token_account_balance
            base_bal_resp = await self.client.get_token_account_balance(base_vault)
            quote_bal_resp = await self.client.get_token_account_balance(quote_vault)
            
            if not base_bal_resp.value or not quote_bal_resp.value:
                logger.warning("Gagal mendapatkan baki vault")
                return None
                
            base_reserve = float(base_bal_resp.value.amount)
            quote_reserve = float(quote_bal_resp.value.amount)
            
            if base_reserve == 0:
                return None
                
            # 4. Kira harga
            # Price = (Quote Reserve / 10^QuoteDecimals) / (Base Reserve / 10^BaseDecimals)
            base_amount = base_reserve / (10 ** base_decimal)
            quote_amount = quote_reserve / (10 ** quote_decimal)
            
            price = quote_amount / base_amount
            
            return {
                'price': price,
                'base_reserve': base_reserve,
                'quote_reserve': quote_reserve,
                'base_decimal': base_decimal,
                'quote_decimal': quote_decimal,
                'base_vault': str(base_vault),
                'quote_vault': str(quote_vault)
            }
            
        except Exception as e:
            logger.error(f"Error fetching pool data: {e}")
            return None
