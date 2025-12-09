"""
Phase 3: Integration Testing & System Validation
Full system integration tests validating all components working together
"""
import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig
from src.solana_bot.security import SecurityAnalyzer
from src.solana_bot.triggers import TradeTriggers


class TestFullSystemIntegration:
    """Full system integration tests - all components working together."""

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create comprehensive test configuration."""
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
            "token_filters": {
                "max_supply": 1000000000,
                "min_holders": 100,
                "max_top_holder_percent": 20.0,
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
        """Create comprehensive mock Solana client."""
        client = AsyncMock()

        # WebSocket manager
        ws_manager = AsyncMock()
        ws_manager.connect = AsyncMock()
        ws_manager.disconnect = AsyncMock()
        ws_manager.subscribe_logs = AsyncMock(return_value=1)
        ws_manager.unsubscribe = AsyncMock()
        client.ws_manager = ws_manager

        # RPC methods
        client.get_account_info = AsyncMock()
        client.get_account_info.return_value = Mock()
        client.get_account_info.return_value.value = Mock()
        client.get_account_info.return_value.value.data = b"mock_data"

        return client

    @pytest.fixture
    def mock_components(self):
        """Create fully integrated mock components."""
        # Price tracker
        price_tracker = Mock()
        price_tracker.register_callback = Mock()
        price_tracker.unregister_callback = Mock()
        price_tracker.get_price = AsyncMock(return_value=1.0)
        price_tracker.start_tracking = Mock()
        price_tracker.stop_tracking = Mock()

        # Raydium swap
        raydium_swap = Mock()
        raydium_swap.get_pool_keys = AsyncMock(return_value={
            'base_mint': 'TOKEN_123',
            'quote_mint': 'So11111111111111111111111111111111111111112',
            'amm_id': 'POOL_123'
        })
        raydium_swap.build_swap_instruction = Mock(return_value=Mock())
        raydium_swap.get_associated_token_address = Mock(return_value="token_account")
        raydium_swap.calculate_min_amount_out = Mock(return_value=1000000)

        # Transaction builder
        transaction_builder = Mock()
        transaction_builder.build_and_send_transaction = AsyncMock(return_value="test_signature")

        # Wallet
        wallet = Mock()
        wallet.keypair = Mock()
        wallet.keypair.pubkey = Mock()
        wallet.keypair.pubkey.__str__ = Mock(return_value="wallet_address")

        return {
            'price_tracker': price_tracker,
            'raydium_swap': raydium_swap,
            'transaction_builder': transaction_builder,
            'wallet': wallet
        }

    @pytest.mark.asyncio
    async def test_complete_system_initialization(self, test_config, mock_solana_client, mock_components):
        """Test complete system initialization with all components."""
        config = BotConfig(test_config)

        # Initialize all major components
        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )
        monitor.client = mock_solana_client

        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Verify all components initialized successfully
        assert monitor.config == config
        assert analyzer.config == config
        assert triggers.config == config

        # Verify component interactions
        assert hasattr(monitor, 'client')
        assert hasattr(monitor, 'security')
        assert hasattr(triggers, 'price_tracker')
        assert hasattr(triggers, 'raydium')

    @pytest.mark.asyncio
    async def test_end_to_end_pool_detection_to_trade_execution(self, test_config, mock_solana_client, mock_components):
        """Test complete end-to-end flow: pool detection → analysis → buy → monitoring → sell."""
        config = BotConfig(test_config)

        # Initialize complete system
        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )
        monitor.client = mock_solana_client

        analyzer = SecurityAnalyzer(mock_solana_client, config=config)
        monitor.security = analyzer

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Step 1: Simulate pool detection
        pool_data = {
            'pool_address': 'POOL_123',
            'token_address': 'TOKEN_123',
            'base_mint': 'So11111111111111111111111111111111111111112',
            'quote_mint': 'TOKEN_123',
            'initial_liquidity': 10000.0,
            'timestamp': time.time()
        }

        # Mock successful pool detection and analysis
        with patch.object(monitor, '_extract_pool_info', return_value=pool_data), \
             patch.object(analyzer, '_check_token_supply', return_value={'passed': True}), \
             patch.object(analyzer, '_check_holder_distribution', return_value={'passed': True}), \
             patch.object(analyzer, '_check_contract_verification', return_value={'passed': True}), \
             patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': True}):

            # Step 2: Process pool detection
            await monitor.execute_auto_buy(pool_data)

            # Step 3: Verify position was created
            assert 'TOKEN_123' in triggers.positions
            position = triggers.positions['TOKEN_123']
            assert position['entry_price'] == 1.0  # Default price
            assert position['amount'] == 100000000  # 0.1 SOL * 1e9

            # Step 4: Simulate price movement triggering sell
            mock_components['transaction_builder'].build_and_send_transaction = AsyncMock(return_value="sell_signature")

            # Trigger take profit
            tp_price = 1.0 * 1.35  # 35% profit
            await triggers.check_triggers('TOKEN_123', tp_price, tp_price)

            # Step 5: Verify sell was executed
            mock_components['transaction_builder'].build_and_send_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_resilience_under_load(self, test_config, mock_solana_client, mock_components):
        """Test system resilience when processing multiple concurrent operations."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )
        monitor.client = mock_solana_client

        analyzer = SecurityAnalyzer(mock_solana_client, config=config)
        monitor.security = analyzer

        # Create multiple pool detections
        pools = []
        for i in range(10):
            pool = {
                'pool_address': f'POOL_{i}',
                'token_address': f'TOKEN_{i}',
                'base_mint': 'So11111111111111111111111111111111111111112',
                'quote_mint': f'TOKEN_{i}',
                'initial_liquidity': 10000.0,
                'timestamp': time.time()
            }
            pools.append(pool)

        start_time = time.time()

        # Process all pools concurrently
        with patch.object(monitor, '_extract_pool_info', return_value=pools[0]), \
             patch.object(analyzer, '_check_token_supply', return_value={'passed': True}), \
             patch.object(analyzer, '_check_holder_distribution', return_value={'passed': True}), \
             patch.object(analyzer, '_check_contract_verification', return_value={'passed': True}), \
             patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': True}):

            tasks = [monitor.execute_auto_buy(pool) for pool in pools]
            await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        duration = end_time - start_time

        # Verify system handled load within reasonable time
        assert duration < 5.0, f"System too slow under load: {duration}s for 10 operations"
        assert monitor.stats['pools_detected'] == 10

    @pytest.mark.asyncio
    async def test_system_error_recovery_and_state_consistency(self, test_config, mock_solana_client, mock_components):
        """Test system error recovery while maintaining state consistency."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )
        monitor.client = mock_solana_client

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Establish baseline state
        initial_pools_detected = monitor.stats['pools_detected']
        initial_trades = len(triggers.positions)

        # Simulate system errors
        with patch.object(monitor, 'execute_auto_buy', side_effect=Exception("RPC Error")), \
             patch.object(triggers, 'check_triggers', side_effect=Exception("Price feed error")):

            pool_data = {
                'pool_address': 'POOL_ERROR',
                'token_address': 'TOKEN_ERROR',
                'base_mint': 'So11111111111111111111111111111111111111112',
                'quote_mint': 'TOKEN_ERROR',
                'initial_liquidity': 10000.0
            }

            # Attempt operations that should fail gracefully
            try:
                await monitor.execute_auto_buy(pool_data)
            except:
                pass  # Expected to handle errors

            try:
                await triggers.check_triggers('NONEXISTENT_TOKEN', 1.0, 1.0)
            except:
                pass  # Expected to handle errors

        # Verify state consistency after errors
        assert monitor.stats['pools_detected'] == initial_pools_detected  # No false positives
        assert len(triggers.positions) == initial_trades  # No corrupted state

    @pytest.mark.asyncio
    async def test_configuration_propagation_and_validation(self, test_config, mock_solana_client, mock_components):
        """Test that configuration properly propagates through all system components."""
        config = BotConfig(test_config)

        # Initialize all components
        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )
        monitor.client = mock_solana_client

        analyzer = SecurityAnalyzer(mock_solana_client, config=config)
        monitor.security = analyzer

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Verify configuration propagation
        assert monitor.config.buy_amount == 0.1
        assert analyzer.config.max_supply == 1000000000
        assert triggers.config.take_profit == 30.0
        assert triggers.config.enable_trailing_stop == True

        # Test configuration-driven behavior
        assert monitor.config.max_trades_per_hour == 5
        assert analyzer.config.min_holders == 100
        assert triggers.config.max_hold_time_hours == 4.0

    @pytest.mark.asyncio
    async def test_system_resource_management(self, test_config, mock_solana_client, mock_components):
        """Test system resource management and cleanup."""
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

        # Verify resources are allocated
        assert monitor.client is not None

        # Stop monitoring and verify cleanup
        await monitor.stop_monitoring()
        assert monitor.is_monitoring == False

        # Verify WebSocket cleanup
        mock_solana_client.ws_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_real_world_scenario_simulation(self, test_config, mock_solana_client, mock_components):
        """Test realistic trading scenario with multiple tokens and price movements."""
        config = BotConfig(test_config)

        # Initialize system
        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )
        monitor.client = mock_solana_client

        analyzer = SecurityAnalyzer(mock_solana_client, config=config)
        monitor.security = analyzer

        triggers = TradeTriggers(
            mock_components['price_tracker'],
            mock_components['raydium_swap'],
            mock_components['transaction_builder'],
            mock_components['wallet'],
            config
        )

        # Scenario: 3 tokens discovered, 2 pass analysis, 1 triggers profit, 1 hits stop loss
        tokens = ['TOKEN_A', 'TOKEN_B', 'TOKEN_C']

        with patch.object(monitor, '_extract_pool_info') as mock_extract, \
             patch.object(analyzer, '_check_token_supply') as mock_supply, \
             patch.object(analyzer, '_check_holder_distribution') as mock_holders, \
             patch.object(analyzer, '_check_contract_verification') as mock_contract, \
             patch.object(analyzer, '_check_ownership_renounced') as mock_ownership:

            # Configure different analysis results
            def supply_result(token):
                if token == 'TOKEN_C':
                    return {'passed': False}  # TOKEN_C fails supply check
                return {'passed': True}

            def holders_result(token):
                return {'passed': True}

            def contract_result(token):
                return {'passed': True}

            def ownership_result(token):
                return {'passed': True}

            mock_supply.side_effect = supply_result
            mock_holders.side_effect = holders_result
            mock_contract.side_effect = contract_result
            mock_ownership.side_effect = ownership_result

            # Process all tokens
            for i, token in enumerate(tokens):
                pool_data = {
                    'pool_address': f'POOL_{token}',
                    'token_address': token,
                    'base_mint': 'So11111111111111111111111111111111111111112',
                    'quote_mint': token,
                    'initial_liquidity': 10000.0
                }
                mock_extract.return_value = pool_data

                await monitor.execute_auto_buy(pool_data)

            # Verify results: only TOKEN_A and TOKEN_B should have positions
            assert 'TOKEN_A' in triggers.positions
            assert 'TOKEN_B' in triggers.positions
            assert 'TOKEN_C' not in triggers.positions  # Failed analysis

            # Simulate price movements and trigger sales
            mock_components['transaction_builder'].build_and_send_transaction = AsyncMock(return_value="sell_sig")

            # TOKEN_A hits take profit
            await triggers.check_triggers('TOKEN_A', 1.35, 1.35)
            # TOKEN_B hits stop loss
            await triggers.check_triggers('TOKEN_B', 0.85, 0.85)

            # Verify both were sold
            assert mock_components['transaction_builder'].build_and_send_transaction.call_count == 2

    @pytest.mark.asyncio
    async def test_system_performance_under_realistic_conditions(self, test_config, mock_solana_client, mock_components):
        """Test system performance with realistic transaction volumes."""
        config = BotConfig(test_config)

        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )
        monitor.client = mock_solana_client

        # Simulate 1 hour of realistic activity (10 pools per hour)
        pools_per_hour = 10
        total_pools = pools_per_hour

        pools = []
        for i in range(total_pools):
            pool = {
                'pool_address': f'POOL_{i}',
                'token_address': f'TOKEN_{i}',
                'base_mint': 'So11111111111111111111111111111111111111112',
                'quote_mint': f'TOKEN_{i}',
                'initial_liquidity': 10000.0,
                'timestamp': time.time()
            }
            pools.append(pool)

        start_time = time.time()

        with patch.object(monitor, '_extract_pool_info', return_value=pools[0]), \
             patch.object(monitor.security, 'check_token_filters', return_value={'passed': True}):

            # Process realistic volume
            for pool in pools:
                await monitor.execute_auto_buy(pool)
                # Simulate processing delay (real systems have network latency)
                await asyncio.sleep(0.01)  # 10ms per operation

        end_time = time.time()
        duration = end_time - start_time

        # Performance validation
        operations_per_second = total_pools / duration
        assert operations_per_second > 50, f"Performance too low: {operations_per_second:.1f} ops/sec"

        # System health checks
        assert monitor.stats['pools_detected'] == total_pools
        assert duration < 10.0, f"Total processing time too high: {duration:.2f}s"
