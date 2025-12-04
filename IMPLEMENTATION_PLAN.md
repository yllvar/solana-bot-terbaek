# 🎯 Rancangan Pembinaan Bot Solana Sniping - Lengkap

## 📋 Gambaran Keseluruhan

Dokumen ini mengandungi rancangan terperinci untuk melengkapkan bot Solana sniping dengan semua ciri yang diperlukan.

---

## 🏗️ Fasa 1: Raydium Swap Integration (KEUTAMAAN TINGGI)

### 1.1 Swap Instruction Building

#### Objektif:
Bina instruction untuk swap token di Raydium AMM

#### Fail Baharu:
- `safe_bot/raydium/swap.py`
- `safe_bot/raydium/layouts.py`
- `safe_bot/raydium/constants.py`

#### Implementasi:

**A. Constants & Layouts**
```python
# safe_bot/raydium/constants.py
RAYDIUM_AMM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_AUTHORITY_V4 = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
SERUM_PROGRAM_ID = "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
WSOL_MINT = "So11111111111111111111111111111111111111112"

# Instruction indices
SWAP_INSTRUCTION = 9
```

**B. Swap Layout**
```python
# safe_bot/raydium/layouts.py
from construct import Struct, Int8ul, Int64ul

SWAP_LAYOUT = Struct(
    "instruction" / Int8ul,
    "amount_in" / Int64ul,
    "min_amount_out" / Int64ul
)

AMM_INFO_LAYOUT_V4 = Struct(
    "status" / Int64ul,
    "nonce" / Int64ul,
    "order_num" / Int64ul,
    "depth" / Int64ul,
    "base_decimal" / Int64ul,
    "quote_decimal" / Int64ul,
    # ... (lengkap dengan semua field)
)
```

**C. Swap Builder**
```python
# safe_bot/raydium/swap.py
class RaydiumSwap:
    def __init__(self, client, wallet):
        self.client = client
        self.wallet = wallet
    
    async def build_swap_instruction(
        self,
        pool_keys: dict,
        amount_in: int,
        min_amount_out: int,
        side: str  # "buy" or "sell"
    ):
        """Build swap instruction"""
        # 1. Get pool accounts
        # 2. Build instruction data
        # 3. Create instruction with accounts
        # 4. Return instruction
        pass
    
    async def get_pool_keys(self, pool_address: Pubkey):
        """Fetch pool keys from chain"""
        # Parse AMM account data
        # Extract all necessary keys
        pass
    
    def calculate_amount_out(
        self,
        amount_in: int,
        reserve_in: int,
        reserve_out: int,
        fee_numerator: int = 25,
        fee_denominator: int = 10000
    ):
        """Calculate expected output amount"""
        # AMM formula: (amount_in * reserve_out) / (reserve_in + amount_in)
        # With fees
        pass
```

#### Masa Anggaran: 6-8 jam
#### Kebergantungan: construct, solders
#### Testing: Unit tests untuk calculation, integration test untuk instruction building

---

### 1.2 Transaction Signing

#### Objektif:
Sign dan hantar transaksi dengan betul

#### Fail Baharu:
- `safe_bot/transaction.py`

#### Implementasi:

```python
# safe_bot/transaction.py
from solders.transaction import Transaction
from solders.message import Message
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

class TransactionBuilder:
    def __init__(self, client: AsyncClient, wallet):
        self.client = client
        self.wallet = wallet
    
    async def build_and_send_transaction(
        self,
        instructions: list,
        signers: list = None,
        skip_preflight: bool = False
    ):
        """Build, sign, and send transaction"""
        # 1. Get recent blockhash
        # 2. Create message
        # 3. Create transaction
        # 4. Sign transaction
        # 5. Send transaction
        # 6. Confirm transaction
        # 7. Return signature
        pass
    
    async def confirm_transaction(
        self,
        signature: str,
        max_retries: int = 30,
        retry_delay: float = 2.0
    ):
        """Confirm transaction with retries"""
        # Poll for confirmation
        # Handle timeout
        # Return confirmation status
        pass
    
    async def simulate_transaction(self, transaction):
        """Simulate transaction before sending"""
        # Useful for debugging
        pass
```

#### Masa Anggaran: 4-6 jam
#### Testing: Test dengan devnet dahulu

---

### 1.3 Slippage Calculation

