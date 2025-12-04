"""
Modul untuk membina dan melaksanakan swap di Raydium
"""
import logging
from typing import Optional, Dict, Any, List
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.system_program import ID as SYSTEM_PROGRAM_ID
from solders.sysvar import RENT
from spl.token.constants import TOKEN_PROGRAM_ID

from .constants import (
    RAYDIUM_AMM_PROGRAM_ID,
    RAYDIUM_AUTHORITY_V4,
    SERUM_PROGRAM_ID,
    SWAP_INSTRUCTION_INDEX
)
from .layouts import SWAP_LAYOUT

logger = logging.getLogger(__name__)

class RaydiumSwap:
    """Kelas untuk menguruskan operasi swap Raydium"""
    
    def __init__(self, client, wallet):
        """
        Inisialisasi RaydiumSwap
        
        Args:
            client: AsyncClient Solana
            wallet: WalletManager instance
        """
        self.client = client
        self.wallet = wallet
        self.program_id = Pubkey.from_string(RAYDIUM_AMM_PROGRAM_ID)
    
    def calculate_min_amount_out(
        self,
        expected_amount: int,
        slippage_bps: int
    ) -> int:
        """
        Kira jumlah minimum keluar berdasarkan slippage
        
        Args:
            expected_amount: Jumlah jangkaan keluar
            slippage_bps: Slippage dalam basis points (cth: 500 = 5%)
            
        Returns:
            Jumlah minimum keluar (integer)
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
        
        Args:
            pool_keys: Dictionary mengandungi kunci pool (AMM ID, Authority, Vaults, dll)
            amount_in: Jumlah token masuk (dalam unit terkecil/lamports)
            min_amount_out: Jumlah minimum token keluar
            token_account_in: Akaun token sumber pengguna
            token_account_out: Akaun token destinasi pengguna
            owner: Public key pemilik (wallet address)
            
        Returns:
            Instruction Solana yang siap untuk transaksi
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
        # Urutan akaun SANGAT PENTING
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
        Dapatkan kunci pool dari blockchain
        
        Args:
            pool_address: Alamat pool Raydium
            
        Returns:
            Dictionary kunci pool atau None jika gagal
        """
        # TODO: Implementasi penuh untuk fetch dan parse akaun AMM
        # Ini memerlukan parsing data akaun menggunakan AMM_INFO_LAYOUT_V4
        # dan kemudian fetch akaun Serum Market untuk mendapatkan kunci tambahan
        pass
