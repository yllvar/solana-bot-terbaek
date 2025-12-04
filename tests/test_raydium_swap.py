"""
Unit tests untuk solana_bot.raydium.swap
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from solana_bot.raydium.swap import RaydiumSwap
from solders.pubkey import Pubkey
from solders.keypair import Keypair


@pytest.fixture
def mock_client():
    """Mock AsyncClient"""
    return AsyncMock()


@pytest.fixture
def mock_wallet():
    """Mock WalletManager"""
    wallet = Mock()
    wallet.keypair = Keypair()
    return wallet


@pytest.fixture
def raydium_swap(mock_client, mock_wallet):
    """RaydiumSwap instance"""
    return RaydiumSwap(mock_client, mock_wallet)


class TestRaydiumSwap:
    """Test suite untuk RaydiumSwap"""
    
    def test_initialization(self, raydium_swap, mock_client, mock_wallet):
        """Test inisialisasi RaydiumSwap"""
        assert raydium_swap.client == mock_client
        assert raydium_swap.wallet == mock_wallet
        assert raydium_swap.program_id is not None
    
    def test_calculate_min_amount_out(self, raydium_swap):
        """Test pengiraan min amount out dengan slippage"""
        expected_amount = 1000000
        slippage_bps = 500  # 5%
        
        min_out = raydium_swap.calculate_min_amount_out(expected_amount, slippage_bps)
        assert min_out == 950000  # 95% of expected
    
    def test_calculate_min_amount_out_zero_slippage(self, raydium_swap):
        """Test dengan zero slippage"""
        expected_amount = 1000000
        min_out = raydium_swap.calculate_min_amount_out(expected_amount, 0)
        assert min_out == 1000000
    
    def test_calculate_min_amount_out_high_slippage(self, raydium_swap):
        """Test dengan slippage tinggi"""
        expected_amount = 1000000
        slippage_bps = 1000  # 10%
        min_out = raydium_swap.calculate_min_amount_out(expected_amount, slippage_bps)
        assert min_out == 900000
    
    def test_build_swap_instruction(self, raydium_swap):
        """Test membina swap instruction"""
        pool_keys = {
            'amm_id': Pubkey.default(),
            'authority': Pubkey.default(),
            'open_orders': Pubkey.default(),
            'target_orders': Pubkey.default(),
            'base_vault': Pubkey.default(),
            'quote_vault': Pubkey.default(),
            'market_program_id': Pubkey.default(),
            'market_id': Pubkey.default(),
            'market_bids': Pubkey.default(),
            'market_asks': Pubkey.default(),
            'market_event_queue': Pubkey.default(),
            'market_base_vault': Pubkey.default(),
            'market_quote_vault': Pubkey.default(),
            'market_vault_signer': Pubkey.default(),
        }
        
        instruction = raydium_swap.build_swap_instruction(
            pool_keys,
            amount_in=1000000,
            min_amount_out=950000,
            token_account_in=Pubkey.default(),
            token_account_out=Pubkey.default(),
            owner=Pubkey.default()
        )
        
        assert instruction is not None
        assert len(instruction.accounts) == 18  # Raydium V4 memerlukan 18 accounts
    
    @pytest.mark.asyncio
    async def test_get_pool_keys_success(self, raydium_swap, mock_client):
        """Test mendapatkan pool keys dengan jayanya"""
        # Mock AMM account data
        mock_amm_data = bytes([0] * 752)  # AMM V4 size
        mock_amm_account = Mock()
        mock_amm_account.value.data = mock_amm_data
        
        # Mock Market account data
        mock_market_data = bytes([0] * 388)  # Market V3 size
        mock_market_account = Mock()
        mock_market_account.value.data = mock_market_data
        
        mock_client.get_account_info = AsyncMock(
            side_effect=[mock_amm_account, mock_market_account]
        )
        
        # Patch layouts untuk return mock data
        with patch('solana_bot.raydium.swap.AMM_INFO_LAYOUT_V4') as mock_amm_layout, \
             patch('solana_bot.raydium.swap.MARKET_LAYOUT_V3') as mock_market_layout:
            
            # Setup mock parsed data
            mock_amm_parsed = Mock()
            mock_amm_parsed.market_id = bytes([0] * 32)
            mock_amm_parsed.base_mint = bytes([0] * 32)
            mock_amm_parsed.quote_mint = bytes([0] * 32)
            mock_amm_parsed.lp_mint = bytes([0] * 32)
            mock_amm_parsed.base_decimal = 9
            mock_amm_parsed.quote_decimal = 9
            mock_amm_parsed.base_vault = bytes([0] * 32)
            mock_amm_parsed.quote_vault = bytes([0] * 32)
            mock_amm_parsed.open_orders = bytes([0] * 32)
            mock_amm_parsed.target_orders = bytes([0] * 32)
            mock_amm_parsed.market_program_id = bytes([0] * 32)
            
            mock_market_parsed = Mock()
            mock_market_parsed.bids = bytes([0] * 32)
            mock_market_parsed.asks = bytes([0] * 32)
            mock_market_parsed.event_queue = bytes([0] * 32)
            mock_market_parsed.base_vault = bytes([0] * 32)
            mock_market_parsed.quote_vault = bytes([0] * 32)
            mock_market_parsed.own_address = bytes([0] * 32)
            mock_market_parsed.vault_signer_nonce = 0
            
            mock_amm_layout.parse.return_value = mock_amm_parsed
            mock_market_layout.parse.return_value = mock_market_parsed
            
            pool_keys = await raydium_swap.get_pool_keys(str(Pubkey.default()))
            
            assert pool_keys is not None
            assert 'amm_id' in pool_keys
            assert 'base_vault' in pool_keys
    
    @pytest.mark.asyncio
    async def test_get_pool_keys_no_amm_account(self, raydium_swap, mock_client):
        """Test get pool keys bila AMM account tidak wujud"""
        mock_client.get_account_info = AsyncMock(return_value=Mock(value=None))
        
        pool_keys = await raydium_swap.get_pool_keys(str(Pubkey.default()))
        assert pool_keys is None
    
    @pytest.mark.asyncio
    async def test_get_pool_keys_error(self, raydium_swap, mock_client):
        """Test get pool keys dengan error"""
        mock_client.get_account_info = AsyncMock(side_effect=Exception("RPC Error"))
        
        pool_keys = await raydium_swap.get_pool_keys(str(Pubkey.default()))
        assert pool_keys is None
    
    def test_get_associated_token_address(self, raydium_swap):
        """Test mendapatkan ATA address"""
        owner = Pubkey.default()
        mint = Pubkey.default()
        
        with patch('solana_bot.raydium.swap.get_associated_token_address') as mock_ata:
            mock_ata.return_value = Pubkey.default()
            ata = raydium_swap.get_associated_token_address(owner, mint)
            assert ata is not None
            mock_ata.assert_called_once_with(owner, mint)
