"""
Unit tests untuk solana_bot.price_tracker
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from solana_bot.price_tracker import PriceTracker
from solders.pubkey import Pubkey


@pytest.fixture
def mock_client():
    """Mock AsyncClient"""
    return AsyncMock()


@pytest.fixture
def mock_raydium():
    """Mock RaydiumSwap"""
    return Mock()


@pytest.fixture
def price_tracker(mock_client, mock_raydium):
    """PriceTracker instance"""
    return PriceTracker(mock_client, mock_raydium)


class TestPriceTracker:
    """Test suite untuk PriceTracker"""
    
    def test_initialization(self, price_tracker, mock_client, mock_raydium):
        """Test inisialisasi PriceTracker"""
        assert price_tracker.client == mock_client
        assert price_tracker.raydium == mock_raydium
        assert isinstance(price_tracker.prices, dict)
        assert isinstance(price_tracker.tracking, dict)
        assert isinstance(price_tracker.callbacks, dict)
    
    @pytest.mark.asyncio
    async def test_start_tracking(self, price_tracker, mock_client):
        """Test memulakan price tracking"""
        token_mint = str(Pubkey.default())
        pool_address = str(Pubkey.default())
        
        # Mock get_pool_data to return valid data
        async def mock_get_pool_data(pool_pubkey):
            return {
                'price': 0.5,
                'base_reserve': 1000000,
                'quote_reserve': 500000,
                'base_decimal': 9,
                'quote_decimal': 9
            }
        
        price_tracker.get_pool_data = mock_get_pool_data
        
        # Start tracking in background
        import asyncio
        task = asyncio.create_task(
            price_tracker.start_tracking(token_mint, pool_address, interval=0.1)
        )
        
        # Wait a bit for tracking to start
        await asyncio.sleep(0.2)
        
        # Stop tracking
        price_tracker.stop_tracking(token_mint)
        
        # Wait for task to complete
        await asyncio.sleep(0.2)
        
        assert token_mint in price_tracker.prices
        assert price_tracker.tracking[token_mint] is False
    
    def test_stop_tracking(self, price_tracker):
        """Test menghentikan tracking"""
        token_mint = str(Pubkey.default())
        price_tracker.tracking[token_mint] = True
        
        price_tracker.stop_tracking(token_mint)
        assert price_tracker.tracking[token_mint] is False
    
    def test_register_callback(self, price_tracker):
        """Test mendaftar callback"""
        token_mint = str(Pubkey.default())
        
        def test_callback(mint, new_price, old_price):
            pass
        
        price_tracker.register_callback(token_mint, test_callback)
        
        assert token_mint in price_tracker.callbacks
        assert test_callback in price_tracker.callbacks[token_mint]
    
    @pytest.mark.asyncio
    async def test_trigger_callbacks_sync(self, price_tracker):
        """Test triggering sync callbacks"""
        token_mint = str(Pubkey.default())
        callback_called = []
        
        def test_callback(mint, new_price, old_price):
            callback_called.append((mint, new_price, old_price))
        
        price_tracker.register_callback(token_mint, test_callback)
        await price_tracker.trigger_callbacks(token_mint, 1.0, 0.5)
        
        assert len(callback_called) == 1
        assert callback_called[0] == (token_mint, 1.0, 0.5)
    
    @pytest.mark.asyncio
    async def test_trigger_callbacks_async(self, price_tracker):
        """Test triggering async callbacks"""
        token_mint = str(Pubkey.default())
        callback_called = []
        
        async def test_callback(mint, new_price, old_price):
            callback_called.append((mint, new_price, old_price))
        
        price_tracker.register_callback(token_mint, test_callback)
        await price_tracker.trigger_callbacks(token_mint, 1.0, 0.5)
        
        assert len(callback_called) == 1
    
    @pytest.mark.asyncio
    async def test_get_pool_data_success(self, price_tracker, mock_client):
        """Test mendapatkan pool data dengan jayanya"""
        # Mock account info
        mock_amm_data = bytes([0] * 752)
        mock_account = Mock()
        mock_account.value.data = mock_amm_data
        mock_client.get_account_info = AsyncMock(return_value=mock_account)
        
        # Mock token account balances
        mock_balance = Mock()
        mock_balance.value.amount = "1000000000"
        mock_client.get_token_account_balance = AsyncMock(return_value=mock_balance)
        
        with patch('solana_bot.price_tracker.AMM_INFO_LAYOUT_V4') as mock_layout:
            mock_parsed = Mock()
            mock_parsed.base_decimal = 9
            mock_parsed.quote_decimal = 9
            mock_parsed.base_vault = bytes([1] * 32)  # Non-zero address
            mock_parsed.quote_vault = bytes([2] * 32)
            mock_layout.parse.return_value = mock_parsed
            
            pool_data = await price_tracker.get_pool_data(Pubkey.default())
            
            assert pool_data is not None
            assert 'price' in pool_data
            assert pool_data['price'] > 0
    
    @pytest.mark.asyncio
    async def test_get_pool_data_no_account(self, price_tracker, mock_client):
        """Test get pool data bila account tidak wujud"""
        mock_client.get_account_info = AsyncMock(return_value=Mock(value=None))
        
        pool_data = await price_tracker.get_pool_data(Pubkey.default())
        assert pool_data is None
    
    @pytest.mark.asyncio
    async def test_get_pool_data_invalid_vault(self, price_tracker, mock_client):
        """Test get pool data dengan vault address tidak sah"""
        mock_amm_data = bytes([0] * 752)
        mock_account = Mock()
        mock_account.value.data = mock_amm_data
        mock_client.get_account_info = AsyncMock(return_value=mock_account)
        
        with patch('solana_bot.price_tracker.AMM_INFO_LAYOUT_V4') as mock_layout:
            mock_parsed = Mock()
            mock_parsed.base_vault = bytes([0] * 32)  # Zero address (invalid)
            mock_parsed.quote_vault = bytes([0] * 32)
            mock_layout.parse.return_value = mock_parsed
            
            pool_data = await price_tracker.get_pool_data(Pubkey.default())
            assert pool_data is None
    
    def test_calculate_price(self, price_tracker):
        """Test pengiraan harga"""
        pool_data = {
            'base_reserve': 1000000000,  # 1 token (9 decimals)
            'quote_reserve': 500000000,  # 0.5 SOL (9 decimals)
            'base_decimal': 9,
            'quote_decimal': 9
        }
        
        price = price_tracker.calculate_price(pool_data)
        assert price == 0.5  # 0.5 SOL per token
    
    def test_calculate_price_zero_reserve(self, price_tracker):
        """Test calculate price dengan zero reserve"""
        pool_data = {
            'base_reserve': 0,
            'quote_reserve': 500000000,
            'base_decimal': 9,
            'quote_decimal': 9
        }
        
        price = price_tracker.calculate_price(pool_data)
        assert price == 0.0
    
    def test_calculate_price_none_data(self, price_tracker):
        """Test calculate price dengan None data"""
        price = price_tracker.calculate_price(None)
        assert price == 0.0
