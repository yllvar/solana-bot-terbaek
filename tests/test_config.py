"""
Unit tests untuk solana_bot.config
"""
import pytest
import json
import tempfile
from pathlib import Path
from solana_bot.config import BotConfig


class TestBotConfig:
    """Test suite untuk BotConfig"""
    
    def test_load_default_config(self):
        """Test loading konfigurasi default"""
        config = BotConfig()
        assert config.rpc_endpoint is not None
        assert config.buy_amount >= 0
        assert config.take_profit_percentage >= 0
        assert config.stop_loss_percentage >= 0
    
    def test_load_custom_config(self, tmp_path):
        """Test loading konfigurasi custom dari file"""
        config_data = {
            "rpc_endpoint": "https://custom.rpc.endpoint",
            "websocket_endpoint": "wss://custom.ws.endpoint",
            "buy_amount": 0.5,
            "take_profit_percentage": 200,
            "stop_loss_percentage": 30,
            "slippage_bps": 100,
            "check_rug_pull": False
        }
        
        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = BotConfig(str(config_file))
        assert config.rpc_endpoint == "https://custom.rpc.endpoint"
        assert config.buy_amount == 0.5
        assert config.take_profit_percentage == 200
        assert config.stop_loss_percentage == 30
    
    def test_config_properties(self):
        """Test property accessors"""
        config = BotConfig()
        
        # Test semua properties boleh diakses
        assert isinstance(config.rpc_endpoint, str)
        assert isinstance(config.websocket_endpoint, str)
        assert isinstance(config.buy_amount, (int, float))
        assert isinstance(config.take_profit_percentage, (int, float))
        assert isinstance(config.stop_loss_percentage, (int, float))
        assert isinstance(config.slippage_bps, int)
        assert isinstance(config.check_rug_pull, bool)
    
    def test_raydium_program_id(self):
        """Test Raydium Program ID adalah Pubkey yang sah"""
        config = BotConfig()
        from solders.pubkey import Pubkey
        assert isinstance(config.raydium_program_id, Pubkey)
    
    def test_invalid_config_file(self):
        """Test handling fail konfigurasi yang tidak sah"""
        # File tidak wujud - sepatutnya guna default
        config = BotConfig("nonexistent_file.json")
        assert config.rpc_endpoint is not None  # Guna default
    
    def test_malformed_json(self, tmp_path):
        """Test handling JSON yang rosak"""
        config_file = tmp_path / "bad_config.json"
        with open(config_file, 'w') as f:
            f.write("{ invalid json }")
        
        config = BotConfig(str(config_file))
        assert config.rpc_endpoint is not None  # Fallback ke default
