"""
Unit tests untuk solana_bot.wallet
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from solana_bot.wallet import WalletManager
from solders.keypair import Keypair
from solders.pubkey import Pubkey


@pytest.fixture
def mock_client():
    """Mock AsyncClient"""
    client = AsyncMock()
    client.get_balance = AsyncMock(return_value=Mock(value=1000000000))  # 1 SOL
    client.close = AsyncMock()
    return client


@pytest.fixture
def wallet_manager(mock_client):
    """WalletManager instance dengan mock client"""
    with patch('solana_bot.wallet.AsyncClient', return_value=mock_client):
        wallet = WalletManager("https://test.rpc")
        wallet.client = mock_client
        return wallet


class TestWalletManager:
    """Test suite untuk WalletManager"""
    
    def test_initialization(self):
        """Test inisialisasi WalletManager"""
        with patch('solana_bot.wallet.AsyncClient'):
            wallet = WalletManager("https://test.rpc")
            assert wallet.keypair is None
            assert wallet.address is None
    
    def test_load_from_private_key_valid(self, wallet_manager):
        """Test loading private key yang sah"""
        # Generate keypair untuk testing
        test_keypair = Keypair()
        test_private_key = str(test_keypair)
        
        result = wallet_manager.load_from_private_key(test_private_key)
        assert result is True
        assert wallet_manager.keypair is not None
        assert wallet_manager.address is not None
    
    def test_load_from_private_key_invalid(self, wallet_manager):
        """Test loading private key yang tidak sah"""
        result = wallet_manager.load_from_private_key("invalid_key")
        assert result is False
        assert wallet_manager.keypair is None
    
    def test_load_from_private_key_empty(self, wallet_manager):
        """Test loading private key kosong"""
        result = wallet_manager.load_from_private_key("")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_balance_success(self, wallet_manager):
        """Test mendapatkan baki SOL"""
        # Setup keypair
        test_keypair = Keypair()
        wallet_manager.keypair = test_keypair
        wallet_manager.address = str(test_keypair.pubkey())
        
        balance = await wallet_manager.get_balance()
        assert balance == 1.0  # 1 SOL
    
    @pytest.mark.asyncio
    async def test_get_balance_no_wallet(self, wallet_manager):
        """Test get balance tanpa wallet loaded"""
        balance = await wallet_manager.get_balance()
        assert balance == 0.0
    
    @pytest.mark.asyncio
    async def test_get_balance_error(self, wallet_manager):
        """Test get balance dengan error"""
        test_keypair = Keypair()
        wallet_manager.keypair = test_keypair
        wallet_manager.address = str(test_keypair.pubkey())
        wallet_manager.client.get_balance = AsyncMock(side_effect=Exception("RPC Error"))
        
        balance = await wallet_manager.get_balance()
        assert balance == 0.0
    
    @pytest.mark.asyncio
    async def test_get_token_balance_success(self, wallet_manager):
        """Test mendapatkan baki token"""
        test_keypair = Keypair()
        wallet_manager.keypair = test_keypair
        
        mock_response = Mock()
        mock_response.value.amount = "1000000"
        mock_response.value.decimals = 6
        wallet_manager.client.get_token_account_balance = AsyncMock(return_value=mock_response)
        
        balance = await wallet_manager.get_token_balance("TokenMintAddress")
        assert balance == 1.0
    
    @pytest.mark.asyncio
    async def test_get_token_balance_no_wallet(self, wallet_manager):
        """Test get token balance tanpa wallet"""
        balance = await wallet_manager.get_token_balance("TokenMintAddress")
        assert balance == 0.0
    
    @pytest.mark.asyncio
    async def test_close(self, wallet_manager):
        """Test closing client connection"""
        await wallet_manager.close()
        wallet_manager.client.close.assert_called_once()