#### Objektif:
Kira slippage dan min_amount_out dengan tepat

#### Implementasi dalam `swap.py`:

```python
def calculate_min_amount_out(
    self,
    expected_amount: int,
    slippage_bps: int
):
    """Calculate minimum amount out with slippage"""
    # slippage_bps = 500 means 5%
    # min_out = expected * (10000 - slippage_bps) / 10000
    slippage_multiplier = (10000 - slippage_bps) / 10000
    return int(expected_amount * slippage_multiplier)

def calculate_price_impact(
    self,
    amount_in: int,
    reserve_in: int,
    reserve_out: int
):
    """Calculate price impact percentage"""
    # Price impact = (amount_in / reserve_in) * 100
    # Higher impact = worse execution
    pass
```

#### Masa Anggaran: 2-3 jam
#### Testing: Test dengan pelbagai nilai slippage

---

## 🏗️ Fasa 2: Price Monitoring (KEUTAMAAN TINGGI)

### 2.1 Real-time Price Tracking

#### Objektif:
Monitor harga token secara real-time

#### Fail Baharu:
- `safe_bot/price_tracker.py`

#### Implementasi:

```python
# safe_bot/price_tracker.py
import asyncio
from typing import Dict, Optional, Callable

class PriceTracker:
    def __init__(self, client, raydium_swap):
        self.client = client
        self.raydium = raydium_swap
        self.prices: Dict[str, float] = {}
        self.tracking: Dict[str, bool] = {}
        self.callbacks: Dict[str, list] = {}
    
    async def start_tracking(
        self,
        token_mint: str,
        pool_address: str,
        interval: float = 1.0
    ):
        """Start tracking price for a token"""
        self.tracking[token_mint] = True
        
        while self.tracking.get(token_mint):
            try:
                # 1. Fetch pool reserves
                pool_data = await self.get_pool_data(pool_address)
                
                # 2. Calculate current price
                price = self.calculate_price(pool_data)
                
                # 3. Update price
                old_price = self.prices.get(token_mint)
                self.prices[token_mint] = price
                
                # 4. Trigger callbacks if price changed
                if old_price and price != old_price:
                    await self.trigger_callbacks(token_mint, price, old_price)
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error tracking price: {e}")
                await asyncio.sleep(interval)
    
    def stop_tracking(self, token_mint: str):
        """Stop tracking price"""
        self.tracking[token_mint] = False
    
    def register_callback(
        self,
        token_mint: str,
        callback: Callable
    ):
        """Register callback for price changes"""
        if token_mint not in self.callbacks:
            self.callbacks[token_mint] = []
        self.callbacks[token_mint].append(callback)
    
    async def get_pool_data(self, pool_address: str):
        """Fetch pool data from chain"""
        # Get account info
        # Parse reserves
        # Return pool data
        pass
    
    def calculate_price(self, pool_data: dict) -> float:
        """Calculate token price from pool reserves"""
        # price = quote_reserve / base_reserve
        # Adjust for decimals
        pass
```

#### Masa Anggaran: 6-8 jam
#### Testing: Monitor beberapa token secara serentak

---

### 2.2 Profit/Loss Calculation

#### Objektif:
Kira P&L dengan tepat untuk trigger take profit/stop loss

#### Implementasi dalam `price_tracker.py`:

```python
class PositionTracker:
    def __init__(self):
        self.positions: Dict[str, dict] = {}
    
    def open_position(
        self,
        token_mint: str,
        entry_price: float,
        amount: float,
        cost_sol: float
    ):
        """Record new position"""
        self.positions[token_mint] = {
            'entry_price': entry_price,
            'amount': amount,
            'cost_sol': cost_sol,
            'entry_time': time.time()
        }
    
    def calculate_pnl(
        self,
        token_mint: str,
        current_price: float
    ) -> dict:
        """Calculate P&L for position"""
        if token_mint not in self.positions:
            return None
        
        pos = self.positions[token_mint]
        current_value = pos['amount'] * current_price
        pnl_sol = current_value - pos['cost_sol']
        pnl_percentage = (pnl_sol / pos['cost_sol']) * 100
        
        return {
            'pnl_sol': pnl_sol,
            'pnl_percentage': pnl_percentage,
            'current_value': current_value,
            'entry_price': pos['entry_price'],
            'current_price': current_price,
            'holding_time': time.time() - pos['entry_time']
        }
    
    def close_position(self, token_mint: str):
        """Close position"""
        if token_mint in self.positions:
            del self.positions[token_mint]
```

