# Solana Sniping Bot - Codebase Index

## Project Overview
A Solana trading bot designed for token sniping and automated trading on the Raydium DEX. The bot provides features like instant token purchases on launch, take-profit automation, and rug-pull protection.

## Technology Stack
- **Language**: Python 3.13+
- **Blockchain**: Solana
- **DEX**: Raydium
- **Key Libraries**: solders, solana, base58, requests, colorama

## Project Structure

### Root Directory
```
/Users/apple/solana-sniping-bot-main/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── checkbalance.py        # SOL balance checking utility
├── getwallet.py           # Wallet management from private keys
├── loadkey.py             # Key loading utilities
├── symbol.py              # Token symbol handling
├── snip_token.txt         # Token configuration (gitignored)
├── LOG                    # Log file (gitignored)
└── .gitignore            # Git ignore rules
```

### Core Modules

#### `/raydium/` - Raydium DEX Integration
- **Raydium.py**: Core Raydium protocol interface
- **buy_swap.py**: Token purchase/swap logic
- **sell_swap.py**: Token selling/swap logic
- **async_txn.py**: Asynchronous transaction handling
- **create_close_account.py**: Account creation and closure
- **layouts.py**: Data structure layouts for Raydium
- **new_pool_address_identifier.py**: Pool address detection

#### `/utils/` - Utility Functions
- **__init__.py**: Package initialization
- **_core.py**: Core utility functions (7KB)
- **contract.py**: Smart contract interactions (8.6KB)
- **checkbalance.py**: Balance checking utilities
- **getwallet.py**: Wallet utilities
- **layouts.py**: Data structure layouts (4.5KB)
- **features.py**: Feature flags and configuration
- **test_*.py**: Test files for various components

#### `/monitoring_price/` - Price Monitoring
- **monitor_price_strategy.py**: Price monitoring and strategy execution

#### `/py_modules/` - Extended Python Modules
Large collection of monitoring and integration modules (96 items):
- **beanstalk/**: Beanstalk integration
- **bind_xml/**: XML binding utilities
- **elasticsearch/**: Elasticsearch integration
- **mongodb/**: MongoDB integration
- **jenkins/**: Jenkins integration
- **memcached_maxage/**: Memcached utilities
- **nginx/**: Nginx status monitoring
- And many more...

#### `/data/` - Data Storage
- Contains runtime data and configuration (2 items)

#### `/.github/` - GitHub Configuration
- GitHub Actions and repository configuration (2 items)

## Key Components

### Main Application Flow
1. **Entry Point**: `main.py` imports from `utils.contract` and calls `main()`
2. **Wallet Setup**: Uses `getwallet.py` to load wallet from private key
3. **Balance Check**: Verifies SOL balance via `checkbalance.py`
4. **Trading Logic**: Executes through Raydium integration modules

### Data Structures
- **SWAP_LAYOUT**: Defines swap instruction format (amount_in, min_amount_out)
- **AMM_INFO_LAYOUT_V4**: Raydium AMM pool information structure
- **MARKET_STATE_LAYOUT_V3**: Market state data structure
- **POOL_INFO_LAYOUT**: Pool information layout

### Core Features
1. **Token Sniping**: Instant buy on liquidity addition
2. **Take Profit**: Automated selling at target percentage
3. **Buy/Sell Multiple Times**: Repeated order execution
4. **Sell Limit Orders**: Predetermined price selling
5. **Rug Pull Protection**: Risk score checking

### Configuration Parameters
- **BALANCE**: Display balance and profit
- **BUY DELAY**: Seconds after launch (0 = immediate)
- **TAKE PROFIT**: Target profit percentage
- **SELL DELAY**: Seconds before selling (0 = immediate)
- **CHECK RUG**: Enable/disable rug pull protection

## WebSocket Integration
The codebase includes WebSocket functionality for real-time updates:
- Account subscription/unsubscription
- Real-time pool monitoring
- Transaction status tracking

## RPC Node Management
- Dynamic RPC node discovery via `getClusterNodes`
- Version filtering for node selection
- Private RPC support
- IP blacklisting capability
- Connection timeout handling

## Error Handling
- Timeout management for network requests
- Invalid private key validation
- Connection error recovery
- Unknown error tracking with counters

## Dependencies
```
solders       # Solana SDK
solana        # Solana Python client
base58        # Base58 encoding
requests      # HTTP library
colorama      # Terminal colors
```

## Security Considerations
- Private keys stored in environment/config (gitignored)
- Wallet addresses exposed only when necessary
- Transaction signing handled securely
- RPC endpoint validation

## Development Notes
- Uses Python 3.13+ features
- Async/await pattern for concurrent operations
- Construct library for binary data structures
- Type hints for better code clarity

## Testing
Test files located in `/utils/`:
- `test_async_client.py`: Async client testing
- `test_memo_program.py`: Memo program tests
- `test_security_txt.py`: Security validation
- `test_spl_token_instructions.py`: SPL token instruction tests
- `test_token_client.py`: Token client tests
- `test_transaction.py`: Transaction tests
- `test_vote_program.py`: Vote program tests

## File Statistics
- **Total Python Files**: 60+
- **Main Application**: ~267 lines
- **Core Utils**: ~7KB (_core.py), ~8.6KB (contract.py)
- **Test Coverage**: 7 test files

## Next Steps for Development
1. Review and update dependencies in requirements.txt
2. Implement comprehensive error logging
3. Add configuration file support (.env)
4. Enhance test coverage
5. Document API endpoints and RPC methods
6. Add monitoring and alerting
7. Implement rate limiting for RPC calls

## Git Repository
- **Status**: Freshly initialized
- **Branch**: main (default)
- **Remote**: Not configured
- **Ignored Files**: Private keys, logs, data, cache files

---
*Last Updated: 2025-12-04*
*Index Version: 1.0*
