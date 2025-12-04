"""
Modul konfigurasi untuk bot Solana sniping
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from solders.pubkey import Pubkey


class BotConfig:
    """Kelas untuk menguruskan konfigurasi bot"""
    
    def __init__(self, config_path: str = "bot_config.json"):
        """
        Inisialisasi konfigurasi bot
        
        Args:
            config_path: Laluan ke fail konfigurasi JSON
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Muat konfigurasi dari fail JSON"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Fail konfigurasi tidak dijumpai: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def save_config(self):
        """Simpan konfigurasi semasa ke fail"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    @property
    def rpc_endpoint(self) -> str:
        """Dapatkan RPC endpoint"""
        return self.config.get('rpc_endpoint', 'https://api.mainnet-beta.solana.com')
    
    @property
    def websocket_endpoint(self) -> str:
        """Dapatkan WebSocket endpoint"""
        return self.config.get('websocket_endpoint', 'wss://api.mainnet-beta.solana.com')
    
    @property
    def raydium_program_id(self) -> Pubkey:
        """Dapatkan Raydium program ID"""
        return Pubkey.from_string(self.config['raydium_program_id'])
    
    @property
    def serum_program_id(self) -> Pubkey:
        """Dapatkan Serum program ID"""
        return Pubkey.from_string(self.config['serum_program_id'])
    
    @property
    def buy_delay(self) -> int:
        """Kelewatan sebelum beli (saat)"""
        return self.config['bot_settings']['buy_delay_seconds']
    
    @property
    def buy_amount(self) -> float:
        """Jumlah SOL untuk beli"""
        return self.config['bot_settings']['buy_amount_sol']
    
    @property
    def take_profit_percentage(self) -> float:
        """Peratus take profit"""
        return self.config['bot_settings']['take_profit_percentage']
    
    @property
    def stop_loss_percentage(self) -> float:
        """Peratus stop loss"""
        return self.config['bot_settings']['stop_loss_percentage']
    
    @property
    def slippage_bps(self) -> int:
        """Slippage dalam basis points"""
        return self.config['bot_settings']['slippage_bps']
    
    @property
    def check_rug_pull(self) -> bool:
        """Adakah perlu semak rug pull"""
        return self.config['bot_settings']['check_rug_pull']
    
    @property
    def max_buy_tax(self) -> float:
        """Cukai beli maksimum yang diterima (%)"""
        return self.config['bot_settings']['max_buy_tax']
    
    @property
    def max_sell_tax(self) -> float:
        """Cukai jual maksimum yang diterima (%)"""
        return self.config['bot_settings']['max_sell_tax']
    
    @property
    def min_liquidity(self) -> float:
        """Kecairan minimum yang diperlukan (SOL)"""
        return self.config['bot_settings']['min_liquidity_sol']
    
    def update_setting(self, key: str, value: Any):
        """
        Kemas kini tetapan bot
        
        Args:
            key: Kunci tetapan
            value: Nilai baharu
        """
        if key in self.config['bot_settings']:
            self.config['bot_settings'][key] = value
            self.save_config()
        else:
            raise KeyError(f"Tetapan tidak dijumpai: {key}")
