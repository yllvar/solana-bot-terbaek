#!/usr/bin/env python3
"""
Test script for multi-source volume validation
"""
import asyncio
import sys
sys.path.insert(0, 'src')

async def test_multi_source_volume():
    print('🧪 TESTING MULTI-SOURCE VOLUME VALIDATION...')

    try:
        from solana_bot.config import BotConfig
        from solana_bot.dex_screener_client import DexScreenerClient
        from solana_bot.birdeye_client import BirdeyeClient
        from solana_bot.volume_validator import VolumeValidator

        # Load config
        config = BotConfig('config/bot_config.json')
        print('✅ Config loaded successfully')
        print(f'   Multi-source volume: {config.multi_source_volume}')
        print(f'   Min volume confidence: {config.min_volume_confidence}')

        # Initialize clients
        birdeye = BirdeyeClient(config.birdeye_api_key)
        dex_screener = DexScreenerClient()
        validator = VolumeValidator(birdeye, dex_screener)

        print('✅ Clients initialized successfully')

        # Test with SOL token (should have good data)
        sol_address = 'So11111111111111111111111111111111111111112'
        print(f'\n🔍 Testing volume validation for SOL: {sol_address}')

        # Get validated volume
        result = await validator.get_validated_volume(sol_address)

        print('✅ Validation successful!')
        print(f'   Final volume: ${result.final_volume:,.0f}')
        print(f'   Confidence: {result.confidence_score:.2f}')
        print(f'   Sources used: {result.sources_used}')
        print(f'   Validation method: {result.validation_method}')

        if result.warnings:
            print(f'   Warnings: {len(result.warnings)}')
            for warning in result.warnings:
                print(f'     - {warning}')

        # Show source details
        print(f'\n📊 Source breakdown:')
        for source in result.sources:
            status = '✅' if source.volume else '❌'
            print(f'   {source.source}: {status} ${source.volume or 0:,.0f} (conf: {source.confidence:.1f})')

        # Test confidence threshold
        min_conf = config.min_volume_confidence
        if result.confidence_score >= min_conf:
            print(f'\n🎯 RESULT: Volume PASSES confidence threshold ({result.confidence_score:.2f} >= {min_conf})')
        else:
            print(f'\n⚠️ RESULT: Volume FAILS confidence threshold ({result.confidence_score:.2f} < {min_conf})')

        # Cleanup
        await validator.close()

        print('\n🎉 Multi-source volume validation test completed successfully!')

    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_multi_source_volume())
