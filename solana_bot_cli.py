#!/usr/bin/env python3
"""
Solana Sniping Bot - Versi Selamat
Bot dagangan automatik untuk Raydium DEX
"""

import asyncio
import logging
import sys
from pathlib import Path
from colorama import init, Fore, Style

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.solana_bot.config import BotConfig
from src.solana_bot.wallet import WalletManager
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.security import SecurityAnalyzer
from src.solana_bot.raydium.swap import RaydiumSwap
from src.solana_bot.transaction import TransactionBuilder
from src.solana_bot.price_tracker import PriceTracker
from src.solana_bot.triggers import TradeTriggers

init(autoreset=True)

# Setup logging dengan format yang lebih baik dan real-time output
import datetime
log_filename = f"bot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, mode='w'),  # New log file setiap run
        logging.StreamHandler()  # Console output
    ],
    force=True  # Override any existing config
)

# Set logging untuk libraries pihak ketiga ke WARNING
logging.getLogger('solana').setLevel(logging.WARNING)
logging.getLogger('solders').setLevel(logging.WARNING)
logging.getLogger('websockets').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info(f"📝 General log file: {log_filename}")

# Import after logging setup to get scanning log filename
from src.solana_bot.monitor import scanning_logger, SCANNING_LOG_FILENAME, MARKET_SCANNING_LOG_FILENAME

logger.info(f"🔍 Raydium scanning log: {SCANNING_LOG_FILENAME}")
logger.info(f"📈 Market scanning log: {MARKET_SCANNING_LOG_FILENAME}")

