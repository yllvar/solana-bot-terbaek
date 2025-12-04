"""
Unit tests untuk solana_bot.transaction
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from solana_bot.transaction import TransactionBuilder
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.hash import Hash


@pytest.fixture
def mock_client():
    """Mock AsyncClient"""
    client = AsyncMock()
    
    # Mock get_latest_blockhash
    mock_blockhash_response = Mock()
    mock_blockhash_response.value.blockhash = Hash.default()
    client.get_latest_blockhash = AsyncMock(return_value=mock_blockhash_response)
    
    # Mock send_transaction
    mock_tx_response = Mock()
    mock_tx_response.value = "test_signature_123"
    client.send_transaction = AsyncMock(return_value=mock_tx_response)
    
    # Mock get_signature_statuses
    mock_status = Mock()
    mock_status.err = None
    mock_status.confirmation_status = "confirmed"
    mock_status_response = Mock()
    mock_status_response.value = [mock_status]
    client.get_signature_statuses = AsyncMock(return_value=mock_status_response)
    
    return client


@pytest.fixture
def mock_wallet():
    """Mock WalletManager"""
    wallet = Mock()
    wallet.keypair = Keypair()
    return wallet


@pytest.fixture
def tx_builder(mock_client, mock_wallet):
    """TransactionBuilder instance"""
    return TransactionBuilder(mock_client, mock_wallet)


class TestTransactionBuilder:
    """Test suite untuk TransactionBuilder"""
    
    def test_initialization(self, tx_builder, mock_client, mock_wallet):
        """Test inisialisasi TransactionBuilder"""
        assert tx_builder.client == mock_client
        assert tx_builder.wallet == mock_wallet
    
    @pytest.mark.asyncio
    async def test_build_and_send_transaction_success(self, tx_builder):
        """Test build dan send transaction dengan jayanya"""
        # Create dummy instruction
        instruction = Instruction(
            program_id=Pubkey.default(),
            data=bytes([0, 1, 2]),
            accounts=[AccountMeta(Pubkey.default(), False, False)]
        )
        
        with patch('solana_bot.transaction.Transaction') as mock_tx_class, \
             patch('solana_bot.transaction.Message') as mock_msg_class:
            
            mock_tx = Mock()
            mock_tx_class.return_value = mock_tx
            
            signature = await tx_builder.build_and_send_transaction([instruction])
            
            assert signature == "test_signature_123"
            tx_builder.client.send_transaction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_build_and_send_transaction_no_wallet(self, tx_builder):
        """Test send transaction tanpa wallet loaded"""
        tx_builder.wallet.keypair = None
        
        instruction = Instruction(
            program_id=Pubkey.default(),
            data=bytes([0]),
            accounts=[]
        )
        
        signature = await tx_builder.build_and_send_transaction([instruction])
        assert signature is None
    
    @pytest.mark.asyncio
    async def test_build_and_send_transaction_error(self, tx_builder):
        """Test send transaction dengan error"""
        tx_builder.client.send_transaction = AsyncMock(side_effect=Exception("Network Error"))
        
        instruction = Instruction(
            program_id=Pubkey.default(),
            data=bytes([0]),
            accounts=[]
        )
        
        with patch('solana_bot.transaction.Transaction'), \
             patch('solana_bot.transaction.Message'):
            signature = await tx_builder.build_and_send_transaction([instruction])
            assert signature is None
    
    @pytest.mark.asyncio
    async def test_confirm_transaction_success(self, tx_builder):
        """Test confirm transaction yang berjaya"""
        from solders.signature import Signature
        
        result = await tx_builder.confirm_transaction("test_sig", timeout=5)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_confirm_transaction_failed(self, tx_builder):
        """Test confirm transaction yang gagal"""
        mock_status = Mock()
        mock_status.err = "Transaction failed"
        mock_status_response = Mock()
        mock_status_response.value = [mock_status]
        tx_builder.client.get_signature_statuses = AsyncMock(return_value=mock_status_response)
        
        result = await tx_builder.confirm_transaction("test_sig", timeout=5)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_confirm_transaction_timeout(self, tx_builder):
        """Test confirm transaction timeout"""
        # Return None untuk simulate pending
        mock_status_response = Mock()
        mock_status_response.value = [None]
        tx_builder.client.get_signature_statuses = AsyncMock(return_value=mock_status_response)
        
        result = await tx_builder.confirm_transaction("test_sig", timeout=1)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_confirm_transaction_error(self, tx_builder):
        """Test confirm transaction dengan error"""
        tx_builder.client.get_signature_statuses = AsyncMock(side_effect=Exception("RPC Error"))
        
        result = await tx_builder.confirm_transaction("test_sig", timeout=5)
        assert result is False
