"""
Modul konfigurasi untuk bot Solana sniping
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
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
    
    @property
    def max_trades_per_hour(self) -> int:
        """Maksimum dagangan per jam"""
        return self.config['bot_settings'].get('max_trades_per_hour', 5)
    
    @property
    def min_volume_24h(self) -> float:
        """Volume minimum 24 jam ($)"""
        return self.config['bot_settings'].get('min_volume_24h', 5000)
    
    @property
    def max_hold_time_hours(self) -> float:
        """Maksimum masa pegangan (jam)"""
        return self.config['bot_settings'].get('max_hold_time_hours', 4)
    
    @property
    def cooldown_after_sell(self) -> int:
        """Cooldown selepas jual (saat)"""
        return self.config['bot_settings'].get('cooldown_after_sell', 60)
    
    @property
    def enable_trailing_stop(self) -> bool:
        """Aktifkan trailing stop"""
        return self.config['bot_settings'].get('enable_trailing_stop', True)
    
    @property
    def trailing_stop_percentage(self) -> float:
        """Peratus trailing stop"""
        return self.config['bot_settings'].get('trailing_stop_percentage', 10)
    
    # Token Filters
    @property
    def max_supply(self) -> int:
        """Bekalan maksimum token"""
        return self.config.get('token_filters', {}).get('max_supply', 1000000000)
    
    @property
    def min_holders(self) -> int:
        """Minimum pemegang token"""
        return self.config.get('token_filters', {}).get('min_holders', 100)
    
    @property
    def max_top_holder_percent(self) -> float:
        """Peratus maksimum pemegang teratas"""
        return self.config.get('token_filters', {}).get('max_top_holder_percent', 20)
    
    @property
    def contract_verified(self) -> bool:
        """Semak kontrak diverifikasi"""
        return self.config.get('token_filters', {}).get('contract_verified', True)
    
    @property
    def renounced_ownership(self) -> bool:
        """Semak pemilikan direnounce"""
        return self.config.get('token_filters', {}).get('renounced_ownership', True)
    
    @property
    def birdeye_api_key(self) -> Optional[str]:
        """Get Birdeye API key"""
        return self.config.get('api_keys', {}).get('birdeye', '')

    @property
    def rugcheck_api_key(self) -> Optional[str]:
        """Get RugCheck API key"""
        return self.config.get('api_keys', {}).get('rugcheck', '')

    # Advanced Features
    @property
    def multi_source_volume(self) -> bool:
        """Enable multi-source volume validation"""
        return self.config.get('advanced_features', {}).get('multi_source_volume', False)

    @property
    def pool_liquidity_analysis(self) -> bool:
        """Enable pool liquidity analysis before trading"""
        return self.config.get('advanced_features', {}).get('pool_liquidity_analysis', False)

    @property
    def price_volatility_filter(self) -> bool:
        """Enable price volatility filtering"""
        return self.config.get('advanced_features', {}).get('price_volatility_filter', False)

    @property
    def token_age_validation(self) -> bool:
        """Enable token age validation"""
        return self.config.get('advanced_features', {}).get('token_age_validation', False)

    @property
    def advanced_holder_analysis(self) -> bool:
        """Enable advanced holder analysis"""
        return self.config.get('advanced_features', {}).get('advanced_holder_analysis', False)

    # Validation Thresholds
    @property
    def min_token_age_hours(self) -> int:
        """Minimum token age in hours"""
        return self.config.get('validation_thresholds', {}).get('min_token_age_hours', 24)

    @property
    def max_price_change_24h(self) -> float:
        """Maximum price change in 24h (%)"""
        return self.config.get('validation_thresholds', {}).get('max_price_change_24h', 50)

    @property
    def max_volatility_threshold(self) -> float:
        """Maximum volatility threshold (0.0-1.0)"""
        return self.config.get('validation_thresholds', {}).get('max_volatility_threshold', 0.3)

    @property
    def min_volume_confidence(self) -> float:
        """Minimum volume confidence score (0.0-1.0)"""
        return self.config.get('validation_thresholds', {}).get('min_volume_confidence', 0.3)

    @property
    def max_price_impact(self) -> float:
        """Maximum price impact threshold (0.0-1.0)"""
        return self.config.get('validation_thresholds', {}).get('max_price_impact', 0.05)

    @property
    def min_distribution_score(self) -> float:
        """Minimum holder distribution score (0.0-1.0)"""
        return self.config.get('validation_thresholds', {}).get('min_distribution_score', 0.7)