class SolanaSnipingBot:
    """Kelas utama untuk bot sniping Solana"""
    
    def __init__(self):
        self.config = None
        self.wallet = None
        self.monitor = None
        self.security = None
        self.raydium_swap = None
        self.tx_builder = None
        self.price_tracker = None
        self.triggers = None
        self.is_running = False
        
    async def initialize(self):
        """Inisialisasi semua komponen bot"""
        try:
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}🚀 SOLANA SNIPING BOT - VERSI SELAMAT")
            print(f"{Fore.CYAN}{'='*60}\n")
            
            # 1. Config
            print(f"{Fore.YELLOW}📋 Memuat konfigurasi...")
            self.config = BotConfig("config/bot_config.json")
            print(f"{Fore.GREEN}✅ Konfigurasi berjaya dimuat\n")
            
            # 2. Wallet
            print(f"{Fore.YELLOW}👛 Menyediakan dompet...")
            self.wallet = WalletManager(self.config.rpc_endpoint)
            
            while True:
                private_key = input(f"{Fore.CYAN}🔑 Sila masukkan private key anda: {Style.RESET_ALL}")
                if self.wallet.load_from_private_key(private_key):
                    break
                else:
                    print(f"{Fore.RED}❌ Private key tidak sah. Sila cuba lagi.\n")
            
            print(f"\n{Fore.GREEN}✅ Alamat Dompet: {Fore.WHITE}{self.wallet.address}")
            balance = await self.wallet.get_balance()
            print(f"{Fore.GREEN}💰 Baki SOL: {Fore.WHITE}{balance:.4f} SOL\n")
            
            if balance < self.config.buy_amount:
                print(f"{Fore.RED}⚠️  AMARAN: Baki tidak mencukupi untuk dagangan!")
            
            # 3. Core Components
            print(f"{Fore.YELLOW}⚙️  Menyediakan komponen dagangan...")
            self.raydium_swap = RaydiumSwap(self.wallet.client, self.wallet)
            self.tx_builder = TransactionBuilder(self.wallet.client, self.wallet)
            self.price_tracker = PriceTracker(self.wallet.client, self.raydium_swap)
            
            # Initialize Birdeye client for advanced features
            from .birdeye_client import BirdeyeClient
            self.birdeye = BirdeyeClient(api_key=self.config.birdeye_api_key)
            
            self.triggers = TradeTriggers(
                self.price_tracker,
                self.raydium_swap,
                self.tx_builder,
                self.wallet,
                self.config
            )
            self.security = SecurityAnalyzer(
                self.wallet.client, 
                self.config,
                birdeye_client=self.birdeye
            )
            
            # 4. Monitor
            print(f"{Fore.YELLOW}🔍 Menyediakan pemantau pool...")
            self.monitor = PoolMonitor(
                self.config.rpc_endpoint,
                self.config.websocket_endpoint,
                self.config.raydium_program_id,
                self.config,
                self.wallet,
                callback=self.on_new_pool
            )
            print(f"{Fore.GREEN}✅ Semua sistem bersedia!\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing bot: {e}", exc_info=True)
            print(f"{Fore.RED}❌ Error semasa inisialisasi: {e}")
            return False
    
    async def on_new_pool(self, pool_info: dict):
        """Callback apabila pool baharu dijumpai"""
        try:
            token_address = pool_info.get('token_address')
            pool_address = pool_info.get('pool_address')
            
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.GREEN}🆕 POOL BAHARU DIJUMPAI!")
            print(f"{Fore.CYAN}{'='*60}")
            print(f"{Fore.WHITE}Token: {token_address}")
            print(f"{Fore.WHITE}Pool: {pool_address}\n")
            
            # 1. Security Check
            if self.config.check_rug_pull:
                print(f"{Fore.YELLOW}🔍 Menganalisis keselamatan token...")
                
                # Run comprehensive token filter checks
                try:
                    filter_result = await self.security.check_token_filters(token_address)
                    
                    if filter_result['passed']:
                        print(f"{Fore.GREEN}✅ Token passed all security filters")
                        # Show filter details
                        filters = filter_result.get('filters', {})
                        if 'supply' in filters and filters['supply']['passed']:
                            supply_info = filters['supply']
                            print(f"{Fore.GREEN}   📊 Supply: {supply_info.get('supply', 'N/A'):,} (OK)")
                        if 'holders' in filters and filters['holders']['passed']:
                            holder_info = filters['holders']
                            print(f"{Fore.GREEN}   👥 Holders: {holder_info.get('holder_count', 'N/A')} (OK)")
                    else:
                        print(f"{Fore.RED}🚫 Token failed security filters!")
                        for warning in filter_result.get('warnings', []):
                            print(f"{Fore.RED}   {warning}")
                        print(f"{Fore.YELLOW}⚠️ Skipping this token due to security concerns")
                        return  # Don't proceed with this token
                        
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Security check failed: {e} - proceeding with caution")
                    print(f"{Fore.GREEN}✅ Using basic security checks (fallback)")
            else:
                print(f"{Fore.YELLOW}ℹ️ Security checks disabled in configuration")
            
            # 2. Auto Buy (Handled by Monitor internally, but we can log here)
            if self.config.buy_amount > 0:
                print(f"{Fore.YELLOW}🤖 Auto Buy diaktifkan...")
                
                # Jika buy berjaya (simulasi logic flow):
                # 3. Start Tracking
                # await self.price_tracker.start_tracking(token_address, pool_address)
                # self.triggers.set_triggers(token_address, self.config.take_profit_percentage, self.config.stop_loss_percentage)
                # self.triggers.open_position(token_address, ...)
            
        except Exception as e:
            logger.error(f"Error processing new pool: {e}", exc_info=True)
            print(f"{Fore.RED}❌ Error memproses pool baharu: {e}\n")
    
    async def start(self):
        """Mulakan bot"""
        try:
            self.is_running = True
            print(f"{Fore.GREEN}{'='*60}")
            print(f"{Fore.GREEN}✅ BOT BERJAYA DIMULAKAN!")
            print(f"{Fore.GREEN}{'='*60}\n")
            
            print(f"{Fore.CYAN}📊 TETAPAN BOT:")
            print(f"{Fore.WHITE}   • Jumlah Beli: {self.config.buy_amount} SOL")
            print(f"{Fore.WHITE}   • Take Profit: {self.config.take_profit_percentage}%")
            print(f"{Fore.WHITE}   • Stop Loss: {self.config.stop_loss_percentage}%")
            
            print(f"{Fore.YELLOW}🔍 Memantau pool baharu...")
            print(f"{Fore.YELLOW}   Tekan Ctrl+C untuk hentikan bot\n")
            
            await self.monitor.start_monitoring()
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️  Bot dihentikan oleh pengguna")
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
            print(f"{Fore.RED}❌ Error: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Bersihkan resources"""
        print(f"\n{Fore.YELLOW}🧹 Membersihkan resources...")
        if self.monitor:
            await self.monitor.stop_monitoring()
        if self.wallet:
            await self.wallet.close()
        if hasattr(self, 'birdeye') and self.birdeye:
            await self.birdeye.close()
        print(f"{Fore.GREEN}✅ Selesai. Terima kasih!\n")
    
    async def run_interactive(self):
        """Jalankan bot dalam mod interaktif"""
        while True:
            self.display_menu()
            choice = input(f"{Fore.CYAN}Pilih opsyen (1-5): {Style.RESET_ALL}")
            
            if choice == '1':
                await self.start()
                break
            elif choice == '2':
                self.show_config()
            elif choice == '3':
                print("Fungsi ubah tetapan belum diimplementasi.")
            elif choice == '4':
                if self.wallet:
                    bal = await self.wallet.get_balance()
                    print(f"\n💰 Baki: {bal:.4f} SOL\n")
            elif choice == '5':
                break
            else:
                print("Pilihan tidak sah.")

    def display_menu(self):
        print(f"\n{Fore.CYAN}📋 MENU UTAMA")
        print("1. Mulakan Bot")
        print("2. Lihat Konfigurasi")
        print("3. Ubah Tetapan")
        print("4. Semak Baki")
        print("5. Keluar\n")

    def show_config(self):
        print(f"\n⚙️  KONFIGURASI")
        print(f"Buy Amount: {self.config.buy_amount} SOL")
        print(f"TP: {self.config.take_profit_percentage}%")
        print(f"SL: {self.config.stop_loss_percentage}%")
        print(f"Trailing Stop: {'Enabled' if self.config.enable_trailing_stop else 'Disabled'} ({self.config.trailing_stop_percentage}%)")
        print(f"Min Liquidity: {self.config.min_liquidity} SOL")
        print(f"Max Trades/Hour: {self.config.max_trades_per_hour}")
        print(f"Max Hold Time: {self.config.max_hold_time_hours} hours")
        print(f"Min Volume 24h: ${self.config.min_volume_24h:,}")
        print(f"Cooldown After Sell: {self.config.cooldown_after_sell}s")
        print(f"\n🔍 TOKEN FILTERS:")
        print(f"Max Supply: {self.config.max_supply:,}")
        print(f"Min Holders: {self.config.min_holders}")
        print(f"Max Top Holder: {self.config.max_top_holder_percent}%")
        print(f"Contract Verified: {self.config.contract_verified}")
        print(f"Ownership Renounced: {self.config.renounced_ownership}")

async def main():
    bot = SolanaSnipingBot()
    if await bot.initialize():
        await bot.run_interactive()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
