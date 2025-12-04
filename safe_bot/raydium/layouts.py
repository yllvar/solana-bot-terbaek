"""
Layout struktur data untuk Raydium dan Serum/OpenBook
"""
from construct import Bytes, Int8ul, Int64ul, BytesInteger, Struct, Padding, Array

# Definisi custom untuk Int128ul (Unsigned Little Endian 128-bit)
Int128ul = BytesInteger(16, swapped=True)

# Layout untuk arahan Swap
SWAP_LAYOUT = Struct(
    "instruction" / Int8ul,
    "amount_in" / Int64ul,
    "min_amount_out" / Int64ul
)

# Layout lengkap untuk AMM Info V4 (OpenBook/Serum based)
AMM_INFO_LAYOUT_V4 = Struct(
    "status" / Int64ul,
    "nonce" / Int64ul,
    "order_num" / Int64ul,
    "depth" / Int64ul,
    "base_decimal" / Int64ul,
    "quote_decimal" / Int64ul,
    "state" / Int64ul,
    "reset_flag" / Int64ul,
    "min_size" / Int64ul,
    "vol_max_cut_ratio" / Int64ul,
    "amount_wave_ratio" / Int64ul,
    "base_lot_size" / Int64ul,
    "quote_lot_size" / Int64ul,
    "min_price_multiplier" / Int64ul,
    "max_price_multiplier" / Int64ul,
    "system_decimal_value" / Int64ul,
    "swap_fee_numerator" / Int64ul,
    "swap_fee_denominator" / Int64ul,
    "lp_price" / Int64ul,
    "base_need_take_pnl" / Int64ul,
    "quote_need_take_pnl" / Int64ul,
    "quote_total_pnl" / Int64ul,
    "base_total_pnl" / Int64ul,
    "pool_open_time" / Int64ul,
    "punish_pc_amount" / Int64ul,
    "punish_coin_amount" / Int64ul,
    "orderbook_to_init_time" / Int64ul,
    "swap_base_in_amount" / Int128ul,
    "swap_quote_out_amount" / Int128ul,
    "swap_base_2_quote_fee" / Int64ul,
    "swap_quote_in_amount" / Int128ul,
    "swap_base_out_amount" / Int128ul,
    "swap_quote_2_base_fee" / Int64ul,
    # Vaults & Mints
    "base_vault" / Bytes(32),       # Alamat Base Token Vault
    "quote_vault" / Bytes(32),      # Alamat Quote Token Vault
    "base_mint" / Bytes(32),        # Alamat Base Token Mint
    "quote_mint" / Bytes(32),       # Alamat Quote Token Mint
    "lp_mint" / Bytes(32),          # Alamat LP Token Mint
    
    # Market Info
    "open_orders" / Bytes(32),      # Open Orders Account
    "market_id" / Bytes(32),        # Market ID (Serum/OpenBook)
    "market_program_id" / Bytes(32),# Market Program ID
    "target_orders" / Bytes(32),    # Target Orders
    "withdraw_queue" / Bytes(32),   # Withdraw Queue
    "lp_vault" / Bytes(32),         # LP Token Vault
    "amm_owner" / Bytes(32),        # AMM Owner Authority
    "lp_amount" / Int64ul,          # LP Amount
    "client_order_id" / Int64ul,    # Client Order ID
    
    Padding(128) # Padding baki
)

# Layout untuk Serum/OpenBook Market V3
MARKET_LAYOUT_V3 = Struct(
    Padding(5), # Blob(5) "account flags"
    "account_flags" / Bytes(4),
    "own_address" / Bytes(32),
    "vault_signer_nonce" / Int64ul,
    "base_mint" / Bytes(32),
    "quote_mint" / Bytes(32),
    "base_vault" / Bytes(32),
    "base_deposits_total" / Int64ul,
    "base_fees_accrued" / Int64ul,
    "quote_vault" / Bytes(32),
    "quote_deposits_total" / Int64ul,
    "quote_fees_accrued" / Int64ul,
    "quote_dust_threshold" / Int64ul,
    "request_queue" / Bytes(32),
    "event_queue" / Bytes(32),
    "bids" / Bytes(32),
    "asks" / Bytes(32),
    "base_lot_size" / Int64ul,
    "quote_lot_size" / Int64ul,
    "fee_rate_bps" / Int64ul,
    "referrer_rebates_accrued" / Int64ul,
    Padding(7)
)
