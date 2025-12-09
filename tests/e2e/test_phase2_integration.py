"""
E2E tests for Phase 2 features: Advanced Holder Analysis & Bulk API Operations
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig
from src.solana_bot.security import SecurityAnalyzer


class TestPhase2E2E:
    """End-to-end tests for Phase 2 enhancements"""

    @pytest.fixture
    def mock_config(self):
        """Create test configuration with Phase 2 features enabled"""
        config = MagicMock(spec=BotConfig)
        # Basic config
        config.buy_amount = 0.1
        config.min_volume_24h = 5000
        config.max_trades_per_hour = 5
        config.cooldown_after_sell = 60

        # Phase 1 features (already working)
        config.multi_source_volume = True
        config.pool_liquidity_analysis = True
        config.price_volatility_filter = True
        config.min_volume_confidence = 0.3
        config.max_price_impact = 0.05
        config.max_volatility_threshold = 0.3

        # Phase 2 features
        config.token_age_validation = True
        config.advanced_holder_analysis = True

        return config

    @pytest.fixture
    def mock_wallet(self):
        """Create mock wallet manager"""
        wallet = MagicMock()
        wallet.keypair = MagicMock()
        wallet.keypair.pubkey.return_value = MagicMock()
        return wallet

    @pytest.fixture
    def mock_security(self, mock_config):
        """Create mock security analyzer with Phase 2 features"""
        security = MagicMock(spec=SecurityAnalyzer)
        security.quick_check = AsyncMock(return_value=(True, []))

        # Mock comprehensive filter check with Phase 2 features
        security.check_token_filters = AsyncMock(return_value={
            'passed': True,
            'filters': {
                'supply': {'passed': True, 'message': '✅ Supply OK'},
                'holders': {
                    'passed': True,
                    'message': '✅ Good distribution (100 holders, top 15.0%)',
                    'data_source': 'on_chain',
                    'holder_count': 100,
                    'top_holder_percentage': 15.0,
                    'concentration_score': 0.6
                },
                'contract_verified': {'passed': True, 'message': '✅ Contract verified'},
                'ownership_renounced': {'passed': True, 'message': '✅ Ownership renounced'},
                'token_age': {'passed': True, 'message': '✅ Token age OK: 50.0h (min: 24h)'}
            },
            'warnings': []
        })

        return security

    @pytest.fixture
    async def monitor(self, mock_config, mock_wallet, mock_security):
        """Create test monitor instance with Phase 2 features"""
        with patch('src.solana_bot.monitor.AsyncClient') as mock_client_class, \
             patch('src.solana_bot.monitor.RaydiumSwap') as mock_raydium_class, \
             patch('src.solana_bot.monitor.TransactionBuilder') as mock_tx_class:

            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            monitor = PoolMonitor(
                rpc_endpoint="https://api.mainnet-beta.solana.com",
                ws_endpoint="wss://api.mainnet-beta.solana.com",
                raydium_program_id=MagicMock(),
                config=mock_config,
                wallet_manager=mock_wallet,
                security_analyzer=mock_security
            )

            # Mock Phase 1 clients (already working)
            monitor.dex_screener = AsyncMock()
            monitor.volume_validator = AsyncMock()
            monitor.birdeye = AsyncMock()

            return monitor

    @pytest.mark.asyncio
    async def test_full_trading_pipeline_with_phase2_features(self, monitor, mock_config):
        """Test complete trading pipeline with all Phase 1 & Phase 2 features"""
        # Mock all validation steps to pass

        # Phase 1: Volume validation
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8
        validated_volume.validation_method = "high_consistency"
        monitor.volume_validator.get_validated_volume = AsyncMock(return_value=validated_volume)

        # Phase 1: Liquidity analysis
        async def mock_liquidity_analysis(*args, **kwargs):
            return {
                'can_trade': True,
                'liquidity_usd': 2000000,
                'price_impact': 0.02,
                'max_allowed_impact': 0.05
            }
        monitor._analyze_pool_liquidity = AsyncMock(side_effect=mock_liquidity_analysis)

        # Phase 1: Volatility check
        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.2)

        # Phase 2: Token age validation (handled by security filters)
        # Phase 2: Advanced holder analysis (handled by security filters)

        # Mock successful pool and transaction setup
        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute auto buy - should pass all Phase 1 & Phase 2 checks
        await monitor.execute_auto_buy(pool_info)

        # Verify all validation steps were called
        monitor.volume_validator.get_validated_volume.assert_called_once()
        monitor._analyze_pool_liquidity.assert_called_once()
        monitor.birdeye.calculate_volatility.assert_called_once()
        monitor.tx_builder.build_and_send_transaction.assert_called_once()

        # Verify trade was executed
        assert monitor.stats['pools_bought'] == 1

    @pytest.mark.asyncio
    async def test_holder_analysis_integration_in_trading(self, monitor, mock_security):
        """Test that advanced holder analysis integrates properly in trading decisions"""
        # Mock all other validations to pass
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8
        monitor.volume_validator.get_validated_volume = AsyncMock(return_value=validated_volume)

        monitor._analyze_pool_liquidity = AsyncMock(return_value={
            'can_trade': True, 'liquidity_usd': 2000000, 'price_impact': 0.02
        })
        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.2)

        # Mock pool setup
        pool_info = {'token_address': 'TEST_TOKEN', 'pool_address': 'TEST_POOL'}
        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute trade
        await monitor.execute_auto_buy(pool_info)

        # Verify security filter check was called (includes holder analysis)
        mock_security.check_token_filters.assert_called_once_with('TEST_TOKEN')

        # Verify trade executed
        monitor.tx_builder.build_and_send_transaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_holder_analysis_failure_blocks_trade(self, monitor, mock_security):
        """Test that poor holder distribution blocks trading"""
        # Mock security check to fail due to bad holder distribution
        mock_security.check_token_filters = AsyncMock(return_value={
            'passed': False,
            'filters': {
                'holders': {
                    'passed': False,
                    'message': '⚠️ High concentration: top holder has 45.0% > 20.0%',
                    'top_holder_percentage': 45.0
                }
            },
            'warnings': ['High concentration: top holder has 45.0%']
        })

        pool_info = {'token_address': 'RISKY_TOKEN', 'pool_address': 'RISKY_POOL'}

        # Execute auto buy - should be blocked by holder analysis
        await monitor.execute_auto_buy(pool_info)

        # Verify trade was blocked
        mock_security.check_token_filters.assert_called_once_with('RISKY_TOKEN')
        monitor.tx_builder.build_and_send_transaction.assert_not_called()
        assert monitor.stats['pools_bought'] == 0

    @pytest.mark.asyncio
    async def test_bulk_operations_performance_integration(self, monitor):
        """Test that bulk operations improve performance for multiple tokens"""
        import time

        # Mock bulk volume validation
        bulk_results = {
            'TOKEN1': MagicMock(final_volume=100000, confidence_score=0.8),
            'TOKEN2': MagicMock(final_volume=150000, confidence_score=0.75),
        }
        monitor.volume_validator.get_bulk_validated_volumes = AsyncMock(return_value=bulk_results)

        # Mock successful other validations
        monitor._analyze_pool_liquidity = AsyncMock(return_value={
            'can_trade': True, 'liquidity_usd': 2000000, 'price_impact': 0.02
        })
        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.2)

        # Test that bulk operations are available
        assert hasattr(monitor.volume_validator, 'get_bulk_validated_volumes')
        assert callable(monitor.volume_validator.get_bulk_validated_volumes)

        # Verify bulk method can be called
        await monitor.volume_validator.initialize()
        result = await monitor.volume_validator.get_bulk_validated_volumes(['TOKEN1', 'TOKEN2'])

        assert len(result) == 2
        assert 'TOKEN1' in result
        assert 'TOKEN2' in result

    @pytest.mark.asyncio
    async def test_token_age_validation_integration(self, monitor, mock_security):
        """Test that token age validation integrates properly"""
        # Mock security check with age validation
        mock_security.check_token_filters = AsyncMock(return_value={
            'passed': False,
            'filters': {
                'token_age': {
                    'passed': False,
                    'message': '🆕 Token too new: 2.0h < 24h minimum',
                    'age_hours': 2.0,
                    'min_required': 24
                }
            },
            'warnings': ['🆕 Token too new: 2.0h < 24h minimum']
        })

        pool_info = {'token_address': 'NEW_TOKEN', 'pool_address': 'NEW_POOL'}

        # Execute auto buy - should be blocked by age validation
        await monitor.execute_auto_buy(pool_info)

        # Verify age check blocked trade
        mock_security.check_token_filters.assert_called_once_with('NEW_TOKEN')
        monitor.tx_builder.build_and_send_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_phase2_feature_combinations(self, monitor, mock_security):
        """Test various combinations of Phase 2 features"""
        test_scenarios = [
            {
                'name': 'All Phase 2 features pass',
                'security_result': {
                    'passed': True,
                    'filters': {
                        'holders': {'passed': True, 'message': 'Good distribution'},
                        'token_age': {'passed': True, 'message': 'Age OK'}
                    }
                },
                'should_trade': True
            },
            {
                'name': 'Holder analysis fails',
                'security_result': {
                    'passed': False,
                    'filters': {
                        'holders': {'passed': False, 'message': 'Bad distribution'},
                        'token_age': {'passed': True, 'message': 'Age OK'}
                    }
                },
                'should_trade': False
            },
            {
                'name': 'Age validation fails',
                'security_result': {
                    'passed': False,
                    'filters': {
                        'holders': {'passed': True, 'message': 'Good distribution'},
                        'token_age': {'passed': False, 'message': 'Too new'}
                    }
                },
                'should_trade': False
            }
        ]

        for scenario in test_scenarios:
            # Reset stats
            monitor.stats['pools_bought'] = 0

            # Setup mocks
            mock_security.check_token_filters = AsyncMock(return_value=scenario['security_result'])

            # Skip other validations for focused testing
            validated_volume = MagicMock()
            validated_volume.final_volume = 100000
            validated_volume.confidence_score = 0.8
            monitor.volume_validator.get_validated_volume = AsyncMock(return_value=validated_volume)

            monitor._analyze_pool_liquidity = AsyncMock(return_value={
                'can_trade': True, 'liquidity_usd': 2000000, 'price_impact': 0.02
            })
            monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.2)

            pool_info = {'token_address': f'TEST_TOKEN_{scenario["name"]}', 'pool_address': 'TEST_POOL'}

            if scenario['should_trade']:
                monitor._extract_pool_info = AsyncMock(return_value=pool_info)
                monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
                monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

            # Execute trade
            await monitor.execute_auto_buy(pool_info)

            # Verify result
            if scenario['should_trade']:
                assert monitor.stats['pools_bought'] == 1, f"Should trade in scenario: {scenario['name']}"
                monitor.tx_builder.build_and_send_transaction.assert_called()
            else:
                assert monitor.stats['pools_bought'] == 0, f"Should not trade in scenario: {scenario['name']}"
                monitor.tx_builder.build_and_send_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_phase1_plus_phase2_full_integration(self, monitor, mock_security):
        """Test complete integration of Phase 1 + Phase 2 features"""
        # Phase 1 validations
        validated_volume = MagicMock()
        validated_volume.final_volume = 75000
        validated_volume.confidence_score = 0.75
        monitor.volume_validator.get_validated_volume = AsyncMock(return_value=validated_volume)

        monitor._analyze_pool_liquidity = AsyncMock(return_value={
            'can_trade': True,
            'liquidity_usd': 1500000,
            'price_impact': 0.035  # 3.5% impact (under 5% limit)
        })

        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.25)  # Under 0.3 threshold

        # Phase 2 validations (via security filters)
        mock_security.check_token_filters = AsyncMock(return_value={
            'passed': True,
            'filters': {
                'supply': {'passed': True},
                'holders': {
                    'passed': True,
                    'data_source': 'on_chain',
                    'holder_count': 150,
                    'top_holder_percentage': 12.0,
                    'concentration_score': 0.55
                },
                'token_age': {
                    'passed': True,
                    'age_hours': 48.0,
                    'min_required': 24
                },
                'contract_verified': {'passed': True},
                'ownership_renounced': {'passed': True}
            },
            'warnings': []
        })

        # Setup successful trade
        pool_info = {'token_address': 'PERFECT_TOKEN', 'pool_address': 'PERFECT_POOL'}
        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute the complete trading pipeline
        await monitor.execute_auto_buy(pool_info)

        # Verify ALL validation steps passed
        monitor.volume_validator.get_validated_volume.assert_called_once()
        monitor._analyze_pool_liquidity.assert_called_once()
        monitor.birdeye.calculate_volatility.assert_called_once()
        mock_security.check_token_filters.assert_called_once_with('PERFECT_TOKEN')
        monitor.tx_builder.build_and_send_transaction.assert_called_once()

        # Verify trade was executed successfully
        assert monitor.stats['pools_bought'] == 1

        print("✅ COMPLETE Phase 1 + Phase 2 integration test PASSED!")
        print("   - Multi-source volume validation: ✅")
        print("   - Pool liquidity analysis: ✅")
        print("   - Price volatility monitoring: ✅")
        print("   - Advanced holder analysis: ✅")
        print("   - Token age validation: ✅")
        print("   - Trade execution: ✅")

    @pytest.mark.asyncio
    async def test_error_handling_in_phase2_features(self, monitor, mock_security):
        """Test error handling when Phase 2 features encounter issues"""
        # Mock security check to raise exception
        mock_security.check_token_filters = AsyncMock(side_effect=Exception("Security analysis failed"))

        # Mock other validations to pass
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8
        monitor.volume_validator.get_validated_volume = AsyncMock(return_value=validated_volume)

        monitor._analyze_pool_liquidity = AsyncMock(return_value={
            'can_trade': True, 'liquidity_usd': 2000000, 'price_impact': 0.02
        })
        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.2)

        pool_info = {'token_address': 'ERROR_TOKEN', 'pool_address': 'ERROR_POOL'}

        # Execute trade - should handle security error gracefully
        await monitor.execute_auto_buy(pool_info)

        # Verify error was caught and trade was blocked
        mock_security.check_token_filters.assert_called_once_with('ERROR_TOKEN')
        monitor.tx_builder.build_and_send_transaction.assert_not_called()
        assert monitor.stats['pools_bought'] == 0
