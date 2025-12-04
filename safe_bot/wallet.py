"""
Modul pengurusan dompet Solana
"""
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WalletManager:
    """Kelas untuk menguruskan dompet Solana"""
    
    def __init__(self, rpc_endpoint: str):
        """
        Inisialisasi wallet manager
        
        Args:
            rpc_endpoint: RPC endpoint untuk sambungan Solana
        """
        self.rpc_endpoint = rpc_endpoint
        self.client = AsyncClient(rpc_endpoint)
        self.keypair: Optional[Keypair] = None
        
    def load_from_private_key(self, private_key_bs58: str) -> bool:
        """
        Muat dompet dari private key Base58
        
        Args:
            private_key_bs58: Private key dalam format Base58
            
        Returns:
            True jika berjaya, False jika gagal
        """
        try:
            # Decode Base58 private key
            private_key_bytes = base58.b58decode(private_key_bs58)
            
            # Buat keypair dari private key
            self.keypair = Keypair.from_bytes(private_key_bytes)
            
            logger.info(f"✅ Dompet berjaya dimuat: {self.public_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Gagal memuat dompet: {e}")
            return False
    
    @property
    def public_key(self) -> Optional[Pubkey]:
        """Dapatkan public key dompet"""
        if self.keypair:
            return self.keypair.pubkey()
        return None
    
    @property
    def address(self) -> Optional[str]:
        """Dapatkan alamat dompet sebagai string"""
        if self.public_key:
            return str(self.public_key)
        return None
    
    async def get_balance(self) -> float:
        """
        Dapatkan baki SOL dompet
        
        Returns:
            Baki dalam SOL
        """
        if not self.public_key:
            return 0.0
        
        try:
            response = await self.client.get_balance(self.public_key)
            if response.value is not None:
                # Convert lamports to SOL (1 SOL = 1,000,000,000 lamports)
                return response.value / 1_000_000_000
            return 0.0
        except Exception as e:
            logger.error(f"❌ Gagal mendapatkan baki: {e}")
            return 0.0
    
    async def get_token_balance(self, token_mint: Pubkey) -> float:
        """
        Dapatkan baki token tertentu
        
        Args:
            token_mint: Alamat mint token
            
        Returns:
            Baki token
        """
        if not self.public_key:
            return 0.0
        
        try:
            # Dapatkan token accounts untuk dompet ini
            response = await self.client.get_token_accounts_by_owner(
                self.public_key,
                {"mint": token_mint}
            )
            
            if response.value:
                # Ambil baki dari account pertama
                account_data = response.value[0].account.data
                # Parse token amount (simplified)
                return 0.0  # TODO: Implement proper token balance parsing
            
            return 0.0
        except Exception as e:
            logger.error(f"❌ Gagal mendapatkan baki token: {e}")
            return 0.0
    
    async def close(self):
        """Tutup sambungan RPC"""
        await self.client.close()
    
    def __del__(self):
        """Destructor untuk pastikan sambungan ditutup"""
        try:
            import asyncio
            asyncio.create_task(self.close())
        except:
            pass
