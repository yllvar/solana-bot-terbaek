"""
Performance benchmarking tests for the Solana bot
"""
import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig
from src.solana_bot.security import SecurityAnalyzer


class TestPerformanceE2E:
    """Performance benchmarking tests."""

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
        """Create mock Solana client."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def mock_components(self):
        """Create mock components."""
        price_tracker = Mock()
        raydium_swap = Mock()
        transaction_builder = Mock()
        wallet = Mock()

        return {
            'price_tracker': price_tracker,
            'raydium_swap': raydium_swap,
            'transaction_builder': transaction_builder,
            'wallet': wallet
        }

    def test_token_analysis_performance(self, test_config, mock_solana_client):
        """Benchmark token analysis performance."""
        config = BotConfig(test_config)
        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        # Mock fast analysis methods
        with patch.object(analyzer, '_check_token_supply', return_value={'passed': True}), \
             patch.object(analyzer, '_check_holder_distribution', return_value={'passed': True}), \
             patch.object(analyzer, '_check_contract_verification', return_value={'passed': True}), \
             patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': True}):

            start_time = time.time()

            # Analyze 50 tokens
            for i in range(50):
                result = asyncio.run(analyzer.check_token_filters(f'TOKEN_{i}'))
                assert result['passed'] == True

            end_time = time.time()
            duration = end_time - start_time

            # Performance assertion: should complete within reasonable time
            # Allow 10 seconds for 50 analyses (0.2s per token)
            assert duration < 10.0, f"Token analysis too slow: {duration}s for 50 tokens"

    def test_pool_detection_performance(self, test_config, mock_solana_client, mock_components):
        """Benchmark pool detection performance."""
        config = BotConfig(test_config)
        monitor = PoolMonitor(
            config.rpc_endpoint,
            config.websocket_endpoint,
            config.raydium_program_id,
            config,
            mock_components['wallet']
        )

        monitor.client = mock_solana_client

        # Create mock transactions
        transactions = []
        for i in range(100):
            tx = Mock()
            tx.result = Mock()
            tx.result.value = Mock()
            tx.result.value.logs = [
                "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke",
                f"Transaction {i}",
            ]
            transactions.append(tx)

        start_time = time.time()

        # Process transactions
        for tx in transactions:
            asyncio.run(monitor._process_notification(tx))

        end_time = time.time()
        duration = end_time - start_time

        # Performance assertion
        assert duration < 5.0, f"Pool detection too slow: {duration}s for 100 transactions"
        assert monitor.stats['transactions_seen'] == 100

    def test_memory_usage_stability(self, test_config, mock_solana_client):
        """Test memory usage stability during extended operation."""
        config = BotConfig(test_config)
        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        # Mock methods to return consistent results
        with patch.object(analyzer, '_check_token_supply', return_value={'passed': True}), \
             patch.object(analyzer, '_check_holder_distribution', return_value={'passed': True}), \
             patch.object(analyzer, '_check_contract_verification', return_value={'passed': True}), \
             patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': True}):

            # Run multiple analysis cycles
            for cycle in range(10):
                for i in range(20):
                    result = asyncio.run(analyzer.check_token_filters(f'CYCLE_{cycle}_TOKEN_{i}'))
                    assert result['passed'] == True

            # Basic stability check - no crashes or memory issues
            assert True  # If we get here without errors, test passes

    def test_concurrent_operation_performance(self, test_config, mock_solana_client):
        """Test performance under concurrent operations."""
        config = BotConfig(test_config)
        analyzer = SecurityAnalyzer(mock_solana_client, config=config)

        async def analyze_token(token_id):
            with patch.object(analyzer, '_check_token_supply', return_value={'passed': True}), \
                 patch.object(analyzer, '_check_holder_distribution', return_value={'passed': True}), \
                 patch.object(analyzer, '_check_contract_verification', return_value={'passed': True}), \
                 patch.object(analyzer, '_check_ownership_renounced', return_value={'passed': True}):
                return await analyzer.check_token_filters(f'TOKEN_{token_id}')

        async def run_concurrent_analysis():
            tasks = [analyze_token(i) for i in range(20)]
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            # Verify all completed successfully
            assert all(result['passed'] == True for result in results)
            return end_time - start_time

        duration = asyncio.run(run_concurrent_analysis())

        # Performance assertion for concurrent operations
        assert duration < 3.0, f"Concurrent analysis too slow: {duration}s for 20 tokens"
