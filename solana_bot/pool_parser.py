"""
Raydium Pool Parser - Proper transaction parsing for pool detection.

This module handles parsing of Raydium AMM initialize2 transactions
to accurately extract pool information for new pool detection.
"""
import base64
import logging
import struct
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

from solders.pubkey import Pubkey

logger = logging.getLogger(__name__)


class PoolVersion(Enum):
    """Raydium pool version types"""
    V4 = "v4"           # Legacy AMM V4
    CP_SWAP = "cp_swap"  # Concentrated Pool (Token-2022 compatible)
    CLMM = "clmm"       # Concentrated Liquidity Market Maker
    UNKNOWN = "unknown"


@dataclass
class PoolInfo:
    """Information about a detected Raydium pool"""
    pool_address: str      # AMM ID
    base_mint: str         # Base token mint (usually the new token)
    quote_mint: str        # Quote token mint (usually SOL/WSOL)
    base_vault: str        # Base token vault
    quote_vault: str       # Quote token vault
    lp_mint: str           # LP token mint
    open_orders: str       # Serum open orders account
    market_id: str         # Serum market ID
    version: PoolVersion
    timestamp: float
    
    def is_sol_pair(self) -> bool:
        """Check if this is a SOL pair (most common for new tokens)"""
        WSOL = "So11111111111111111111111111111111111111112"
        return self.base_mint == WSOL or self.quote_mint == WSOL
    
    def get_token_mint(self) -> str:
        """Get the non-SOL token mint address"""
        WSOL = "So11111111111111111111111111111111111111112"
        if self.base_mint == WSOL:
            return self.quote_mint
        return self.base_mint
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'pool_address': self.pool_address,
            'token_address': self.get_token_mint(),
            'base_mint': self.base_mint,
            'quote_mint': self.quote_mint,
            'base_vault': self.base_vault,
            'quote_vault': self.quote_vault,
            'lp_mint': self.lp_mint,
            'open_orders': self.open_orders,
            'market_id': self.market_id,
            'version': self.version.value,
            'is_sol_pair': self.is_sol_pair(),
            'timestamp': self.timestamp
        }


