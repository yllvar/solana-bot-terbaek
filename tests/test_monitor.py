"""
Unit tests untuk solana_bot.monitor
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from solana_bot.monitor import PoolMonitor
from solders.pubkey import Pubkey
import base64


@pytest.fixture
def mock_config():
    """Mock BotConfig"""
    config = Mock()
    config.buy_amount = 0.1
    config.buy_delay = 0
    return config


@pytest.fixture
def mock_wallet():
    """Mock WalletManager"""
    from solders.keypair import Keypair
    wallet = Mock()
    wallet.keypair = Keypair()
    return wallet


@pytest.fixture
def pool_monitor(mock_config, mock_wallet):
    """PoolMonitor instance"""
    with patch('solana_bot.monitor.AsyncClient'):
        monitor = PoolMonitor(
            rpc_endpoint="https://test.rpc",
            ws_endpoint="wss://test.ws",
            raydium_program_id=Pubkey.default(),
            config=mock_config,
            wallet_manager=mock_wallet
        )
        monitor.client = AsyncMock()
        return monitor


class TestPoolMonitor:
    """Test suite untuk PoolMonitor"""
    
    def test_initialization(self, pool_monitor, mock_config, mock_wallet):
        """Test inisialisasi PoolMonitor"""
        assert pool_monitor.config == mock_config
        assert pool_monitor.wallet == mock_wallet
        assert pool_monitor.is_monitoring is False
    
    def test_is_new_pool_true(self, pool_monitor):
        """Test detection pool baharu"""
        mock_result = Mock()
        mock_result.value.logs = [
            "Program log: Instruction: Initialize",
            "Program log: ray_log: test_data"
        ]
        
        is_new = pool_monitor._is_new_pool(mock_result)
        assert is_new is True
    
    def test_is_new_pool_false(self, pool_monitor):
        """Test detection bukan pool baharu"""
        mock_result = Mock()
        mock_result.value.logs = [
            "Program log: Instruction: Swap",
            "Program log: Some other log"
        ]
        
        is_new = pool_monitor._is_new_pool(mock_result)
        assert is_new is False
    
    def test_is_new_pool_no_logs(self, pool_monitor):
        """Test dengan tiada logs"""
        mock_result = Mock()
        mock_result.value = None
        
        is_new = pool_monitor._is_new_pool(mock_result)
        assert is_new is False
    
    def test_decode_ray_log_valid(self, pool_monitor):
        """Test decode ray_log yang sah"""
        # Create mock ray_log data
        # log_type (1) + other data (42) + pubkeys (32 * 11) = 395 bytes minimum
        mock_data = bytes([0] * 400)  # log_type = 0 (Init)
        b64_data = base64.b64encode(mock_data).decode()
        
        pool_data = pool_monitor._decode_ray_log(b64_data)
        
        assert pool_data is not None
        assert 'pool_address' in pool_data
        assert 'token_address' in pool_data
    
    def test_decode_ray_log_too_short(self, pool_monitor):
        """Test decode ray_log yang terlalu pendek"""
        mock_data = bytes([0] * 50)  # Too short
        b64_data = base64.b64encode(mock_data).decode()
        
        pool_data = pool_monitor._decode_ray_log(b64_data)
        assert pool_data is None
    
    def test_decode_ray_log_wrong_type(self, pool_monitor):
        """Test decode ray_log dengan log type yang salah"""
        mock_data = bytes([1] * 400)  # log_type = 1 (bukan Init)
        b64_data = base64.b64encode(mock_data).decode()
        
        pool_data = pool_monitor._decode_ray_log(b64_data)
        assert pool_data is None
    
    def test_decode_ray_log_invalid_base64(self, pool_monitor):
        """Test decode ray_log dengan base64 tidak sah"""
        pool_data = pool_monitor._decode_ray_log("invalid_base64!!!")
        assert pool_data is None
    
    @pytest.mark.asyncio
    async def test_extract_pool_info_success(self, pool_monitor):
        """Test extract pool info dengan jayanya"""
        mock_data = bytes([0] * 400)
        b64_data = base64.b64encode(mock_data).decode()
        
        mock_result = Mock()
        mock_result.value.logs = [f"Program log: ray_log: {b64_data}"]
        
        pool_info = await pool_monitor._extract_pool_info(mock_result)
        
        assert pool_info is not None
        assert 'pool_address' in pool_info
    
    @pytest.mark.asyncio
    async def test_extract_pool_info_no_ray_log(self, pool_monitor):
        """Test extract pool info tanpa ray_log"""
        mock_result = Mock()
        mock_result.value.logs = ["Program log: Other log"]
        
        pool_info = await pool_monitor._extract_pool_info(mock_result)
        assert pool_info is None
    
    @pytest.mark.asyncio
    async def test_execute_auto_buy_success(self, pool_monitor):
        """Test auto buy dengan jayanya"""
        pool_info = {
            'pool_address': str(Pubkey.default()),
            'token_address': str(Pubkey.default())
        }
        
        # Mock dependencies
        pool_monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={
            'base_mint': Pubkey.default(),
            'quote_mint': Pubkey.default(),
        })
        pool_monitor.raydium_swap.get_associated_token_address = Mock(return_value=Pubkey.default())
        pool_monitor.raydium_swap.build_swap_instruction = Mock()
        pool_monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="test_sig")
        
        await pool_monitor.execute_auto_buy(pool_info)
        
        pool_monitor.tx_builder.build_and_send_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_auto_buy_no_pool_address(self, pool_monitor):
        """Test auto buy tanpa pool address"""
        pool_info = {'token_address': str(Pubkey.default())}
        
        # Should not raise error
        await pool_monitor.execute_auto_buy(pool_info)
    
    @pytest.mark.asyncio
    async def test_execute_auto_buy_no_pool_keys(self, pool_monitor):
        """Test auto buy bila pool keys tidak dijumpai"""
        pool_info = {
            'pool_address': str(Pubkey.default()),
            'token_address': str(Pubkey.default())
        }
        
        pool_monitor.raydium_swap.get_pool_keys = AsyncMock(return_value=None)
        pool_monitor.tx_builder.build_and_send_transaction = AsyncMock()
        
        await pool_monitor.execute_auto_buy(pool_info)
        
        # Transaction should not be sent
        pool_monitor.tx_builder.build_and_send_transaction.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_auto_buy_with_delay(self, pool_monitor, mock_config):
        """Test auto buy dengan delay"""
        mock_config.buy_delay = 1
        pool_info = {
            'pool_address': str(Pubkey.default()),
            'token_address': str(Pubkey.default())
        }
        
        pool_monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={
            'base_mint': Pubkey.default(),
            'quote_mint': Pubkey.default(),
        })
        pool_monitor.raydium_swap.get_associated_token_address = Mock(return_value=Pubkey.default())
        pool_monitor.raydium_swap.build_swap_instruction = Mock()
        pool_monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="test_sig")
        
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            await pool_monitor.execute_auto_buy(pool_info)
            mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, pool_monitor):
        """Test stop monitoring"""
        pool_monitor.is_monitoring = True
        
        await pool_monitor.stop_monitoring()
        
        assert pool_monitor.is_monitoring is False
        pool_monitor.client.close.assert_called_once()