#### Masa Anggaran: 3-4 jam

---

### 2.3 Take Profit / Stop Loss Triggers

#### Objektif:
Auto-trigger jual apabila mencapai target

#### Fail Baharu:
- `safe_bot/triggers.py`

#### Implementasi:

```python
# safe_bot/triggers.py
class TradeTriggers:
    def __init__(
        self,
        price_tracker: PriceTracker,
        position_tracker: PositionTracker,
        raydium_swap: RaydiumSwap
    ):
        self.price_tracker = price_tracker
        self.position_tracker = position_tracker
        self.raydium = raydium_swap
        self.active_triggers: Dict[str, dict] = {}
    
    def set_take_profit(
        self,
        token_mint: str,
        target_percentage: float
    ):
        """Set take profit trigger"""
        self.active_triggers[token_mint] = {
            'type': 'take_profit',
            'target': target_percentage,
            'enabled': True
        }
    
    def set_stop_loss(
        self,
        token_mint: str,
        stop_percentage: float
    ):
        """Set stop loss trigger"""
        if token_mint not in self.active_triggers:
            self.active_triggers[token_mint] = {}
        
        self.active_triggers[token_mint]['stop_loss'] = {
            'target': stop_percentage,
            'enabled': True
        }
    
    async def check_triggers(
        self,
        token_mint: str,
        current_price: float
    ):
        """Check if any triggers should fire"""
        if token_mint not in self.active_triggers:
            return
        
        # Calculate current P&L
        pnl = self.position_tracker.calculate_pnl(token_mint, current_price)
        if not pnl:
            return
        
        triggers = self.active_triggers[token_mint]
        
        # Check take profit
        if 'take_profit' in triggers and triggers['take_profit']['enabled']:
            if pnl['pnl_percentage'] >= triggers['take_profit']['target']:
                await self.execute_sell(token_mint, "TAKE PROFIT")
                return
        
        # Check stop loss
        if 'stop_loss' in triggers and triggers['stop_loss']['enabled']:
            if pnl['pnl_percentage'] <= -triggers['stop_loss']['target']:
                await self.execute_sell(token_mint, "STOP LOSS")
                return
    
    async def execute_sell(self, token_mint: str, reason: str):
        """Execute sell order"""
        logger.info(f"🎯 Triggering {reason} for {token_mint}")
        
        # 1. Get position info
        # 2. Build sell transaction
        # 3. Execute sell
        # 4. Close position
        # 5. Log result
        pass
```

#### Masa Anggaran: 5-6 jam
#### Testing: Simulate dengan harga palsu

---

## 🏗️ Fasa 3: Auto Buy Logic (KEUTAMAAN SEDERHANA)

### 3.1 Buy Execution

#### Objektif:
Execute pembelian automatik apabila pool baharu dijumpai

#### Fail: Update `safe_bot/monitor.py`

#### Implementasi:

```python
# Tambah dalam PoolMonitor class
async def execute_buy(
    self,
    pool_info: dict,
    amount_sol: float,
    slippage_bps: int
):
    """Execute buy order"""
    try:
        # 1. Get pool keys
        pool_keys = await self.raydium.get_pool_keys(pool_info['pool_address'])
        
        # 2. Calculate amounts
        amount_in = int(amount_sol * 1e9)  # Convert to lamports
        expected_out = await self.raydium.calculate_amount_out(
            amount_in,
            pool_keys['quote_reserve'],
            pool_keys['base_reserve']
        )
        min_amount_out = self.raydium.calculate_min_amount_out(
            expected_out,
            slippage_bps
        )
        
        # 3. Build swap instruction
        swap_ix = await self.raydium.build_swap_instruction(
            pool_keys,
            amount_in,
            min_amount_out,
            side="buy"
        )
        
        # 4. Build and send transaction
        signature = await self.transaction_builder.build_and_send_transaction(
            [swap_ix],
            skip_preflight=True  # For speed
        )
        
        # 5. Log success
        logger.info(f"✅ Buy executed: {signature}")
        
        return signature
        
    except Exception as e:
        logger.error(f"❌ Buy failed: {e}")
        return None
```

