"""
E2E tests for Phase 1 enhancements: Multi-source volume, liquidity analysis, and volatility monitoring
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.solana_bot.monitor import PoolMonitor
from src.solana_bot.config import BotConfig
from src.solana_bot.security import SecurityAnalyzer


class TestPhase1E2E:
    """End-to-end tests for Phase 1 enhancements"""

    @pytest.fixture
    def mock_config(self):
        """Create test configuration with Phase 1 features enabled"""
        config = MagicMock(spec=BotConfig)
        # Basic config
        config.buy_amount = 0.1
        config.min_volume_24h = 5000
        config.max_trades_per_hour = 5
        config.cooldown_after_sell = 60

        # Phase 1 features enabled
        config.multi_source_volume = True
        config.pool_liquidity_analysis = True
        config.price_volatility_filter = True
        config.min_volume_confidence = 0.3
        config.max_price_impact = 0.05  # 5%
        config.max_volatility_threshold = 0.3
        config.max_price_change_24h = 50

        return config

    @pytest.fixture
    def mock_wallet(self):
        """Create mock wallet manager"""
        wallet = MagicMock()
        wallet.keypair = MagicMock()
        wallet.keypair.pubkey.return_value = MagicMock()
        return wallet

    @pytest.fixture
    def mock_security(self):
        """Create mock security analyzer"""
        security = MagicMock(spec=SecurityAnalyzer)
        security.quick_check = AsyncMock(return_value=(True, []))
        return security

    @pytest.fixture
    def monitor(self, mock_config, mock_wallet, mock_security):
        """Create test monitor instance"""
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

            # Mock the additional clients
            monitor.dex_screener = AsyncMock()
            monitor.volume_validator = AsyncMock()

            return monitor

    @pytest.mark.asyncio
    async def test_full_trading_pipeline_success(self, monitor, mock_config):
        """Test complete trading pipeline with all Phase 1 features passing"""
        # Mock successful volume validation
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8
        validated_volume.sources_used = 2
        validated_volume.validation_method = "high_consistency"
        validated_volume.warnings = []

        monitor.volume_validator.get_validated_volume = AsyncMock(return_value=validated_volume)

        # Mock successful liquidity analysis
        async def mock_liquidity_analysis(*args, **kwargs):
            return {
                'can_trade': True,
                'liquidity_usd': 2000000,  # $2M liquidity
                'price_impact': 0.02,      # 2% impact
                'max_allowed_impact': 0.05,
                'sources_used': 2,
                'reason': None
            }

        monitor._analyze_pool_liquidity = AsyncMock(side_effect=mock_liquidity_analysis)

        # Mock successful volatility check (stable token)
        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.1)  # Low volatility

        # Mock pool and transaction setup
        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify all checks passed
        monitor.volume_validator.get_validated_volume.assert_called_once_with('TEST_TOKEN_ADDRESS')
        monitor._analyze_pool_liquidity.assert_called_once()
        monitor.birdeye.calculate_volatility.assert_called_once()
        monitor.tx_builder.build_and_send_transaction.assert_called_once()

        # Verify trade was executed
        assert monitor.stats['pools_bought'] == 1

    @pytest.mark.asyncio
    async def test_volume_validation_failure_blocks_trade(self, monitor):
        """Test that low confidence volume validation blocks trading"""
        # Mock failed volume validation (low confidence)
        validated_volume = MagicMock()
        validated_volume.final_volume = 10000
        validated_volume.confidence_score = 0.1  # Below threshold
        validated_volume.sources_used = 1
        validated_volume.validation_method = "low_confidence"

        monitor.volume_validator.get_validated_volume.return_value = validated_volume

        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify trade was blocked
        monitor.tx_builder.build_and_send_transaction.assert_not_called()
        assert monitor.stats['pools_bought'] == 0

    @pytest.mark.asyncio
    async def test_liquidity_analysis_blocks_high_impact_trade(self, monitor):
        """Test that high price impact blocks trading"""
        # Mock successful volume validation
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8

        monitor.volume_validator.get_validated_volume.return_value = validated_volume

        # Mock failed liquidity analysis (high impact)
        liquidity_result = {
            'can_trade': False,
            'liquidity_usd': 50000,   # Low liquidity
            'price_impact': 0.08,     # 8% impact (above 5% limit)
            'max_allowed_impact': 0.05,
            'reason': 'Price impact too high: 8.00% > 5.00%'
        }
        monitor._analyze_pool_liquidity = AsyncMock(return_value=liquidity_result)

        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify trade was blocked
        monitor.tx_builder.build_and_send_transaction.assert_not_called()
        assert monitor.stats['pools_bought'] == 0

    @pytest.mark.asyncio
    async def test_volatility_filter_blocks_volatile_token(self, monitor):
        """Test that high volatility blocks trading"""
        # Mock successful volume validation
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8

        monitor.volume_validator.get_validated_volume.return_value = validated_volume

        # Mock successful liquidity analysis
        liquidity_result = {
            'can_trade': True,
            'liquidity_usd': 2000000,
            'price_impact': 0.02,
            'max_allowed_impact': 0.05
        }
        monitor._analyze_pool_liquidity = AsyncMock(return_value=liquidity_result)

        # Mock high volatility (should block trade)
        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.5)  # Above 0.3 threshold

        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify trade was blocked
        monitor.tx_builder.build_and_send_transaction.assert_not_called()
        assert monitor.stats['pools_bought'] == 0

    @pytest.mark.asyncio
    async def test_phase1_features_can_be_disabled(self, monitor):
        """Test that Phase 1 features can be individually disabled"""
        # Disable all Phase 1 features
        monitor.config.pool_liquidity_analysis = False
        monitor.config.price_volatility_filter = False

        # Mock successful volume validation
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8

        monitor.volume_validator.get_validated_volume.return_value = validated_volume

        # Mock pool and transaction setup
        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify disabled features were not called
        monitor._analyze_pool_liquidity.assert_not_called()
        monitor.birdeye.calculate_volatility.assert_not_called()

        # But volume validation still ran (core feature)
        monitor.volume_validator.get_validated_volume.assert_called_once()

        # And trade was executed
        monitor.tx_builder.build_and_send_transaction.assert_called_once()
        assert monitor.stats['pools_bought'] == 1

    @pytest.mark.asyncio
    async def test_error_handling_in_phase1_features(self, monitor):
        """Test error handling when Phase 1 features fail"""
        # Mock volume validation failure
        monitor.volume_validator.get_validated_volume.side_effect = Exception("API Error")

        # Mock liquidity analysis failure
        monitor._analyze_pool_liquidity = AsyncMock(side_effect=Exception("Liquidity Error"))

        # Mock volatility check failure
        monitor.birdeye.calculate_volatility = AsyncMock(side_effect=Exception("Volatility Error"))

        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        # Execute auto buy - should handle errors gracefully
        await monitor.execute_auto_buy(pool_info)

        # Verify trade was not executed (due to volume validation failure)
        monitor.tx_builder.build_and_send_transaction.assert_not_called()
        assert monitor.stats['pools_bought'] == 0

    @pytest.mark.asyncio
    async def test_multi_source_volume_integration(self, monitor):
        """Test multi-source volume validation integration"""
        # Mock detailed volume validation result
        validated_volume = MagicMock()
        validated_volume.final_volume = 125000
        validated_volume.confidence_score = 0.85
        validated_volume.sources_used = 2
        validated_volume.validation_method = "high_consistency"
        validated_volume.warnings = []

        monitor.volume_validator.get_validated_volume.return_value = validated_volume

        # Disable other Phase 1 features for focused testing
        monitor.config.pool_liquidity_analysis = False
        monitor.config.price_volatility_filter = False

        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify multi-source validation was used
        monitor.volume_validator.get_validated_volume.assert_called_once_with('TEST_TOKEN_ADDRESS')

        # Verify trade executed with validated volume
        monitor.tx_builder.build_and_send_transaction.assert_called_once()
        assert monitor.stats['pools_bought'] == 1

    @pytest.mark.asyncio
    async def test_liquidity_analysis_integration(self, monitor):
        """Test liquidity analysis integration with realistic data"""
        # Mock successful volume validation
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8

        monitor.volume_validator.get_validated_volume.return_value = validated_volume

        # Mock realistic liquidity analysis (large pool)
        liquidity_result = {
            'can_trade': True,
            'liquidity_usd': 5000000,  # $5M pool
            'price_impact': 0.004,     # 0.4% impact (very low)
            'max_allowed_impact': 0.05,
            'sources_used': 2,
            'reason': None
        }
        monitor._analyze_pool_liquidity = AsyncMock(return_value=liquidity_result)

        # Disable volatility check for focused testing
        monitor.config.price_volatility_filter = False

        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify liquidity analysis was called correctly
        monitor._analyze_pool_liquidity.assert_called_once_with(
            'TEST_POOL_ADDRESS', 'TEST_TOKEN_ADDRESS', monitor.config.buy_amount
        )

        # Verify trade executed
        monitor.tx_builder.build_and_send_transaction.assert_called_once()
        assert monitor.stats['pools_bought'] == 1

    @pytest.mark.asyncio
    async def test_volatility_filter_integration(self, monitor):
        """Test volatility filter integration"""
        # Mock successful volume validation
        validated_volume = MagicMock()
        validated_volume.final_volume = 100000
        validated_volume.confidence_score = 0.8

        monitor.volume_validator.get_validated_volume.return_value = validated_volume

        # Mock successful liquidity analysis
        liquidity_result = {
            'can_trade': True,
            'liquidity_usd': 2000000,
            'price_impact': 0.02,
            'max_allowed_impact': 0.05
        }
        monitor._analyze_pool_liquidity = AsyncMock(return_value=liquidity_result)

        # Mock low volatility (should allow trade)
        monitor.birdeye.calculate_volatility = AsyncMock(return_value=0.2)  # Below 0.3 threshold

        pool_info = {
            'token_address': 'TEST_TOKEN_ADDRESS',
            'pool_address': 'TEST_POOL_ADDRESS'
        }

        monitor._extract_pool_info = AsyncMock(return_value=pool_info)
        monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
        monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

        # Execute auto buy
        await monitor.execute_auto_buy(pool_info)

        # Verify volatility check was called
        monitor.birdeye.calculate_volatility.assert_called_once_with('TEST_TOKEN_ADDRESS', '1H', 24)

        # Verify trade executed
        monitor.tx_builder.build_and_send_transaction.assert_called_once()
        assert monitor.stats['pools_bought'] == 1

    @pytest.mark.asyncio
    async def test_comprehensive_trading_rejection_scenarios(self, monitor):
        """Test various scenarios where trades should be rejected"""
        test_cases = [
            {
                'name': 'Low volume confidence',
                'volume_confidence': 0.1,
                'liquidity_can_trade': True,
                'volatility': 0.1,
                'should_reject': True
            },
            {
                'name': 'High price impact',
                'volume_confidence': 0.8,
                'liquidity_can_trade': False,
                'volatility': 0.1,
                'should_reject': True
            },
            {
                'name': 'High volatility',
                'volume_confidence': 0.8,
                'liquidity_can_trade': True,
                'volatility': 0.5,
                'should_reject': True
            },
            {
                'name': 'All checks pass',
                'volume_confidence': 0.8,
                'liquidity_can_trade': True,
                'volatility': 0.2,
                'should_reject': False
            }
        ]

        for test_case in test_cases:
            # Reset stats
            monitor.stats['pools_bought'] = 0

            # Setup mocks
            validated_volume = MagicMock()
            validated_volume.final_volume = 100000
            validated_volume.confidence_score = test_case['volume_confidence']

            monitor.volume_validator.get_validated_volume.return_value = validated_volume

            liquidity_result = {
                'can_trade': test_case['liquidity_can_trade'],
                'liquidity_usd': 2000000,
                'price_impact': 0.02,
                'max_allowed_impact': 0.05
            }
            monitor._analyze_pool_liquidity = AsyncMock(return_value=liquidity_result)

            monitor.birdeye.calculate_volatility = AsyncMock(return_value=test_case['volatility'])

            pool_info = {
                'token_address': 'TEST_TOKEN_ADDRESS',
                'pool_address': 'TEST_POOL_ADDRESS'
            }

            # Only setup transaction mocks if trade should succeed
            if not test_case['should_reject']:
                monitor._extract_pool_info = AsyncMock(return_value=pool_info)
                monitor.raydium_swap.get_pool_keys = AsyncMock(return_value={'base_mint': 'BASE', 'quote_mint': 'QUOTE'})
                monitor.tx_builder.build_and_send_transaction = AsyncMock(return_value="TX_SIGNATURE")

            # Execute auto buy
            await monitor.execute_auto_buy(pool_info)

            # Verify result
            if test_case['should_reject']:
                assert monitor.stats['pools_bought'] == 0, f"Trade should be rejected: {test_case['name']}"
                monitor.tx_builder.build_and_send_transaction.assert_not_called()
            else:
                assert monitor.stats['pools_bought'] == 1, f"Trade should succeed: {test_case['name']}"
                monitor.tx_builder.build_and_send_transaction.assert_called_once()
