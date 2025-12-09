from construct import Bytes, Int8ul, Int64ul, BytesInteger
from construct import Struct as cStruct 

"""Thanks to v0idum for creating layouts in python""" 


POOL_INFO_LAYOUT = cStruct(
    "instruction" / Int8ul,
    "simulate_type" / Int8ul
)

SWAP_LAYOUT = cStruct(
    "instruction" / Int8ul,
    "amount_in" / Int64ul,
    "min_amount_out" / Int64ul
)

AMM_INFO_LAYOUT_V4 = cStruct(
    'status' / Int64ul,
    'nonce' / Int64ul,
    'order_num' / Int64ul,
    'depth' / Int64ul,
    'base_decimal' / Int64ul,
    'quote_decimal' / Int64ul,
    'state' / Int64ul,
    'reset_flag' / Int64ul,
    'min_size' / Int64ul,
    'vol_max_cut_ratio' / Int64ul,
    'amount_wave_ratio' / Int64ul,
    'base_lot_size' / Int64ul,
    'quote_lot_size' / Int64ul,
    'min_price_multiplier' / Int64ul,
    'max_price_multiplier' / Int64ul,
    'system_decimal_value' / Int64ul,
    'swap_fee_numerator' / Int64ul,
    'swap_fee_denominator' / Int64ul,
    'amm_owner' / Bytes(32),
    'lpReserve' / Int64ul,
    'coin_decimals' / Int64ul,
    'pc_decimals' / Int64ul,
    'coin_lot_size' / Int64ul,
    'pc_lot_size' / Int64ul,
    'coin_mint_address' / Bytes(32),
    'pc_mint_address' / Bytes(32),
    'lp_mint_address' / Bytes(32),
    'amm_coin_vault_mint_address' / Bytes(32),
    'amm_pc_vault_mint_address' / Bytes(32),
    'amm_lp_mint_address' / Bytes(32),
    'amm_coin_vault_address' / Bytes(32),
    'amm_pc_vault_address' / Bytes(32),
    'amm_withdraw_queue' / Bytes(32),
    'amm_temp_lp_token_account' / Bytes(32),
    'serum_program_id' / Bytes(32),
    'amm_target_orders' / Bytes(32),
    'amm_quantities' / Bytes(32),
    'pool_coin_token_account' / Bytes(32),
    'pool_pc_token_account' / Bytes(32),
    'coin_mint_address' / Bytes(32),
    'pc_mint_address' / Bytes(32),
    'lp_mint_address' / Bytes(32),
)

MARKET_LAYOUT_V3 = cStruct(
    'blob5' / Bytes(5),
    'account_flags_layout' / Bytes(8),
    'blob40' / Bytes(40),
    'vault_signer_nonce' / Int64ul,
    'base_mint' / Bytes(32),
    'quote_mint' / Bytes(32),
    'base_vault' / Bytes(32),
    'base_withdraw_queue' / Bytes(32),
    'base_min_size' / Int64ul,
    'quote_vault' / Bytes(32),
    'quote_withdraw_queue' / Bytes(32),
    'quote_min_size' / Int64ul,
    'base_lot_size' / Int64ul,
    'quote_lot_size' / Int64ul,
    'fee_rate_bps' / Int64ul,
    'referrer_rebates_accrued' / Int64ul,
    'blob7' / Bytes(7),
)