#### Masa Anggaran: 4-5 jam

---

### 3.2 Buy Delay Handling

#### Objektif:
Implement delay sebelum beli (jika dikehendaki)

#### Implementasi:

```python
async def handle_new_pool_with_delay(
    self,
    pool_info: dict,
    delay_seconds: int
):
    """Handle new pool with optional delay"""
    if delay_seconds > 0:
        logger.info(f"⏰ Waiting {delay_seconds}s before buying...")
        await asyncio.sleep(delay_seconds)
    
    # Execute buy
    await self.execute_buy(pool_info, self.config.buy_amount, self.config.slippage_bps)
```

#### Masa Anggaran: 1-2 jam

---

### 3.3 Transaction Confirmation

#### Objektif:
Confirm transaksi dengan betul dan handle errors

#### Implementasi dalam `transaction.py`:

```python
async def wait_for_confirmation(
    self,
    signature: str,
    commitment: str = "confirmed",
    timeout: int = 60
):
    """Wait for transaction confirmation"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = await self.client.get_signature_statuses([signature])
            
            if response.value and response.value[0]:
                status = response.value[0]
                
                if status.confirmation_status == commitment:
                    if status.err:
                        raise Exception(f"Transaction failed: {status.err}")
                    return True
            
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error checking confirmation: {e}")
            await asyncio.sleep(2)
    
    raise TimeoutError(f"Transaction not confirmed within {timeout}s")
```

#### Masa Anggaran: 3-4 jam

---

## 🏗️ Fasa 4: Advanced Features (KEUTAMAAN RENDAH)

### 4.1 Multi-Wallet Support

#### Objektif:
Sokongan untuk berbilang dompet serentak

#### Fail Baharu:
- `safe_bot/multi_wallet.py`

#### Implementasi:

```python
# safe_bot/multi_wallet.py
class MultiWalletManager:
    def __init__(self, rpc_endpoint: str):
        self.wallets: Dict[str, WalletManager] = {}
        self.rpc_endpoint = rpc_endpoint
    
    def add_wallet(self, name: str, private_key: str):
        """Add wallet to manager"""
        wallet = WalletManager(self.rpc_endpoint)
        wallet.load_from_private_key(private_key)
        self.wallets[name] = wallet
    
    async def get_total_balance(self) -> float:
        """Get total balance across all wallets"""
        total = 0
        for wallet in self.wallets.values():
            total += await wallet.get_balance()
        return total
    
    def get_wallet(self, name: str) -> WalletManager:
        """Get specific wallet"""
        return self.wallets.get(name)
```

#### Masa Anggaran: 4-5 jam

---

### 4.2 Webhook Notifications

#### Objektif:
Hantar notifikasi ke Discord/Telegram

#### Fail Baharu:
- `safe_bot/notifications.py`

#### Implementasi:

```python
# safe_bot/notifications.py
import aiohttp

class WebhookNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_notification(
        self,
        title: str,
        message: str,
        color: str = "green"
    ):
        """Send webhook notification"""
        # Discord webhook format
        payload = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": self.get_color_code(color),
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_url, json=payload)
    
    async def notify_new_pool(self, pool_info: dict):
        """Notify about new pool"""
        await self.send_notification(
            "🆕 New Pool Detected",
            f"Token: {pool_info['token_address']}\nPool: {pool_info['pool_address']}",
            "blue"
        )
    
    async def notify_buy(self, token: str, amount: float, price: float):
        """Notify about buy"""
        await self.send_notification(
            "✅ Buy Executed",
            f"Token: {token}\nAmount: {amount}\nPrice: {price}",
            "green"
        )
    
    async def notify_sell(self, token: str, pnl: float, reason: str):
        """Notify about sell"""
        color = "green" if pnl > 0 else "red"
        await self.send_notification(
            f"💰 Sell Executed - {reason}",
            f"Token: {token}\nP&L: {pnl:.2f}%",
            color
        )
```

#### Masa Anggaran: 3-4 jam

---

### 4.3 Backtesting

#### Objektif:
Test strategi dengan data sejarah

#### Fail Baharu:
- `safe_bot/backtest.py`

#### Implementasi:

