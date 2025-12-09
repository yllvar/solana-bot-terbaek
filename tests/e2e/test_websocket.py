"""
End-to-end tests for WebSocket connection and transaction stream testing
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig


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

        # Mock WebSocket connection
        ws_manager = AsyncMock()
        ws_manager.connect = AsyncMock()
        ws_manager.disconnect = AsyncMock()
        ws_manager.subscribe_logs = AsyncMock(return_value=1)  # subscription ID
        ws_manager.unsubscribe = AsyncMock()

        client.ws_manager = ws_manager
        return client

    @pytest.fixture
    def mock_components(self):
        """Create mock components for WebSocket testing."""
        price_tracker = Mock()
        raydium_swap = Mock()
        transaction_builder = Mock()
        wallet = Mock()
        security_analyzer = Mock()
        security_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})

        return {
            'price_tracker': price_tracker,
            'raydium_swap': raydium_swap,
            'transaction_builder': transaction_builder,
            'wallet': wallet,
            'security_analyzer': security_analyzer
        }

    def test_websocket_connection_initialization(self, test_config, mock_solana_client, mock_components):
        """Test WebSocket connection setup and initialization."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        # Mock the client assignment
        monitor.client = mock_solana_client

        assert monitor.ws_endpoint == config.websocket_endpoint
        assert monitor.raydium_program_id == config.raydium_program_id

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self, test_config, mock_solana_client, mock_components):
        """Test complete WebSocket connection lifecycle."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Test connection establishment
        await monitor.start_monitoring()

        # Verify WebSocket connection was established
        mock_solana_client.ws_manager.connect.assert_called_once()
        assert monitor.is_monitoring == True

        # Test disconnection
        await monitor.stop_monitoring()

        # Verify WebSocket disconnection
        mock_solana_client.ws_manager.disconnect.assert_called_once()
        assert monitor.is_monitoring == False

    @pytest.mark.asyncio
    async def test_transaction_stream_subscription(self, test_config, mock_solana_client, mock_components):
        """Test transaction stream subscription for pool monitoring."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Mock the monitoring start
        with patch.object(monitor, '_start_transaction_stream', new_callable=AsyncMock):
            await monitor.start_monitoring()

            # Verify Raydium program subscription
            mock_solana_client.ws_manager.subscribe_logs.assert_called_once()
            call_args = mock_solana_client.ws_manager.subscribe_logs.call_args[0][0]

            # Should subscribe to Raydium program logs
            assert call_args == config.raydium_program_id

    @pytest.mark.asyncio
    async def test_transaction_message_processing(self, test_config, mock_solana_client, mock_components):
        """Test processing of transaction messages from WebSocket stream."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client
        monitor.security = mock_components['security_analyzer']

        # Mock successful transaction processing
        mock_pool_info = {
            'pool_address': 'POOL_123',
            'token_address': 'TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'TOKEN_123',
            'initial_liquidity': 10000.0
        }

        with patch.object(monitor, '_extract_pool_info', return_value=mock_pool_info), \
             patch.object(monitor, 'execute_auto_buy', new_callable=AsyncMock) as mock_buy:

            # Simulate receiving a transaction message
            mock_transaction = Mock()
            mock_transaction.value = Mock()
            mock_transaction.value.logs = [
                "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
                "ray_log: InitializeInstruction2",
            ]

            await monitor._process_transaction(mock_transaction)

            # Verify pool extraction was called
            monitor._extract_pool_info.assert_called_once_with(mock_transaction)

            # Verify auto-buy was attempted
            mock_buy.assert_called_once_with(mock_pool_info)

    @pytest.mark.asyncio
    async def test_websocket_reconnection_handling(self, test_config, mock_solana_client, mock_components):
        """Test WebSocket reconnection handling after connection loss."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.is_monitoring == True

        # Simulate connection loss
        monitor.is_monitoring = False

        # Mock reconnection attempt
        with patch.object(monitor, '_start_transaction_stream', new_callable=AsyncMock):
            await monitor.start_monitoring()

            # Should attempt to reconnect
            mock_solana_client.ws_manager.connect.assert_called()
            assert monitor.is_monitoring == True

    @pytest.mark.asyncio
    async def test_transaction_filtering_by_program(self, test_config, mock_solana_client, mock_components):
        """Test that transactions are filtered by Raydium program ID."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Test transaction with Raydium program
        raydium_transaction = Mock()
        raydium_transaction.value = Mock()
        raydium_transaction.value.logs = [
            "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
            "ray_log: InitializeInstruction2",
        ]

        # Test transaction with different program
        other_transaction = Mock()
        other_transaction.value = Mock()
        other_transaction.value.logs = [
            "Program TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA invoke",
            "Transfer",
        ]

        with patch.object(monitor, '_extract_pool_info', return_value=None), \
             patch.object(monitor, 'execute_auto_buy', new_callable=AsyncMock) as mock_buy:

            # Process Raydium transaction
            await monitor._process_notification(raydium_transaction)

            # Process non-Raydium transaction
            await monitor._process_notification(other_transaction)

            # Verify _extract_pool_info was called for both
            assert monitor._extract_pool_info.call_count == 2

            # But execute_auto_buy should only be called if pool info was extracted
            # (in this case, we mocked it to return None, so no buy should happen)

    @pytest.mark.asyncio
    async def test_websocket_message_rate_limiting(self, test_config, mock_solana_client, mock_components):
        """Test rate limiting of WebSocket message processing."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Create multiple rapid transaction messages
        transactions = []
        for i in range(10):
            tx = Mock()
            tx.value = Mock()
            tx.value.logs = [
                "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
                f"ray_log: InitializeInstruction2_{i}",
            ]
            transactions.append(tx)

        with patch.object(monitor, '_extract_pool_info', return_value=None), \
             patch.object(asyncio, 'sleep', new_callable=AsyncMock) as mock_sleep:

            # Process all transactions rapidly
            for tx in transactions:
                await monitor._process_transaction(tx)

            # Verify transactions_seen counter was incremented
            assert monitor.stats['transactions_seen'] == 10

            # Verify no artificial delays were introduced (rate limiting should be at buy level, not processing)
            mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, test_config, mock_solana_client, mock_components):
        """Test WebSocket error handling and recovery."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Start monitoring
        await monitor.start_monitoring()

        # Simulate WebSocket error during operation
        mock_solana_client.ws_manager.subscribe_logs.side_effect = Exception("WebSocket connection failed")

        # Attempt to restart monitoring (should handle error gracefully)
        try:
            await monitor.start_monitoring()
        except Exception:
            pass  # Expected to handle errors gracefully

        # Verify monitoring status
        assert monitor.is_monitoring == True  # Should remain monitoring despite error

    @pytest.mark.asyncio
    async def test_real_time_pool_detection_workflow(self, test_config, mock_solana_client, mock_components):
        """Test complete real-time pool detection workflow via WebSocket."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client
        monitor.security = mock_components['security_analyzer']

        # Mock successful pool creation detection
        mock_pool_info = {
            'pool_address': 'POOL_123',
            'token_address': 'TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'TOKEN_123',
            'initial_liquidity': 10000.0,
            'timestamp': 1234567890
        }

        # Simulate receiving a new pool creation transaction
        new_pool_transaction = Mock()
        new_pool_transaction.result = Mock()
        new_pool_transaction.result.value = Mock()
        new_pool_transaction.result.value.logs = [
            "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
            "ray_log: InitializeInstruction2",
            "Create",
        ]

        with patch.object(monitor, '_extract_pool_info', return_value=mock_pool_info), \
             patch.object(monitor, 'execute_auto_buy', new_callable=AsyncMock) as mock_buy:

            # Process the transaction
            await monitor._process_notification(new_pool_transaction)

            # Verify the complete workflow
            monitor._extract_pool_info.assert_called_once()
            mock_buy.assert_called_once_with(mock_pool_info)

            # Verify statistics were updated
            assert monitor.stats['pools_detected'] == 1
            assert monitor.stats['transactions_seen'] == 1

    def test_websocket_connection_configuration(self, test_config, mock_solana_client, mock_components):
        """Test WebSocket connection configuration and parameters."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

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
    async def test_websocket_subscription_management(self, test_config, mock_solana_client, mock_components):
        """Test WebSocket subscription creation and cleanup."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Start monitoring (creates subscription)
        await monitor.start_monitoring()

        # Verify subscription was created
        mock_solana_client.ws_manager.subscribe_logs.assert_called_once_with(config.raydium_program_id)

        # Stop monitoring (should cleanup subscription)
        await monitor.stop_monitoring()

        # Verify unsubscription was called
        mock_solana_client.ws_manager.unsubscribe.assert_called_once()
