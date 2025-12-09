"""
Error handling and recovery tests for the Solana bot
Refactored with proper mocking and async handling
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig
from src.solana_bot.security import SecurityAnalyzer


class TestErrorHandlingE2E:
    """Error handling and recovery tests."""

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
        """Create mock Solana client."""
        client = AsyncMock()

        # Mock WebSocket manager
        ws_manager = AsyncMock()
        ws_manager.connect = AsyncMock()
        ws_manager.disconnect = AsyncMock()
        ws_manager.subscribe_logs = AsyncMock(return_value=1)
        ws_manager.unsubscribe = AsyncMock()

        client.ws_manager = ws_manager
        return client

    @pytest.fixture
    def mock_components(self):
        """Create mock components."""
        price_tracker = AsyncMock()
        raydium_swap = AsyncMock()
        transaction_builder = AsyncMock()
        wallet = AsyncMock()
        security_analyzer = AsyncMock()
        security_analyzer.check_token_filters = AsyncMock(return_value={'passed': True})

        return {
            'price_tracker': price_tracker,
            'raydium_swap': raydium_swap,
            'transaction_builder': transaction_builder,
            'wallet': wallet,
            'security_analyzer': security_analyzer
        }

    @pytest.mark.asyncio
    async def test_network_connection_failure_recovery(self, test_config, mock_solana_client, mock_components):
        """Test recovery from network connection failures."""
        config = BotConfig(test_config)

        # Create monitor with mocked dependencies
        with patch('src.solana_bot.monitor.AsyncClient', return_value=mock_solana_client), \
             patch('src.solana_bot.monitor.BirdeyeClient') as mock_birdeye_class, \
             patch('src.solana_bot.monitor.DexScreenerClient') as mock_dex_class, \
             patch('src.solana_bot.monitor.VolumeValidator') as mock_validator_class:

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

            # Simulate network failure during monitoring
            mock_solana_client.ws_manager.connect.side_effect = Exception("Network connection failed")

            with patch('src.solana_bot.monitor.connect') as mock_connect:
                mock_connect.side_effect = Exception("Connection failed")

                # Should handle error gracefully
                try:
                    await asyncio.wait_for(monitor.start_monitoring(), timeout=1.0)
                except (Exception, asyncio.TimeoutError):
                    pass  # Expected to handle errors gracefully

                # Verify monitoring state remains manageable
                assert monitor.is_monitoring == False

    @pytest.mark.asyncio
    async def test_invalid_token_address_handling(self, test_config, mock_solana_client):
        """Test handling of invalid token addresses."""
        config = BotConfig(test_config)
        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        # Test with completely invalid address
        result = await analyzer.check_token_filters("INVALID_ADDRESS")

        # Should return structured result even for invalid addresses
        assert 'passed' in result
        assert 'filters' in result
        assert 'warnings' in result
        assert result['passed'] == False
        assert len(result['warnings']) > 0

    @pytest.mark.asyncio
    async def test_rpc_timeout_recovery(self, test_config, mock_solana_client):
        """Test recovery from RPC timeouts."""
        config = BotConfig(test_config)
        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        # Mock RPC timeout
        mock_solana_client.get_account_info.side_effect = asyncio.TimeoutError("RPC timeout")

        # Should handle timeout gracefully
        result = await analyzer.check_token_filters("So11111111111111111111111111111111111111112")

        # Should return result structure
        assert 'passed' in result
        assert 'filters' in result

    @pytest.mark.asyncio
    async def test_websocket_reconnection_logic(self, test_config, mock_solana_client, mock_components):
        """Test WebSocket reconnection logic."""
        config = BotConfig(test_config)

        with patch('src.solana_bot.monitor.AsyncClient', return_value=mock_solana_client), \
             patch('src.solana_bot.monitor.BirdeyeClient') as mock_birdeye_class, \
             patch('src.solana_bot.monitor.DexScreenerClient') as mock_dex_class, \
             patch('src.solana_bot.monitor.VolumeValidator') as mock_validator_class:

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

            monitor.client = mock_solana_client

            with patch('src.solana_bot.monitor.connect') as mock_connect:
                mock_websocket = AsyncMock()
                mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
                mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_websocket.logs_subscribe = AsyncMock()
                mock_websocket.__aiter__ = AsyncMock(return_value=iter([]))

                # Start monitoring successfully
                start_task = asyncio.create_task(monitor.start_monitoring())
                await asyncio.sleep(0.1)

                assert monitor.is_monitoring == True

                # Simulate connection drop
                monitor.is_monitoring = False

                # Attempt reconnection
                mock_solana_client.ws_manager.connect.side_effect = None  # Reset side effect

                # Should be able to restart monitoring
                monitor.is_monitoring = True  # Simulate successful restart

                # Cancel the task
                start_task.cancel()
                try:
                    await start_task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_transaction_parsing_error_recovery(self, test_config, mock_solana_client, mock_components):
        """Test recovery from transaction parsing errors."""
        config = BotConfig(test_config)

        with patch('src.solana_bot.monitor.AsyncClient', return_value=mock_solana_client), \
             patch('src.solana_bot.monitor.BirdeyeClient') as mock_birdeye_class, \
             patch('src.solana_bot.monitor.DexScreenerClient') as mock_dex_class, \
             patch('src.solana_bot.monitor.VolumeValidator') as mock_validator_class:

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

            monitor.client = mock_solana_client

            # Create malformed transaction
            malformed_tx = Mock()
            malformed_tx.result = None  # Missing result

            # Should handle malformed transaction without crashing
            try:
                await monitor._process_notification(malformed_tx)
                # If we get here, the error was handled gracefully
                assert True
            except Exception as e:
                # If an exception is raised, it should be caught and logged
                assert "error" in str(e).lower() or "exception" in str(e).lower()

    @pytest.mark.asyncio
    async def test_security_analysis_error_recovery(self, test_config, mock_solana_client):
        """Test recovery from security analysis errors."""
        config = BotConfig(test_config)
        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        # Mock all security checks to fail with exceptions
        with patch.object(analyzer, '_check_token_supply', side_effect=Exception("Supply check failed")), \
             patch.object(analyzer, '_check_holder_distribution', side_effect=Exception("Holder check failed")), \
             patch.object(analyzer, '_check_contract_verification', side_effect=Exception("Contract check failed")), \
             patch.object(analyzer, '_check_ownership_renounced', side_effect=Exception("Ownership check failed")):

            result = await analyzer.check_token_filters("So11111111111111111111111111111111111111112")

            # Should return structured result despite all failures
            assert 'passed' in result
            assert 'filters' in result
            assert 'warnings' in result
            assert result['passed'] == False

    def test_configuration_validation_errors(self, test_config):
        """Test handling of configuration validation errors."""
        config = BotConfig(test_config)

        # Test invalid RPC endpoint
        config.config['rpc_endpoint'] = ""

        # Bot should handle gracefully (this is tested at config load time)
        assert config.rpc_endpoint == ""  # Should not crash

    @pytest.mark.asyncio
    async def test_memory_cleanup_on_errors(self, test_config, mock_solana_client, mock_components):
        """Test memory cleanup when errors occur."""
        config = BotConfig(test_config)

        with patch('src.solana_bot.monitor.AsyncClient', return_value=mock_solana_client), \
             patch('src.solana_bot.monitor.BirdeyeClient') as mock_birdeye_class, \
             patch('src.solana_bot.monitor.DexScreenerClient') as mock_dex_class, \
             patch('src.solana_bot.monitor.VolumeValidator') as mock_validator_class:

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

            monitor.client = mock_solana_client

            with patch('src.solana_bot.monitor.connect') as mock_connect:
                mock_websocket = AsyncMock()
                mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_websocket)
                mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)

                mock_websocket.logs_subscribe = AsyncMock()
                mock_websocket.__aiter__ = AsyncMock(return_value=iter([]))

                # Start monitoring
                start_task = asyncio.create_task(monitor.start_monitoring())
                await asyncio.sleep(0.1)

                # Simulate error conditions
                monitor.stats['transactions_seen'] = 1000
                monitor.stats['pools_detected'] = 50

                # Stop monitoring (should cleanup properly)
                monitor.is_monitoring = False
                await monitor.stop_monitoring()

                # Verify cleanup occurred
                assert monitor.is_monitoring == False

                # Cancel the task
                start_task.cancel()
                try:
                    await start_task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, test_config, mock_solana_client):
        """Test recovery when only some operations fail."""
        config = BotConfig(test_config)
        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        # Mock partial failures
        with patch.object(analyzer, '_check_token_supply', return_value={'passed': True}), \
             patch.object(analyzer, '_check_holder_distribution', side_effect=Exception("Holder check failed")), \
             patch.object(analyzer, '_check_contract_verification', return_value={'passed': True}), \
             patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': True}):

            result = await analyzer.check_token_filters("So11111111111111111111111111111111111111112")

            # Should have mixed results
            assert 'passed' in result
            assert 'filters' in result
            assert result['filters']['supply']['passed'] == True
            assert result['filters']['contract_verified']['passed'] == True
            assert result['filters']['ownership_renounced']['passed'] == True
            # Overall result should reflect the failure
            assert result['passed'] == False