```python
# safe_bot/backtest.py
class Backtester:
    def __init__(self, config: BotConfig):
        self.config = config
        self.trades: list = []
        self.balance = 10.0  # Starting balance in SOL
    
    def load_historical_data(self, file_path: str):
        """Load historical price data"""
        # Load from CSV/JSON
        pass
    
    def simulate_trade(
        self,
        entry_price: float,
        exit_price: float,
        amount_sol: float
    ):
        """Simulate a trade"""
        # Calculate P&L
        # Update balance
        # Record trade
        pass
    
    def run_backtest(self, data: list):
        """Run backtest on historical data"""
        for candle in data:
            # Simulate buy logic
            # Simulate sell logic (TP/SL)
            # Track performance
            pass
    
    def generate_report(self):
        """Generate backtest report"""
        # Total trades
        # Win rate
        # Average P&L
        # Max drawdown
        # Sharpe ratio
        pass
```

#### Masa Anggaran: 8-10 jam

---

## 📊 Jadual Pembangunan

### Sprint 1 (Minggu 1-2): Raydium Integration
- [ ] Day 1-2: Swap layouts & constants
- [ ] Day 3-5: Swap instruction building
- [ ] Day 6-8: Transaction signing
- [ ] Day 9-10: Slippage calculation
- [ ] Day 11-12: Testing & debugging
- [ ] Day 13-14: Documentation

**Deliverable:** Fully working swap integration

---

### Sprint 2 (Minggu 3-4): Price Monitoring
- [ ] Day 1-3: Price tracker implementation
- [ ] Day 4-5: P&L calculation
- [ ] Day 6-8: Trigger system (TP/SL)
- [ ] Day 9-10: Integration with swap
- [ ] Day 11-12: Testing
- [ ] Day 13-14: Optimization

**Deliverable:** Working TP/SL system

---

### Sprint 3 (Minggu 5): Auto Buy
- [ ] Day 1-2: Buy execution logic
- [ ] Day 3: Delay handling
- [ ] Day 4-5: Transaction confirmation
- [ ] Day 6-7: Testing & refinement

**Deliverable:** Auto-buy functionality

---

### Sprint 4 (Minggu 6-7): Advanced Features
- [ ] Day 1-3: Multi-wallet support
- [ ] Day 4-5: Webhook notifications
- [ ] Day 6-10: Backtesting system
- [ ] Day 11-14: Final testing & polish

**Deliverable:** Complete bot with all features

---

## 🧪 Testing Strategy

### Unit Tests:
- Swap calculation functions
- P&L calculation
- Slippage calculation
- Price calculation

### Integration Tests:
- Swap instruction building
- Transaction signing
- Price tracking
- Trigger execution

### End-to-End Tests:
- Full buy flow (devnet)
- Full sell flow (devnet)
- TP/SL triggers (devnet)

### Performance Tests:
- Latency measurement
- Concurrent operations
- Memory usage

---

## 📦 Kebergantungan Tambahan

```txt
# Tambah ke requirements_safe.txt
pytest>=7.4.0              # Testing
pytest-asyncio>=0.21.0     # Async testing
python-dotenv>=1.0.0       # Environment variables
pandas>=2.0.0              # Backtesting data
matplotlib>=3.7.0          # Backtesting charts
```

---

## 🎯 Metrics untuk Kejayaan

### Performance Metrics:
- Buy latency: < 500ms from pool detection
- Transaction success rate: > 95%
- Price update frequency: < 2s
- TP/SL trigger accuracy: 100%

### Quality Metrics:
- Code coverage: > 80%
- No critical bugs
- Documentation complete
- All tests passing

---

## 🚀 Deployment Checklist

- [ ] All features implemented
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] User guide created
- [ ] Example configurations provided
- [ ] Error handling comprehensive
- [ ] Logging adequate
- [ ] Monitoring in place

---

## 📝 Notes

### Risiko & Mitigasi:
1. **RPC Rate Limits** - Gunakan multiple RPC endpoints
2. **Transaction Failures** - Implement retry logic
3. **Price Slippage** - Dynamic slippage adjustment
4. **Network Congestion** - Priority fees

### Optimizations:
1. Cache pool data
2. Batch RPC calls
3. Use WebSocket for real-time data
4. Parallel transaction processing

---

**Versi:** 1.0  
**Tarikh:** 4 Disember 2025  
**Status:** Rancangan Lengkap - Sedia untuk Implementasi
