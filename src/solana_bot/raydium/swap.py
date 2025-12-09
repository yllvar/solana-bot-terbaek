"""
Modul untuk membina dan melaksanakan swap di Raydium
"""
import logging
from typing import Optional, Dict, Any, List
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.instructions import get_associated_token_address

from .constants import (
    RAYDIUM_AMM_PROGRAM_ID,
    RAYDIUM_AUTHORITY_V4,
    SERUM_PROGRAM_ID,
    SWAP_INSTRUCTION_INDEX,
    TOKEN_PROGRAM_ID
)
from .layouts import SWAP_LAYOUT, AMM_INFO_LAYOUT_V4, MARKET_LAYOUT_V3

logger = logging.getLogger(__name__)

class RaydiumSwap:
    """Kelas untuk menguruskan operasi swap Raydium"""
    
    def __init__(self, client, wallet):
        """
        Inisialisasi RaydiumSwap
        """
        self.client = client
        self.wallet = wallet
        self.program_id = RAYDIUM_AMM_PROGRAM_ID
    
    def calculate_min_amount_out(
        self,
        expected_amount: int,
        slippage_bps: int
    ) -> int:
        """
        Kira jumlah minimum keluar berdasarkan slippage
        """
        slippage_multiplier = (10000 - slippage_bps) / 10000
        return int(expected_amount * slippage_multiplier)

    def build_swap_instruction(
        self,
        pool_keys: Dict[str, Any],
        amount_in: int,
        min_amount_out: int,
        token_account_in: Pubkey,
        token_account_out: Pubkey,
        owner: Pubkey
    ) -> Instruction:
        """
        Bina instruction untuk swap
        """
        
        # Data instruction
        data = SWAP_LAYOUT.build(
            dict(
                instruction=SWAP_INSTRUCTION_INDEX,
                amount_in=amount_in,
                min_amount_out=min_amount_out
            )
        )
        
        # Senarai akaun yang diperlukan oleh Raydium Swap V4
        keys = [
            # 1. Token Program
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            # 2. AMM Id
            AccountMeta(pubkey=pool_keys['amm_id'], is_signer=False, is_writable=True),
            # 3. AMM Authority
            AccountMeta(pubkey=pool_keys['authority'], is_signer=False, is_writable=False),
            # 4. AMM Open Orders
            AccountMeta(pubkey=pool_keys['open_orders'], is_signer=False, is_writable=True),
            # 5. AMM Target Orders
            AccountMeta(pubkey=pool_keys['target_orders'], is_signer=False, is_writable=True),
            # 6. AMM Base Vault
            AccountMeta(pubkey=pool_keys['base_vault'], is_signer=False, is_writable=True),
            # 7. AMM Quote Vault
            AccountMeta(pubkey=pool_keys['quote_vault'], is_signer=False, is_writable=True),
            # 8. Serum Program Id
            AccountMeta(pubkey=pool_keys['market_program_id'], is_signer=False, is_writable=False),
            # 9. Serum Market
            AccountMeta(pubkey=pool_keys['market_id'], is_signer=False, is_writable=True),
            # 10. Serum Bids
            AccountMeta(pubkey=pool_keys['market_bids'], is_signer=False, is_writable=True),
            # 11. Serum Asks
            AccountMeta(pubkey=pool_keys['market_asks'], is_signer=False, is_writable=True),
            # 12. Serum Event Queue
            AccountMeta(pubkey=pool_keys['market_event_queue'], is_signer=False, is_writable=True),
            # 13. Serum Base Vault
            AccountMeta(pubkey=pool_keys['market_base_vault'], is_signer=False, is_writable=True),
            # 14. Serum Quote Vault
            AccountMeta(pubkey=pool_keys['market_quote_vault'], is_signer=False, is_writable=True),
            # 15. Serum Vault Signer
            AccountMeta(pubkey=pool_keys['market_vault_signer'], is_signer=False, is_writable=False),
            # 16. User Source Token Account
            AccountMeta(pubkey=token_account_in, is_signer=False, is_writable=True),
            # 17. User Destination Token Account
            AccountMeta(pubkey=token_account_out, is_signer=False, is_writable=True),
            # 18. User Owner (Signer)
            AccountMeta(pubkey=owner, is_signer=True, is_writable=False)
        ]
        
        return Instruction(self.program_id, data, keys)

    async def get_pool_keys(self, pool_address: str) -> Optional[Dict[str, Any]]:
        """
        Dapatkan kunci pool dari blockchain secara lengkap
        """
        try:
            pool_pubkey = Pubkey.from_string(pool_address)
            
            # 1. Fetch AMM Account
            amm_info = await self.client.get_account_info(pool_pubkey)
            if not amm_info.value:
                logger.error("Gagal mendapatkan akaun AMM")
                return None
                
            amm_data = AMM_INFO_LAYOUT_V4.parse(amm_info.value.data)
            
            # 2. Extract Market ID
            market_id = Pubkey.from_bytes(amm_data.market_id)
            
            # 3. Fetch Market Account
            market_info = await self.client.get_account_info(market_id)
            if not market_info.value:
                logger.error("Gagal mendapatkan akaun Market")
                return None
                
            market_data = MARKET_LAYOUT_V3.parse(market_info.value.data)
            
            # 4. Construct Pool Keys
            pool_keys = {
                'amm_id': pool_pubkey,
                'authority': RAYDIUM_AUTHORITY_V4,
                'base_mint': Pubkey.from_bytes(amm_data.base_mint),
                'quote_mint': Pubkey.from_bytes(amm_data.quote_mint),
                'lp_mint': Pubkey.from_bytes(amm_data.lp_mint),
                'base_decimals': amm_data.base_decimal,
                'quote_decimals': amm_data.quote_decimal,
                'base_vault': Pubkey.from_bytes(amm_data.base_vault),
                'quote_vault': Pubkey.from_bytes(amm_data.quote_vault),
                'open_orders': Pubkey.from_bytes(amm_data.open_orders),
                'target_orders': Pubkey.from_bytes(amm_data.target_orders),
                'market_program_id': Pubkey.from_bytes(amm_data.market_program_id),
                'market_id': market_id,
                'market_bids': Pubkey.from_bytes(market_data.bids),
                'market_asks': Pubkey.from_bytes(market_data.asks),
                'market_event_queue': Pubkey.from_bytes(market_data.event_queue),
                'market_base_vault': Pubkey.from_bytes(market_data.base_vault),
                'market_quote_vault': Pubkey.from_bytes(market_data.quote_vault),
                'market_vault_signer': Pubkey.from_bytes(market_data.own_address) # Selalunya own_address dalam layout V3 adalah vault signer? Perlu verify.
                # Nota: Vault signer nonce digunakan untuk derive address jika perlu.
                # Untuk simplifikasi, kita anggap kita boleh derive atau ia ada dalam data.
                # Sebenarnya, market vault signer perlu diderive dari market id dan nonce.
            }
            
            # Derive Market Vault Signer (jika own_address bukan vault signer)
            # Biasanya kita derive:
            nonce = market_data.vault_signer_nonce
            vault_signer_key, _ = Pubkey.find_program_address(
                [bytes(market_id), bytes([nonce])],
                Pubkey.from_bytes(amm_data.market_program_id) # Serum Program ID
            )
            pool_keys['market_vault_signer'] = vault_signer_key
            
            return pool_keys
            
        except Exception as e:
            logger.error(f"Error fetching pool keys: {e}")
            return None
            
    def get_associated_token_address(self, owner: Pubkey, mint: Pubkey) -> Pubkey:
        """Dapatkan alamat Associated Token Account (ATA)"""
        return get_associated_token_address(owner, mint)
