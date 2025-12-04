#!/usr/bin/env python3
"""
Solana Sniping Bot - Versi Selamat
Bot dagangan automatik untuk Raydium DEX

AMARAN: Bot ini untuk tujuan pendidikan sahaja.
Dagangan cryptocurrency melibatkan risiko tinggi.
"""

import asyncio
import logging
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Tambah parent directory ke path
sys.path.insert(0, str(Path(__file__).parent))

from safe_bot.config import BotConfig
from safe_bot.wallet import WalletManager
from safe_bot.monitor import PoolMonitor
from safe_bot.security import SecurityAnalyzer

# Inisialisasi colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SolanaSnipingBot:
    """Kelas utama untuk bot sniping Solana"""
    
    def __init__(self):
        """Inisialisasi bot"""
        self.config = None
        self.wallet = None
        self.monitor = None
        self.security = None
        self.is_running = False
        
    async def initialize(self):
        """Inisialisasi semua komponen bot"""
        try:
            # Muat konfigurasi
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.CYAN}🚀 SOLANA SNIPING BOT - VERSI SELAMAT")
            print(f"{Fore.CYAN}{'='*60}\n")
            
            print(f"{Fore.YELLOW}📋 Memuat konfigurasi...")
            self.config = BotConfig()
            print(f"{Fore.GREEN}✅ Konfigurasi berjaya dimuat\n")
            
            # Setup wallet
            print(f"{Fore.YELLOW}👛 Menyediakan dompet...")
            self.wallet = WalletManager(self.config.rpc_endpoint)
            
            # Minta private key
            while True:
                private_key = input(f"{Fore.CYAN}🔑 Sila masukkan private key anda: {Style.RESET_ALL}")
                
                if self.wallet.load_from_private_key(private_key):
                    break
                else:
                    print(f"{Fore.RED}❌ Private key tidak sah. Sila cuba lagi.\n")
            
            # Papar maklumat dompet
            print(f"\n{Fore.GREEN}✅ Alamat Dompet: {Fore.WHITE}{self.wallet.address}")
            
            balance = await self.wallet.get_balance()
            print(f"{Fore.GREEN}💰 Baki SOL: {Fore.WHITE}{balance:.4f} SOL\n")
            
            if balance < self.config.buy_amount:
                print(f"{Fore.RED}⚠️  AMARAN: Baki tidak mencukupi untuk dagangan!")
                print(f"{Fore.RED}   Diperlukan: {self.config.buy_amount} SOL")
                print(f"{Fore.RED}   Anda ada: {balance} SOL\n")
            
            # Setup security analyzer
            print(f"{Fore.YELLOW}🛡️  Menyediakan penganalisis keselamatan...")
            self.security = SecurityAnalyzer(self.wallet.client)
            print(f"{Fore.GREEN}✅ Penganalisis keselamatan bersedia\n")
            
            # Setup pool monitor
            print(f"{Fore.YELLOW}🔍 Menyediakan pemantau pool...")
            self.monitor = PoolMonitor(
                self.config.rpc_endpoint,
                self.config.websocket_endpoint,
                self.config.raydium_program_id,
                callback=self.on_new_pool
            )
            print(f"{Fore.GREEN}✅ Pemantau pool bersedia\n")
            
            return True
            
        except FileNotFoundError as e:
            print(f"{Fore.RED}❌ Error: {e}")
            print(f"{Fore.YELLOW}💡 Pastikan fail bot_config.json wujud")
            return False
        except Exception as e:
            logger.error(f"Error initializing bot: {e}", exc_info=True)
            print(f"{Fore.RED}❌ Error semasa inisialisasi: {e}")
            return False
    
    async def on_new_pool(self, pool_info: dict):
        """
        Callback apabila pool baharu dijumpai
        
        Args:
            pool_info: Maklumat pool baharu
        """
        try:
            token_address = pool_info.get('token_address')
            pool_address = pool_info.get('pool_address')
            
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.GREEN}🆕 POOL BAHARU DIJUMPAI!")
            print(f"{Fore.CYAN}{'='*60}")
            print(f"{Fore.WHITE}Token: {token_address}")
            print(f"{Fore.WHITE}Pool: {pool_address}\n")
            
            # Check keselamatan jika enabled
            if self.config.check_rug_pull:
                print(f"{Fore.YELLOW}🔍 Menganalisis keselamatan token...")
                
                # TODO: Implement actual security check
                # security_result = await self.security.analyze_token(token_mint, pool_address)
                
                print(f"{Fore.GREEN}✅ Analisis keselamatan selesai\n")
            
            # TODO: Implement buy logic
            print(f"{Fore.YELLOW}💡 Fungsi pembelian automatik akan dilaksanakan di sini")
            print(f"{Fore.YELLOW}   (Masih dalam pembangunan)\n")
            
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
            print(f"{Fore.WHITE}   • Slippage: {self.config.slippage_bps / 100}%")
            print(f"{Fore.WHITE}   • Check Rug Pull: {'Ya' if self.config.check_rug_pull else 'Tidak'}\n")
            
            print(f"{Fore.YELLOW}🔍 Memantau pool baharu...")
            print(f"{Fore.YELLOW}   Tekan Ctrl+C untuk hentikan bot\n")
            
            # Mulakan monitoring
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
        
        print(f"{Fore.GREEN}✅ Selesai. Terima kasih!\n")
    
    def display_menu(self):
        """Papar menu utama"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}📋 MENU UTAMA")
        print(f"{Fore.CYAN}{'='*60}\n")
        print(f"{Fore.WHITE}1. Mulakan Bot (Monitor & Snipe)")
        print(f"{Fore.WHITE}2. Lihat Konfigurasi")
        print(f"{Fore.WHITE}3. Ubah Tetapan")
        print(f"{Fore.WHITE}4. Semak Baki Dompet")
        print(f"{Fore.WHITE}5. Keluar\n")
    
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
                await self.change_settings()
            elif choice == '4':
                await self.check_balance()
            elif choice == '5':
                print(f"\n{Fore.GREEN}👋 Terima kasih! Selamat berdagang!\n")
                break
            else:
                print(f"{Fore.RED}❌ Pilihan tidak sah. Sila cuba lagi.\n")
    
    def show_config(self):
        """Papar konfigurasi semasa"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}⚙️  KONFIGURASI SEMASA")
        print(f"{Fore.CYAN}{'='*60}\n")
        print(f"{Fore.WHITE}Jumlah Beli: {self.config.buy_amount} SOL")
        print(f"{Fore.WHITE}Take Profit: {self.config.take_profit_percentage}%")
        print(f"{Fore.WHITE}Stop Loss: {self.config.stop_loss_percentage}%")
        print(f"{Fore.WHITE}Slippage: {self.config.slippage_bps / 100}%")
        print(f"{Fore.WHITE}Check Rug Pull: {'Ya' if self.config.check_rug_pull else 'Tidak'}")
        print(f"{Fore.WHITE}Kecairan Minimum: {self.config.min_liquidity} SOL\n")
    
    async def change_settings(self):
        """Ubah tetapan bot"""
        print(f"\n{Fore.YELLOW}⚙️  Fungsi ubah tetapan akan dilaksanakan di sini")
        print(f"{Fore.YELLOW}   (Masih dalam pembangunan)\n")
    
    async def check_balance(self):
        """Semak baki dompet"""
        if self.wallet:
            balance = await self.wallet.get_balance()
            print(f"\n{Fore.GREEN}💰 Baki Semasa: {Fore.WHITE}{balance:.4f} SOL\n")
        else:
            print(f"\n{Fore.RED}❌ Dompet belum dimuat\n")


async def main():
    """Fungsi utama"""
    bot = SolanaSnipingBot()
    
    # Inisialisasi bot
    if await bot.initialize():
        # Jalankan bot dalam mod interaktif
        await bot.run_interactive()
    else:
        print(f"\n{Fore.RED}❌ Gagal memulakan bot\n")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Bot dihentikan. Terima kasih!\n")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n{Fore.RED}❌ Error kritikal: {e}\n")
        sys.exit(1)
