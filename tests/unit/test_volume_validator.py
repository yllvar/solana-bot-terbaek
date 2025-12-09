"""
Unit tests for VolumeValidator multi-source validation
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from src.solana_bot.volume_validator import VolumeValidator, VolumeData, ValidatedVolume


class TestVolumeValidator:
    """Test VolumeValidator functionality"""

    @pytest.fixture
    def mock_birdeye(self):
        """Mock Birdeye client"""
        client = AsyncMock()
        client.get_token_volume_24h = AsyncMock()
        return client

    @pytest.fixture
    def mock_dex_screener(self):
        """Mock DexScreener client"""
        client = AsyncMock()
        client.get_token_volume_24h = AsyncMock()
        return client

    @pytest.fixture
    def validator(self, mock_birdeye, mock_dex_screener):
        """Create test validator instance"""
        return VolumeValidator(mock_birdeye, mock_dex_screener)

    @pytest.mark.asyncio
    async def test_initialization(self, validator):
        """Test validator initialization"""
        assert validator.birdeye is not None
        assert validator.dex_screener is not None
        assert not validator._dex_screener_initialized

    @pytest.mark.asyncio
    async def test_initialization_with_auto_start(self, validator):
        """Test automatic client initialization"""
        await validator.initialize()
        assert validator._dex_screener_initialized

        # Test double initialization doesn't fail
        await validator.initialize()
        assert validator._dex_screener_initialized

    @pytest.mark.asyncio
    async def test_collect_volume_sources_both_success(self, validator, mock_birdeye, mock_dex_screener):
        """Test collecting volume from both sources successfully"""
        mock_birdeye.get_token_volume_24h.return_value = 100000
        mock_dex_screener.get_token_volume_24h.return_value = 95000

        await validator.initialize()
        sources = await validator._collect_volume_sources("TEST_TOKEN")

        assert len(sources) == 2
        assert all(isinstance(s, VolumeData) for s in sources)
        assert sources[0].source == "birdeye"
        assert sources[0].volume == 100000
        assert sources[1].source == "dexscreener"
        assert sources[1].volume == 95000

    @pytest.mark.asyncio
    async def test_collect_volume_sources_partial_failure(self, validator, mock_birdeye, mock_dex_screener):
        """Test collecting volume when one source fails"""
        mock_birdeye.get_token_volume_24h.return_value = 100000
        mock_dex_screener.get_token_volume_24h.side_effect = Exception("API Error")

        await validator.initialize()
        sources = await validator._collect_volume_sources("TEST_TOKEN")

        assert len(sources) == 2
        assert sources[0].volume == 100000  # Success
        assert sources[1].volume is None   # Failed
        assert sources[1].error == "API Error"

    @pytest.mark.asyncio
    async def test_collect_volume_sources_all_failure(self, validator, mock_birdeye, mock_dex_screener):
        """Test collecting volume when all sources fail"""
        mock_birdeye.get_token_volume_24h.side_effect = Exception("API Error 1")
        mock_dex_screener.get_token_volume_24h.side_effect = Exception("API Error 2")

        await validator.initialize()
        sources = await validator._collect_volume_sources("TEST_TOKEN")

        assert len(sources) == 2
        assert all(s.volume is None for s in sources)
        assert all(s.error is not None for s in sources)

    @pytest.mark.asyncio
    async def test_validate_and_combine_single_source(self, validator):
        """Test validation with single volume source"""
        sources = [
            VolumeData(source="birdeye", volume=100000, confidence=0.8, timestamp=0)
        ]

        result = validator._validate_and_combine(sources)

        assert isinstance(result, ValidatedVolume)
        assert result.final_volume == 100000
        assert result.confidence_score == 0.64  # 0.8 * 0.8 (single source reduction)
        assert result.sources_used == 1
        assert "single_source" in result.validation_method

    @pytest.mark.asyncio
    async def test_validate_and_combine_consistent_sources(self, validator):
        """Test validation with consistent multiple sources"""
        sources = [
            VolumeData(source="birdeye", volume=100000, confidence=0.8, timestamp=0),
            VolumeData(source="dexscreener", volume=95000, confidence=0.7, timestamp=0)
        ]

        result = validator._validate_and_combine(sources)

        assert result.final_volume == 97500  # Average of 100000 and 95000
        assert result.confidence_score > 0.8  # High confidence for consistent data
        assert "high_consistency" in result.validation_method
        assert len(result.warnings) == 0

    @pytest.mark.asyncio
    async def test_validate_and_combine_inconsistent_sources(self, validator):
        """Test validation with inconsistent sources"""
        sources = [
            VolumeData(source="birdeye", volume=100000, confidence=0.8, timestamp=0),
            VolumeData(source="dexscreener", volume=50000, confidence=0.7, timestamp=0)  # 50% difference
        ]

        result = validator._validate_and_combine(sources)

        assert result.final_volume == 75000  # Median of inconsistent data
        assert result.confidence_score < 0.7  # Lower confidence
        assert "inconsistent" in result.validation_method
        assert len(result.warnings) > 0
        assert "variation" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_validate_and_combine_no_sources(self, validator):
        """Test validation with no valid sources"""
        sources = []

        result = validator._validate_and_combine(sources)

        assert result.final_volume == 10000  # Fallback value
        assert result.confidence_score == 0.0
        assert result.sources_used == 0
        assert "no_data" in result.validation_method

    @pytest.mark.asyncio
    async def test_get_validated_volume_success(self, validator, mock_birdeye, mock_dex_screener):
        """Test full volume validation success"""
        mock_birdeye.get_token_volume_24h.return_value = 100000
        mock_dex_screener.get_token_volume_24h.return_value = 95000

        await validator.initialize()
        result = await validator.get_validated_volume("TEST_TOKEN")

        assert isinstance(result, ValidatedVolume)
        assert result.sources_used == 2
        assert result.final_volume > 0
        assert result.confidence_score > 0

    @pytest.mark.asyncio
    async def test_get_validated_volume_all_failures(self, validator, mock_birdeye, mock_dex_screener):
        """Test volume validation when all sources fail"""
        mock_birdeye.get_token_volume_24h.side_effect = Exception("API Error")
        mock_dex_screener.get_token_volume_24h.side_effect = Exception("API Error")

        await validator.initialize()
        result = await validator.get_validated_volume("TEST_TOKEN")

        assert result.final_volume == 100000  # Error fallback
        assert result.confidence_score == 0.0
        assert "error_fallback" in result.validation_method

    @pytest.mark.asyncio
    async def test_get_volume_confidence_report(self, validator, mock_birdeye, mock_dex_screener):
        """Test detailed confidence report generation"""
        mock_birdeye.get_token_volume_24h.return_value = 100000
        mock_dex_screener.get_token_volume_24h.return_value = 95000

        await validator.initialize()
        report = await validator.get_volume_confidence_report("TEST_TOKEN")

        assert report["token_address"] == "TEST_TOKEN"
        assert "final_volume" in report
        assert "confidence_score" in report
        assert "sources_used" in report
        assert "source_details" in report
        assert len(report["source_details"]) == 2

    @pytest.mark.asyncio
    async def test_close_functionality(self, validator, mock_dex_screener):
        """Test proper client cleanup"""
        await validator.initialize()
        assert validator._dex_screener_initialized

        await validator.close()
        mock_dex_screener.close.assert_called_once()
        assert not validator._dex_screener_initialized

    @pytest.mark.asyncio
    async def test_error_resilience(self, validator, mock_birdeye, mock_dex_screener):
        """Test error resilience and fallback behavior"""
        # Make all API calls fail
        mock_birdeye.get_token_volume_24h.side_effect = Exception("Network error")
        mock_dex_screener.get_token_volume_24h.side_effect = Exception("API timeout")

        await validator.initialize()

        # Should not raise exception, should return fallback
        result = await validator.get_validated_volume("TEST_TOKEN")

        assert result.final_volume > 0  # Fallback value
        assert result.confidence_score == 0.0
        assert result.sources_used == 0

    def test_volume_data_structure(self):
        """Test VolumeData dataclass structure"""
        data = VolumeData(
            source="test",
            volume=100000,
            confidence=0.8,
            timestamp=1234567890,
            error="test error"
        )

        assert data.source == "test"
        assert data.volume == 100000
        assert data.confidence == 0.8
        assert data.timestamp == 1234567890
        assert data.error == "test error"

    def test_validated_volume_structure(self):
        """Test ValidatedVolume dataclass structure"""
        volume = ValidatedVolume(
            final_volume=100000,
            confidence_score=0.85,
            sources_used=2,
            sources=[],
            validation_method="high_consistency",
            warnings=["Minor variation detected"]
        )

        assert volume.final_volume == 100000
        assert volume.confidence_score == 0.85
        assert volume.sources_used == 2
        assert volume.validation_method == "high_consistency"
        assert len(volume.warnings) == 1