class RaydiumPoolParser:
    """
    Parser for Raydium pool initialization transactions.
    
    Supports detection of:
    - Raydium AMM V4 (initialize2 instruction)
    - CP-Swap (Standard AMM for Token-2022)
    """
    
    # Raydium Program IDs
    RAYDIUM_V4_PROGRAM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
    RAYDIUM_CP_SWAP_PROGRAM = "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C"
    RAYDIUM_CLMM_PROGRAM = "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
    
    # Initialize2 instruction discriminator (first 8 bytes)
    # This is derived from anchor's instruction discriminator
    INITIALIZE2_DISCRIMINATOR = bytes([175, 175, 109, 31, 13, 152, 155, 237])
    
    # Account indices in initialize2 instruction
    # Based on Raydium V4 SDK
    ACCOUNT_INDICES = {
        'token_program': 0,
        'system_program': 1,
        'rent': 2,
        'amm': 3,              # AMM account (pool address)
        'amm_authority': 4,
        'amm_open_orders': 5,
        'lp_mint': 6,
        'coin_mint': 7,        # Base token mint
        'pc_mint': 8,          # Quote token mint (usually WSOL)
        'coin_vault': 9,       # Base vault
        'pc_vault': 10,        # Quote vault
        'target_orders': 11,
        'serum_market': 12,
        'serum_program': 13,
        'user_wallet': 14,
        'user_coin_token': 15,
        'user_pc_token': 16,
        'user_lp_token': 17,
    }

    def __init__(self):
        self.program_ids = {
            self.RAYDIUM_V4_PROGRAM: PoolVersion.V4,
            self.RAYDIUM_CP_SWAP_PROGRAM: PoolVersion.CP_SWAP,
            self.RAYDIUM_CLMM_PROGRAM: PoolVersion.CLMM,
        }
    
    def detect_pool_version(self, program_id: str) -> PoolVersion:
        """Detect pool version from program ID"""
        return self.program_ids.get(program_id, PoolVersion.UNKNOWN)
    
    def is_raydium_program(self, program_id: str) -> bool:
        """Check if the program ID is a known Raydium program"""
        return program_id in self.program_ids
    
    def parse_transaction_logs(
        self,
        logs: List[str],
        timestamp: float
    ) -> Optional[PoolInfo]:
        """
        Parse transaction logs to detect pool initialization.
        
        This method looks for "ray_log" entries in logs and decodes them.
        It's the primary method for WebSocket-based detection.
        
        Args:
            logs: List of log strings from transaction
            timestamp: Unix timestamp of detection
            
        Returns:
            PoolInfo if this is a pool initialization, None otherwise
        """
        try:
            for log in logs:
                # Check for Raydium program invocation
                if "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke" in log:
                    logger.debug("Found Raydium V4 program invocation")
                    
                # Look for ray_log entries
                if "ray_log:" in log:
                    logger.debug(f"Found ray_log entry")
                    pool_info = self._decode_ray_log(log, timestamp)
                    if pool_info:
                        return pool_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing transaction logs: {e}")
            return None
    
    def parse_initialize2_accounts(
        self,
        accounts: List[str],
        timestamp: float
    ) -> Optional[PoolInfo]:
        """
        Parse pool info directly from initialize2 instruction accounts.
        
        This is the most reliable method when we have parsed transaction data.
        
        Args:
            accounts: List of account pubkeys from the instruction
            timestamp: Unix timestamp
            
        Returns:
            PoolInfo with extracted addresses
        """
        try:
            if len(accounts) < 18:
                logger.warning(f"Not enough accounts for initialize2: {len(accounts)}")
                return None
            
            idx = self.ACCOUNT_INDICES
            
            pool_info = PoolInfo(
                pool_address=accounts[idx['amm']],
                base_mint=accounts[idx['coin_mint']],
                quote_mint=accounts[idx['pc_mint']],
                base_vault=accounts[idx['coin_vault']],
                quote_vault=accounts[idx['pc_vault']],
                lp_mint=accounts[idx['lp_mint']],
                open_orders=accounts[idx['amm_open_orders']],
                market_id=accounts[idx['serum_market']],
                version=PoolVersion.V4,
                timestamp=timestamp
            )
            
            logger.info(f"✅ Parsed pool from accounts: {pool_info.pool_address}")
            return pool_info
            
        except Exception as e:
            logger.error(f"Error parsing initialize2 accounts: {e}")
            return None
    
    def _decode_ray_log(self, log: str, timestamp: float) -> Optional[PoolInfo]:
        """
        Decode Raydium ray_log data.
        
        Format: "Program log: ray_log: <BASE64_DATA>"
        
        Ray log structure for init (log_type = 0):
        - Offset 0:   log_type (1 byte)
        - Offset 1:   open_time (8 bytes, u64)
        - Offset 9:   init_pc_amount (8 bytes, u64)
        - Offset 17:  init_coin_amount (8 bytes, u64)
        ... various fields ...
        - Offset 75+: Pubkeys (32 bytes each)
        """
        try:
            parts = log.split("ray_log: ")
            if len(parts) < 2:
                return None
                
            b64_data = parts[1].strip()
            data = base64.b64decode(b64_data)
            
            # Check minimum length for init log
            if len(data) < 100:
                logger.debug(f"ray_log too short ({len(data)} bytes), not init log")
                return None
            
            log_type = data[0]
            
            # Log type 0 = Initialize
            if log_type != 0:
                logger.debug(f"ray_log type {log_type}, not init (type 0)")
                return None
            
            logger.info("🎯 Detected ray_log init log (type 0)")
            
            # Parse pubkeys from known offsets
            # Note: These offsets are for the init log structure
            # They may vary slightly between versions
            
            try:
                # Try to extract key addresses
                # The exact layout depends on Raydium version
                # We'll try multiple offset patterns
                
                pool_info = self._try_parse_init_log_v1(data, timestamp)
                if pool_info:
                    return pool_info
                    
                pool_info = self._try_parse_init_log_v2(data, timestamp)
                if pool_info:
                    return pool_info
                    
            except Exception as e:
                logger.warning(f"Error parsing ray_log init data: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error decoding ray_log: {e}")
            return None
    
    def _try_parse_init_log_v1(self, data: bytes, timestamp: float) -> Optional[PoolInfo]:
        """
        Try parsing with V1 offset layout.
        
        Layout (approximate):
        - log_type: 1 byte (offset 0)
        - open_time: 8 bytes (offset 1)
        - pc_decimals: 1 byte (offset 9)
        - coin_decimals: 1 byte (offset 10)
        - pc_lot_size: 8 bytes (offset 11)
        - coin_lot_size: 8 bytes (offset 19)
        - pc_amount: 8 bytes (offset 27)
        - coin_amount: 8 bytes (offset 35)
        - market: 32 bytes (offset 43)
        ... more pubkeys follow
        """
        try:
            if len(data) < 395:  # Minimum for full init log
                return None
            
            # Known working offsets for Raydium V4 init log
            offsets = {
                'market': 43,
                'amm_id': 267,
                'lp_mint': 299,
                'coin_mint': 331,
                'pc_mint': 363,
            }
            
            def read_pubkey(offset: int) -> str:
                return str(Pubkey.from_bytes(data[offset:offset+32]))
            
            pool_info = PoolInfo(
                pool_address=read_pubkey(offsets['amm_id']),
                base_mint=read_pubkey(offsets['coin_mint']),
                quote_mint=read_pubkey(offsets['pc_mint']),
                base_vault="",  # Not in ray_log, need to fetch separately
                quote_vault="",
                lp_mint=read_pubkey(offsets['lp_mint']),
                open_orders="",
                market_id=read_pubkey(offsets['market']),
                version=PoolVersion.V4,
                timestamp=timestamp
            )
            
            # Validate - check if quote is WSOL (most new pools are Token/SOL)
            WSOL = "So11111111111111111111111111111111111111112"
            if pool_info.quote_mint == WSOL or pool_info.base_mint == WSOL:
                logger.info(f"✅ Valid SOL pair detected via ray_log V1")
                return pool_info
            
            # If not SOL pair, might still be valid (e.g., Token/USDC)
            return pool_info
            
        except Exception as e:
            logger.debug(f"V1 layout parse failed: {e}")
            return None
    
    def _try_parse_init_log_v2(self, data: bytes, timestamp: float) -> Optional[PoolInfo]:
        """
        Try parsing with alternative offset layout.
        
        Some versions have slightly different offsets.
        """
        try:
            if len(data) < 300:
                return None
            
            # Alternative offsets
            offsets = {
                'amm_id': 203,
                'coin_mint': 235,
                'pc_mint': 267,
            }
            
            def read_pubkey(offset: int) -> str:
                return str(Pubkey.from_bytes(data[offset:offset+32]))
            
            pool_info = PoolInfo(
                pool_address=read_pubkey(offsets['amm_id']),
                base_mint=read_pubkey(offsets['coin_mint']),
                quote_mint=read_pubkey(offsets['pc_mint']),
                base_vault="",
                quote_vault="",
                lp_mint="",
                open_orders="",
                market_id="",
                version=PoolVersion.V4,
                timestamp=timestamp
            )
            
            return pool_info
            
        except Exception as e:
            logger.debug(f"V2 layout parse failed: {e}")
            return None
    
    def is_initialize_instruction(self, logs: List[str]) -> bool:
        """
        Check if transaction logs indicate a pool initialization.
        
        More accurate than simple keyword matching - checks for
        both program invocation and success.
        
        Args:
            logs: Transaction log strings
            
        Returns:
            True if this appears to be a pool initialization
        """
        has_raydium_invoke = False
        has_init_log = False
        has_success = False
        
        for log in logs:
            # Check for Raydium V4 program invocation
            if "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 invoke" in log:
                has_raydium_invoke = True
            
            # Check for ray_log (indicates pool operation)
            if "ray_log:" in log:
                has_init_log = True
            
            # Check for program success (not just invocation)
            if "Program 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8 success" in log:
                has_success = True
        
        # All conditions must be met
        result = has_raydium_invoke and has_init_log and has_success
        
        if result:
            logger.debug("✅ Transaction appears to be pool initialization")
        elif has_raydium_invoke:
            logger.debug("⚠️ Raydium tx but not pool init (missing ray_log or success)")
        
        return result
    
    def filter_init_logs_only(self, logs: List[str]) -> bool:
        """
        Filter to only detect actual initialization transactions.
        
        Distinguishes from regular swaps, deposits, etc.
        """
        for log in logs:
            if "ray_log:" in log:
                # Decode and check log type
                try:
                    parts = log.split("ray_log: ")
                    if len(parts) >= 2:
                        data = base64.b64decode(parts[1].strip())
                        if len(data) > 0 and data[0] == 0:  # log_type 0 = init
                            return True
                except:
                    pass
        return False
