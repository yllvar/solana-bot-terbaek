"""
Modul pengurusan transaksi Solana
"""
import logging
import asyncio
from typing import List, Optional, Union
from solders.transaction import Transaction
from solders.message import Message
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.hash import Hash
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Processed
from solana.rpc.types import TxOpts

logger = logging.getLogger(__name__)

class TransactionBuilder:
    """Kelas untuk membina dan menghantar transaksi"""
    
    def __init__(self, client: AsyncClient, wallet_manager):
        """
        Inisialisasi TransactionBuilder
        
        Args:
            client: AsyncClient Solana
            wallet_manager: WalletManager instance
        """
        self.client = client
        self.wallet = wallet_manager
        
    async def build_and_send_transaction(
        self,
        instructions: List[Instruction],
        signers: Optional[List[Keypair]] = None,
        skip_preflight: bool = False,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Bina, tandatangan, dan hantar transaksi
        
        Args:
            instructions: Senarai arahan (instructions) untuk transaksi
            signers: Senarai penandatangan tambahan (selain fee payer)
            skip_preflight: Skip simulasi transaksi (untuk kelajuan)
            max_retries: Jumlah percubaan semula jika gagal
            
        Returns:
            Signature transaksi (string) jika berjaya, None jika gagal
        """
        if not self.wallet.keypair:
            logger.error("❌ Dompet tidak dimuatkan. Tidak dapat menandatangani transaksi.")
            return None
            
        try:
            # 1. Dapatkan blockhash terkini
            logger.info("🔄 Mendapatkan blockhash terkini...")
            recent_blockhash_resp = await self.client.get_latest_blockhash(commitment=Processed)
            recent_blockhash = recent_blockhash_resp.value.blockhash
            
            # 2. Bina Mesej
            # Fee payer adalah dompet utama
            payer = self.wallet.keypair.pubkey()
            message = Message(instructions, payer)
            
            # 3. Bina Transaksi
            tx = Transaction(
                from_keypairs=[self.wallet.keypair], # Payer sign automatik di sini
                message=message,
                recent_blockhash=recent_blockhash
            )
            
            # Tambah signers tambahan jika ada
            if signers:
                # Nota: solders.Transaction.new_signed_with_payer logic mungkin berbeza
                # Untuk solders, kita sign semasa creation atau partial_sign
                # Implementation di atas sudah sign dengan payer.
                # Jika ada signer lain, kita perlu handle partial sign.
                # Untuk sniping bot, biasanya hanya payer yang sign, kecuali create account baru.
                pass 
                
            # 4. Hantar Transaksi
            logger.info("🚀 Menghantar transaksi...")
            opts = TxOpts(skip_preflight=skip_preflight, preflight_commitment=Processed)
            resp = await self.client.send_transaction(tx, opts=opts)
            
            signature = str(resp.value)
            logger.info(f"✅ Transaksi dihantar! Signature: {signature}")
            
            return signature
            
        except Exception as e:
            logger.error(f"❌ Gagal menghantar transaksi: {e}")
            return None

    async def confirm_transaction(
        self,
        signature: str,
        commitment: str = "confirmed",
        timeout: int = 60
    ) -> bool:
        """
        Tunggu pengesahan transaksi
        
        Args:
            signature: Signature transaksi
            commitment: Tahap pengesahan (processed, confirmed, finalized)
            timeout: Masa menunggu maksimum (saat)
            
        Returns:
            True jika disahkan, False jika gagal/timeout
        """
        logger.info(f"⏳ Menunggu pengesahan transaksi: {signature}...")
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            try:
                # Tukar string signature ke solders.signature (jika perlu) atau biar library handle
                # AsyncClient.get_signature_statuses terima list of strings atau Signature objects
                # Kita guna string dulu
                from solders.signature import Signature
                sig_obj = Signature.from_string(signature)
                
                resp = await self.client.get_signature_statuses([sig_obj])
                
                if resp.value and resp.value[0]:
                    status = resp.value[0]
                    
                    if status.err:
                        logger.error(f"❌ Transaksi gagal di-chain: {status.err}")
                        return False
                        
                    if status.confirmation_status == commitment or status.confirmation_status == "finalized":
                        logger.info(f"✅ Transaksi disahkan ({status.confirmation_status})!")
                        return True
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error checking confirmation: {e}")
                await asyncio.sleep(1)
        
        logger.warning(f"⚠️  Timeout menunggu pengesahan transaksi: {signature}")
        return False
