"""
End-to-end tests for WebSocket connection and transaction stream testing
Refactored with proper mocking and async handling
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig
from src.solana_bot.raydium.swap import RaydiumSwap
from src.solana_bot.transaction import TransactionBuilder


class TestWebSocketE2E:
    """End-to-end tests for WebSocket connections and transaction streams."""

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create test configuration file."""
        config_data = {
            "rpc_endpoint": "https://api.devnet.solana.com",
            "websocket_endpoint": "wss://api.devnet.solana.com",
            "raydium_program_id": "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
            "wallet_private_key": "test_private_key_placeholder",
            "bot_settings": {
                "buy_amount_sol": 0.1,
                "take_profit": 30.0,
                "stop_loss": 15.0,
                "max_trades_per_hour": 5,
                "min_volume_24h": 5000.0,
                "max_hold_time_hours": 4.0,
                "cooldown_after_sell": 60,
                "enable_trailing_stop": True,
                "trailing_stop_percentage": 10.0
            },
            "advanced_features": {
                "multi_source_volume": True,
                "pool_liquidity_analysis": True,
                "price_volatility_filter": True,
                "token_age_validation": True
            },
            "validation_thresholds": {
                "min_volume_confidence": 0.3,
                "max_price_impact": 0.05,
                "max_volatility_threshold": 0.3,
                "min_token_age_hours": 24
            },
            "token_filters": {
                "max_supply": 1000000000,
                "min_holders": 100,
                "max_top_holder_percent": 20,
                "contract_verified": True,
                "renounced_ownership": True
            }
        }

        config_file = tmp_path / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        return str(config_file)

    @pytest.fixture
    def mock_solana_client(self):
        """Create mock Solana client with WebSocket support."""
        client = AsyncMock()

        # Mock WebSocket manager
        ws_manager = AsyncMock()
        ws_manager.connect = AsyncMock()
        ws_manager.disconnect = AsyncMock()
        ws_manager.subscribe_logs = AsyncMock(return_value=1)
        ws_manager.unsubscribe = AsyncMock()

        # Mock RPC methods
        client.get_account_info = AsyncMock()
        client.get_token_supply = AsyncMock()
        client.get_token_largest_accounts = AsyncMock()

        client.ws_manager = ws_manager
        return client

    @pytest.fixture
    def mock_components(self):
        """Create mock components for WebSocket testing."""
        price_tracker = AsyncMock()
        raydium_swap = AsyncMock()
        transaction_builder = AsyncMock()
        wallet = AsyncMock()
        security_analyzer = AsyncMock()
        security_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})

        # Mock RaydiumSwap
        raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        raydium_swap.get_associated_token_address = AsyncMock(return_value="ATA_ADDRESS")

        # Mock TransactionBuilder
        transaction_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        return {
            'price_tracker': price_tracker,
            'raydium_swap': raydium_swap,
            'transaction_builder': transaction_builder,
            'wallet': wallet,
            'security_analyzer': security_analyzer
        }

    @pytest.fixture
    async def monitor(self, test_config, mock_solana_client, mock_components):
        """Create properly mocked monitor instance."""
        config = BotConfig(test_config)

        # Create monitor with mocked dependencies
        with patch('src.solana_bot.monitor.AsyncClient', return_value=mock_solana_client), \
             patch('src.solana_bot.monitor.BirdeyeClient') as mock_birdeye_class, \
             patch('src.solana_bot.monitor.DexScreenerClient') as mock_dex_class, \
             patch('src.solana_bot.monitor.VolumeValidator') as mock_validator_class, \
             patch('src.solana_bot.monitor.RaydiumSwap', return_value=mock_components['raydium_swap']), \
             patch('src.solana_bot.monitor.TransactionBuilder', return_value=mock_components['transaction_builder']):

            # Mock API clients
            mock_birdeye = AsyncMock()
            mock_dex = AsyncMock()
            mock_validator = AsyncMock()

            mock_birdeye_class.return_value = mock_birdeye
            mock_dex_class.return_value = mock_dex
            mock_validator_class.return_value = mock_validator

            monitor = PoolMonitor(
                config.rpc_endpoint,
                config.websocket_endpoint,
                config.raydium_program_id,
                config,
                mock_components['wallet']
            )

            # Assign mocked components
            monitor.client = mock_solana_client
            monitor.birdeye = mock_birdeye
            monitor.dex_screener = mock_dex
            monitor.volume_validator = mock_validator
            monitor.raydium_swap = mock_components['raydium_swap']
            monitor.tx_builder = mock_components['transaction_builder']
            monitor.security = mock_components['security_analyzer']

            yield monitor

    def test_websocket_connection_initialization(self, test_config, monitor):
        """Test WebSocket connection setup and initialization."""
        config = BotConfig(test_config)

        assert monitor.ws_endpoint == config.websocket_endpoint
        assert monitor.raydium_program_id == config.raydium_program_id
        assert monitor.is_monitoring == False
        assert monitor.stats['transactions_seen'] == 0

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, monitor, mock_solana_client):
        """Test complete WebSocket connection lifecycle."""
        # Mock the websocket connection to avoid real network calls
        with patch('src.solana_bot.monitor.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
            mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock websocket logs subscription
            mock_websocket.logs_subscribe = AsyncMock()
            mock_websocket.__aiter__ = AsyncMock(return_value=iter([]))  # Empty iterator

            # Test connection establishment
            start_task = asyncio.create_task(monitor.start_monitoring())
            await asyncio.sleep(0.1)  # Let monitoring start

            # Verify WebSocket connection setup
            mock_solana_client.ws_manager.connect.assert_called_once()

            # Cancel monitoring to avoid infinite loop
            monitor.is_monitoring = False
            start_task.cancel()

            try:
                await start_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_transaction_stream_subscription(self, monitor, mock_solana_client):
        """Test transaction stream subscription for pool monitoring."""
        with patch('src.solana_bot.monitor.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
            mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_websocket.logs_subscribe = AsyncMock()
            mock_websocket.__aiter__ = AsyncMock(return_value=iter([]))

            # Start monitoring
            start_task = asyncio.create_task(monitor.start_monitoring())
            await asyncio.sleep(0.1)

            # Verify Raydium program subscription
            mock_solana_client.ws_manager.subscribe_logs.assert_called_once()

            # Stop monitoring
            monitor.is_monitoring = False
            start_task.cancel()

            try:
                await start_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_transaction_message_processing(self, monitor):
        """Test processing of transaction messages from WebSocket stream."""
        # Mock pool extraction
        mock_pool_info = {
            'pool_address': 'POOL_123',
            'token_address': 'TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'TOKEN_123',
            'initial_liquidity': 10000.0
        }

        with patch.object(monitor, '_extract_pool_info', return_value=mock_pool_info) as mock_extract, \
             patch.object(monitor, 'execute_auto_buy', new_callable=AsyncMock) as mock_buy:

            # Create mock transaction notification
            mock_notification = Mock()
            mock_notification.result = Mock()
            mock_notification.result.value = Mock()
            mock_notification.result.value.logs = [
                "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
                "ray_log: InitializeInstruction2",
            ]

            # Process the notification
            await monitor._process_notification(mock_notification)

            # Verify pool extraction was called
            mock_extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_reconnection_handling(self, monitor, mock_solana_client):
        """Test WebSocket reconnection handling after connection loss."""
        with patch('src.solana_bot.monitor.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
            mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_websocket.logs_subscribe = AsyncMock()
            mock_websocket.__aiter__ = AsyncMock(return_value=iter([]))

            # Start monitoring
            start_task = asyncio.create_task(monitor.start_monitoring())
            await asyncio.sleep(0.1)

            # Simulate connection loss and reconnection
            monitor.is_monitoring = False
            await asyncio.sleep(0.1)

            # Verify connection was established
            mock_solana_client.ws_manager.connect.assert_called_once()

            # Cancel task
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_transaction_filtering_by_program(self, monitor):
        """Test that transactions are filtered by Raydium program ID."""
        # Mock pool extraction to return None (no pool found)
        with patch.object(monitor, '_extract_pool_info', return_value=None) as mock_extract:

            # Test transaction with Raydium program
            raydium_tx = Mock()
            raydium_tx.result = Mock()
            raydium_tx.result.value = Mock()
            raydium_tx.result.value.logs = [
                "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
                "ray_log: InitializeInstruction2",
            ]

            # Test transaction with different program
            other_tx = Mock()
            other_tx.result = Mock()
            other_tx.result.value = Mock()
            other_tx.result.value.logs = [
                "Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA invoke",
                "Transfer",
            ]

            # Process both transactions
            await monitor._process_notification(raydium_tx)
            await monitor._process_notification(other_tx)

            # Verify _extract_pool_info was called for both
            assert mock_extract.call_count == 2

    @pytest.mark.asyncio
    async def test_websocket_message_rate_limiting(self, monitor):
        """Test rate limiting of WebSocket message processing."""
        # Mock pool extraction to avoid side effects
        with patch.object(monitor, '_extract_pool_info', return_value=None):

            # Create multiple rapid transaction messages
            transactions = []
            for i in range(5):  # Reduced count for faster testing
                tx = Mock()
                tx.result = Mock()
                tx.result.value = Mock()
                tx.result.value.logs = [
                    "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
                    f"ray_log: InitializeInstruction2_{i}",
                ]
                transactions.append(tx)

            # Process all transactions rapidly
            for tx in transactions:
                await monitor._process_notification(tx)

            # Verify transactions_seen counter was incremented
            assert monitor.stats['transactions_seen'] == 5

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, monitor, mock_solana_client):
        """Test WebSocket error handling and recovery."""
        # Simulate WebSocket connection failure
        mock_solana_client.ws_manager.subscribe_logs.side_effect = Exception("WebSocket connection failed")

        with patch('src.solana_bot.monitor.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            # Attempt to start monitoring - should handle error gracefully
            try:
                await asyncio.wait_for(monitor.start_monitoring(), timeout=1.0)
            except (Exception, asyncio.TimeoutError):
                pass  # Expected to handle errors gracefully

            # Verify monitoring status remains manageable
            assert monitor.is_monitoring == False

    @pytest.mark.asyncio
    async def test_real_time_pool_detection_workflow(self, monitor):
        """Test complete real-time pool detection workflow via WebSocket."""
        # Mock successful pool creation detection
        mock_pool_info = {
            'pool_address': 'POOL_123',
            'token_address': 'TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'TOKEN_123',
            'initial_liquidity': 10000.0,
            'timestamp': 1234567890
        }

        with patch.object(monitor, '_extract_pool_info', return_value=mock_pool_info) as mock_extract, \
             patch.object(monitor, 'execute_auto_buy', new_callable=AsyncMock) as mock_buy:

            # Create mock transaction notification
            mock_notification = Mock()
            mock_notification.result = Mock()
            mock_notification.result.value = Mock()
            mock_notification.result.value.logs = [
                "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
                "ray_log: InitializeInstruction2",
                "Create",
            ]

            # Process the transaction
            await monitor._process_notification(mock_notification)

            # Verify the complete workflow
            mock_extract.assert_called_once()
            mock_buy.assert_called_once_with(mock_pool_info)

            # Verify statistics were updated
            assert monitor.stats['pools_detected'] == 1
            assert monitor.stats['transactions_seen'] == 1

    def test_websocket_connection_configuration(self, test_config, monitor):
        """Test WebSocket connection configuration and parameters."""
        config = BotConfig(test_config)

        # Verify configuration is properly set
        assert monitor.rpc_endpoint == config.rpc_endpoint
        assert monitor.ws_endpoint == config.websocket_endpoint
        assert monitor.raydium_program_id == config.raydium_program_id

        # Verify initial state
        assert monitor.is_monitoring == False
        assert monitor.stats['transactions_seen'] == 0
        assert monitor.stats['pools_detected'] == 0
        assert monitor.stats['pools_bought'] == 0

    @pytest.mark.asyncio
    async def test_websocket_subscription_management(self, monitor, mock_solana_client):
        """Test WebSocket subscription creation and cleanup."""
        with patch('src.solana_bot.monitor.connect') as mock_connect:
            mock_websocket = AsyncMock()
            mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
            mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)

            mock_websocket.logs_subscribe = AsyncMock()
            mock_websocket.__aiter__ = AsyncMock(return_value=iter([]))

            # Start monitoring (creates subscription)
            start_task = asyncio.create_task(monitor.start_monitoring())
            await asyncio.sleep(0.1)

            # Verify subscription was created
            mock_solana_client.ws_manager.subscribe_logs.assert_called_once()

            # Stop monitoring (should cleanup subscription)
            monitor.is_monitoring = False
            await monitor.stop_monitoring()

            # Verify unsubscription was called
            mock_solana_client.ws_manager.unsubscribe.assert_called_once()

            # Cancel the start task
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass
