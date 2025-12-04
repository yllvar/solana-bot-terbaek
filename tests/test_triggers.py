"""
Unit tests untuk solana_bot.triggers
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from solana_bot.triggers import TradeTriggers
from solders.pubkey import Pubkey


@pytest.fixture
def mock_price_tracker():
    """Mock PriceTracker"""
    tracker = Mock()
    tracker.register_callback = Mock()
    tracker.stop_tracking = Mock()
    return tracker


@pytest.fixture
def mock_raydium():
    """Mock RaydiumSwap"""
    raydium = Mock()
    raydium.calculate_min_amount_out = Mock(return_value=950000)
    raydium.get_associated_token_address = Mock(return_value=Pubkey.default())
    raydium.build_swap_instruction = Mock()
    raydium.get_pool_keys = AsyncMock(return_value={
        'base_mint': Pubkey.default(),
        'quote_mint': Pubkey.default(),
    })
    return raydium


@pytest.fixture
def mock_tx_builder():
    """Mock TransactionBuilder"""
    builder = AsyncMock()
    builder.build_and_send_transaction = AsyncMock(return_value="test_signature")
    return builder


@pytest.fixture
def mock_wallet():
    """Mock Wallet"""
    from solders.keypair import Keypair
    wallet = Mock()
    wallet.keypair = Keypair()
    return wallet


@pytest.fixture
def triggers(mock_price_tracker, mock_raydium, mock_tx_builder, mock_wallet):
    """TradeTriggers instance"""
    return TradeTriggers(mock_price_tracker, mock_raydium, mock_tx_builder, mock_wallet)


class TestTradeTriggers:
    """Test suite untuk TradeTriggers"""
    
    def test_initialization(self, triggers, mock_price_tracker, mock_raydium):
        """Test inisialisasi TradeTriggers"""
        assert triggers.price_tracker == mock_price_tracker
        assert triggers.raydium == mock_raydium
        assert isinstance(triggers.positions, dict)
        assert isinstance(triggers.triggers, dict)
    
    def test_open_position(self, triggers):
        """Test membuka posisi baharu"""
        token_mint = str(Pubkey.default())
        pool_address = str(Pubkey.default())
        
        triggers.open_position(
            token_mint=token_mint,
            entry_price=0.5,
            amount_token=1000,
            cost_sol=0.5,
            pool_address=pool_address
        )
        
        assert token_mint in triggers.positions
        assert triggers.positions[token_mint]['entry_price'] == 0.5
        assert triggers.positions[token_mint]['amount'] == 1000
        assert triggers.positions[token_mint]['cost_sol'] == 0.5
        assert triggers.positions[token_mint]['pool_address'] == pool_address
    
    def test_set_triggers(self, triggers, mock_price_tracker):
        """Test menetapkan TP/SL triggers"""
        token_mint = str(Pubkey.default())
        
        triggers.set_triggers(token_mint, take_profit_pct=100, stop_loss_pct=50)
        
        assert token_mint in triggers.triggers
        assert triggers.triggers[token_mint]['take_profit'] == 100
        assert triggers.triggers[token_mint]['stop_loss'] == 50
        assert triggers.triggers[token_mint]['enabled'] is True
        mock_price_tracker.register_callback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_triggers_take_profit(self, triggers):
        """Test trigger take profit"""
        token_mint = str(Pubkey.default())
        
        # Setup position and triggers
        triggers.open_position(token_mint, 0.5, 1000, 0.5, str(Pubkey.default()))
        triggers.set_triggers(token_mint, 100, 50)
        
        # Mock execute_sell
        triggers.execute_sell = AsyncMock()
        
        # Trigger dengan harga yang mencapai TP (100% gain = 2x)
        await triggers.check_triggers(token_mint, 1.0, 0.5)
        
        triggers.execute_sell.assert_called_once()
        call_args = triggers.execute_sell.call_args[0]
        assert call_args[1] == "TAKE_PROFIT"
    
    @pytest.mark.asyncio
    async def test_check_triggers_stop_loss(self, triggers):
        """Test trigger stop loss"""
        token_mint = str(Pubkey.default())
        
        triggers.open_position(token_mint, 1.0, 1000, 1.0, str(Pubkey.default()))
        triggers.set_triggers(token_mint, 100, 50)
        
        triggers.execute_sell = AsyncMock()
        
        # Trigger dengan harga yang mencapai SL (50% loss)
        await triggers.check_triggers(token_mint, 0.5, 1.0)
        
        triggers.execute_sell.assert_called_once()
        call_args = triggers.execute_sell.call_args[0]
        assert call_args[1] == "STOP_LOSS"
    
    @pytest.mark.asyncio
    async def test_check_triggers_no_trigger(self, triggers):
        """Test bila harga tidak mencapai trigger"""
        token_mint = str(Pubkey.default())
        
        triggers.open_position(token_mint, 1.0, 1000, 1.0, str(Pubkey.default()))
        triggers.set_triggers(token_mint, 100, 50)
        
        triggers.execute_sell = AsyncMock()
        
        # Harga masih dalam range
        await triggers.check_triggers(token_mint, 1.1, 1.0)
        
        triggers.execute_sell.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_check_triggers_disabled(self, triggers):
        """Test bila triggers disabled"""
        token_mint = str(Pubkey.default())
        
        triggers.open_position(token_mint, 1.0, 1000, 1.0, str(Pubkey.default()))
        triggers.set_triggers(token_mint, 100, 50)
        triggers.triggers[token_mint]['enabled'] = False
        
        triggers.execute_sell = AsyncMock()
        
        await triggers.check_triggers(token_mint, 2.0, 1.0)
        triggers.execute_sell.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_sell_success(self, triggers, mock_raydium, mock_tx_builder, mock_price_tracker):
        """Test execute sell dengan jayanya"""
        token_mint = str(Pubkey.default())
        pool_address = str(Pubkey.default())
        
        triggers.open_position(token_mint, 1.0, 1000000, 1.0, pool_address)
        triggers.set_triggers(token_mint, 100, 50)
        
        await triggers.execute_sell(token_mint, "TAKE_PROFIT", 2.0)
        
        # Verify transaction was sent
        mock_tx_builder.build_and_send_transaction.assert_called_once()
        
        # Verify position was closed
        assert token_mint not in triggers.positions
        
        # Verify tracking stopped
        mock_price_tracker.stop_tracking.assert_called_once_with(token_mint)
    
    @pytest.mark.asyncio
    async def test_execute_sell_no_pool_keys(self, triggers, mock_raydium):
        """Test execute sell bila pool keys tidak dijumpai"""
        token_mint = str(Pubkey.default())
        pool_address = str(Pubkey.default())
        
        triggers.open_position(token_mint, 1.0, 1000000, 1.0, pool_address)
        triggers.set_triggers(token_mint, 100, 50)
        
        # Mock get_pool_keys to return None
        mock_raydium.get_pool_keys = AsyncMock(return_value=None)
        
        await triggers.execute_sell(token_mint, "TAKE_PROFIT", 2.0)
        
        # Position should still exist (sell failed)
        assert token_mint in triggers.positions
    
    @pytest.mark.asyncio
    async def test_execute_sell_tx_failed(self, triggers, mock_tx_builder, mock_price_tracker):
        """Test execute sell bila transaksi gagal"""
        token_mint = str(Pubkey.default())
        pool_address = str(Pubkey.default())
        
        triggers.open_position(token_mint, 1.0, 1000000, 1.0, pool_address)
        triggers.set_triggers(token_mint, 100, 50)
        
        # Mock transaction failure
        mock_tx_builder.build_and_send_transaction = AsyncMock(return_value=None)
        
        await triggers.execute_sell(token_mint, "TAKE_PROFIT", 2.0)
        
        # Trigger should be re-enabled
        assert triggers.triggers[token_mint]['enabled'] is True
        
        # Position should still exist
        assert token_mint in triggers.positions
    
    @pytest.mark.asyncio
    async def test_execute_sell_no_position(self, triggers):
        """Test execute sell tanpa posisi"""
        token_mint = str(Pubkey.default())
        
        # Should not raise error
        await triggers.execute_sell(token_mint, "TAKE_PROFIT", 2.0)
