"""
Multi-source volume validation system
Combines data from multiple DEX APIs for accurate volume validation
"""
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from statistics import mean, median, stdev
from dataclasses import dataclass

from .birdeye_client import BirdeyeClient
from .dex_screener_client import DexScreenerClient

logger = logging.getLogger(__name__)


@dataclass
class VolumeData:
    """Volume data from a single source"""
    source: str
    volume: Optional[float]
    confidence: float  # 0.0 to 1.0
    timestamp: float
    error: Optional[str] = None


@dataclass
class ValidatedVolume:
    """Validated volume result from multiple sources"""
    final_volume: float
    confidence_score: float  # 0.0 to 1.0
    sources_used: int
    sources: List[VolumeData]
    validation_method: str
    warnings: List[str]


class VolumeValidator:
    """
    Multi-source volume validator for enhanced trading accuracy

    Combines data from Birdeye, DexScreener, and potentially other sources
    to provide more reliable volume validation.
    """

    def __init__(self, birdeye_client: BirdeyeClient, dex_screener_client: Optional[DexScreenerClient] = None):
        """
        Initialize volume validator

        Args:
            birdeye_client: Initialized Birdeye client
            dex_screener_client: Optional DexScreener client
        """
        self.birdeye = birdeye_client
        self.dex_screener = dex_screener_client or DexScreenerClient()
        self._dex_screener_initialized = False

    async def initialize(self):
        """Initialize all clients"""
        if not self._dex_screener_initialized:
            await self.dex_screener.start()
            self._dex_screener_initialized = True

    async def close(self):
        """Close all clients"""
        if self._dex_screener_initialized:
            await self.dex_screener.close()

    async def get_validated_volume(self, token_address: str) -> ValidatedVolume:
        """
        Get validated volume from multiple sources

        Args:
            token_address: Solana token mint address

        Returns:
            ValidatedVolume with consensus volume and confidence score
        """
        try:
            await self.initialize()

            # Collect volume data from all sources
            volume_sources = await self._collect_volume_sources(token_address)

            if not volume_sources:
                # Fallback: return safe default
                return ValidatedVolume(
                    final_volume=10000.0,
                    confidence_score=0.1,
                    sources_used=0,
                    sources=[],
                    validation_method="fallback",
                    warnings=["No volume sources available"]
                )

            # Validate and combine results
            validated_result = self._validate_and_combine(volume_sources)

            logger.debug(
                f"📊 Validated volume for {token_address[:8]}...: "
                f"${validated_result.final_volume:,.0f} "
                f"(confidence: {validated_result.confidence_score:.2f}, "
                f"sources: {validated_result.sources_used})"
            )

            return validated_result

        except Exception as e:
            logger.error(f"❌ Volume validation failed for {token_address}: {e}")
            # Return safe fallback
            return ValidatedVolume(
                final_volume=100000.0,
                confidence_score=0.0,
                sources_used=0,
                sources=[],
                validation_method="error_fallback",
                warnings=[f"Validation error: {str(e)}"]
            )

    async def get_bulk_validated_volumes(self, token_addresses: List[str]) -> Dict[str, ValidatedVolume]:
        """
        Get validated volumes for multiple tokens efficiently using bulk operations.

        Args:
            token_addresses: List of token addresses to validate

        Returns:
            Dict mapping token addresses to ValidatedVolume objects
        """
        try:
            await self.initialize()
            results = {}

            # Collect volume data from all sources using bulk operations
            birdeye_volumes = {}
            dex_volumes = {}

            try:
                birdeye_volumes = await self.birdeye.get_bulk_volume_data(token_addresses)
            except Exception as e:
                logger.warning(f"Birdeye bulk volume fetch failed: {e}")

            try:
                dex_volumes = {}
                for address in token_addresses:
                    try:
                        volume = await self.dex_screener.get_token_volume_24h(address)
                        dex_volumes[address] = volume
                    except Exception as e:
                        logger.debug(f"DexScreener volume fetch failed for {address[:8]}: {e}")
                        dex_volumes[address] = None
            except Exception as e:
                logger.warning(f"DexScreener bulk volume fetch failed: {e}")

            # Process each token
            for token_address in token_addresses:
                volume_sources = []

                # Add Birdeye data
                birdeye_volume = birdeye_volumes.get(token_address)
                if birdeye_volume is not None:
                    volume_sources.append(VolumeData(
                        source="birdeye",
                        volume=birdeye_volume,
                        confidence=0.8,
                        timestamp=asyncio.get_event_loop().time()
                    ))

                # Add DexScreener data
                dex_volume = dex_volumes.get(token_address)
                if dex_volume is not None:
                    volume_sources.append(VolumeData(
                        source="dexscreener",
                        volume=dex_volume,
                        confidence=0.7,
                        timestamp=asyncio.get_event_loop().time()
                    ))

                if volume_sources:
                    validated_result = self._validate_and_combine(volume_sources)
                else:
                    # No data available
                    validated_result = ValidatedVolume(
                        final_volume=10000.0,
                        confidence_score=0.1,
                        sources_used=0,
                        sources=[],
                        validation_method="bulk_fallback",
                        warnings=["No volume data available in bulk fetch"]
                    )

                results[token_address] = validated_result

            logger.debug(f"✅ Bulk validated volumes for {len(results)} tokens")
            return results

        except Exception as e:
            logger.error(f"❌ Bulk volume validation failed: {e}")
            # Return fallback results for all tokens
            fallback = ValidatedVolume(
                final_volume=100000.0,
                confidence_score=0.0,
                sources_used=0,
                sources=[],
                validation_method="bulk_error_fallback",
                warnings=[f"Bulk validation error: {str(e)}"]
            )
            return {address: fallback for address in token_addresses}

    async def _collect_volume_sources(self, token_address: str) -> List[VolumeData]:
        """
        Collect volume data from all available sources

        Args:
            token_address: Token address to check

        Returns:
            List of VolumeData from different sources
        """
        sources = []
        timestamp = asyncio.get_event_loop().time()

        # Source 1: Birdeye API
        try:
            birdeye_volume = await self.birdeye.get_token_volume_24h(token_address)
            sources.append(VolumeData(
                source="birdeye",
                volume=birdeye_volume,
                confidence=0.8 if birdeye_volume else 0.0,
                timestamp=timestamp,
                error=None if birdeye_volume else "No data"
            ))
        except Exception as e:
            sources.append(VolumeData(
                source="birdeye",
                volume=None,
                confidence=0.0,
                timestamp=timestamp,
                error=str(e)
            ))

        # Source 2: DexScreener API
        try:
            dex_volume = await self.dex_screener.get_token_volume_24h(token_address)
            sources.append(VolumeData(
                source="dexscreener",
                volume=dex_volume,
                confidence=0.7 if dex_volume else 0.0,
                timestamp=timestamp,
                error=None if dex_volume else "No data"
            ))
        except Exception as e:
            sources.append(VolumeData(
                source="dexscreener",
                volume=None,
                confidence=0.0,
                timestamp=timestamp,
                error=str(e)
            ))

        # Filter out failed sources
        valid_sources = [s for s in sources if s.volume is not None and s.volume > 0]

        logger.debug(f"📊 Collected {len(valid_sources)}/{len(sources)} volume sources for {token_address[:8]}...")

        return valid_sources

    def _validate_and_combine(self, volume_sources: List[VolumeData]) -> ValidatedVolume:
        """
        Validate consistency and combine volume data

        Args:
            volume_sources: List of volume data from different sources

        Returns:
            Validated volume result
        """
        if not volume_sources:
            return ValidatedVolume(
                final_volume=10000.0,
                confidence_score=0.0,
                sources_used=0,
                sources=volume_sources,
                validation_method="no_data",
                warnings=["No valid volume data available"]
            )

        if len(volume_sources) == 1:
            # Single source - use it with moderate confidence
            source = volume_sources[0]
            return ValidatedVolume(
                final_volume=source.volume,
                confidence_score=source.confidence * 0.7,  # Reduce confidence for single source
                sources_used=1,
                sources=volume_sources,
                validation_method="single_source",
                warnings=["Only one volume source available"]
            )

        # Multiple sources - validate consistency
        volumes = [s.volume for s in volume_sources]
        confidences = [s.confidence for s in volume_sources]

        # Calculate statistical measures
        avg_volume = mean(volumes)
        median_volume = median(volumes)

        # Check consistency (coefficient of variation)
        if len(volumes) > 1:
            try:
                std_dev = stdev(volumes)
                cv = std_dev / avg_volume if avg_volume > 0 else float('inf')

                # Consistency thresholds
                if cv < 0.1:  # Very consistent (< 10% variation)
                    consistency_score = 1.0
                    method = "high_consistency"
                    warnings = []
                elif cv < 0.3:  # Moderately consistent (< 30% variation)
                    consistency_score = 0.8
                    method = "moderate_consistency"
                    warnings = []
                elif cv < 0.5:  # Somewhat consistent (< 50% variation)
                    consistency_score = 0.6
                    method = "low_consistency"
                    warnings = [f"Volume variation: {cv:.1%}"]
                else:  # Inconsistent (> 50% variation)
                    consistency_score = 0.3
                    method = "inconsistent"
                    warnings = [f"High volume variation: {cv:.1%}", "Using median value"]

                # Choose final volume based on consistency
                if consistency_score >= 0.8:
                    final_volume = avg_volume  # Use average for consistent data
                else:
                    final_volume = median_volume  # Use median for inconsistent data

                # Calculate overall confidence
                avg_confidence = mean(confidences)
                final_confidence = min(consistency_score * avg_confidence * len(volume_sources) / 2, 1.0)

                return ValidatedVolume(
                    final_volume=final_volume,
                    confidence_score=final_confidence,
                    sources_used=len(volume_sources),
                    sources=volume_sources,
                    validation_method=method,
                    warnings=warnings
                )

            except Exception as e:
                logger.warning(f"Statistical analysis failed: {e}")
                # Fallback to median
                return ValidatedVolume(
                    final_volume=median_volume,
                    confidence_score=0.4,
                    sources_used=len(volume_sources),
                    sources=volume_sources,
                    validation_method="median_fallback",
                    warnings=["Statistical analysis failed", str(e)]
                )

        # Fallback for edge cases
        return ValidatedVolume(
            final_volume=median_volume,
            confidence_score=0.5,
            sources_used=len(volume_sources),
            sources=volume_sources,
            validation_method="median_default",
            warnings=[]
        )

    async def get_volume_confidence_report(self, token_address: str) -> Dict[str, Any]:
        """
        Get detailed volume confidence report for analysis

        Args:
            token_address: Token address to analyze

        Returns:
            Detailed report with all source data and validation metrics
        """
        validated = await self.get_validated_volume(token_address)

        report = {
            "token_address": token_address,
            "final_volume": validated.final_volume,
            "confidence_score": validated.confidence_score,
            "sources_used": validated.sources_used,
            "validation_method": validated.validation_method,
            "warnings": validated.warnings,
            "source_details": []
        }

        for source in validated.sources:
            report["source_details"].append({
                "source": source.source,
                "volume": source.volume,
                "confidence": source.confidence,
                "error": source.error
            })

        return report
