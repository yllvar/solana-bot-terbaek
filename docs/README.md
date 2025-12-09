# 🚀 SOLANA SNIPER BOT TERBAEK

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Solana-Blockchain-purple.svg" alt="Solana">
  <img src="https://img.shields.io/badge/Raydium-DEX-green.svg" alt="Raydium">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <strong>Bot dagangan automatik canggih untuk Raydium DEX di rangkaian Solana</strong><br>
  Beli token baharu dengan pantas, ambil keuntungan secara automatik, dan lindungi diri daripada rug-pull dengan keselamatan dipertingkat!
</p>

---

## 🆕 Apa Yang Baru - Sokongan CPMM & Pengesanan Pool Dipertingkat

Bot ini mempunyai sistem pengesanan pool dan analisis keselamatan yang **ditulis semula sepenuhnya** dengan **sokongan CPMM**:

### ✨ Pengesanan Pool Dipertingkat
- **Penghuraian arahan `initialize2` yang betul** - Tiada lagi positif palsu daripada padanan kata kunci naif
- **Penyahkodan `ray_log` berstruktur** - Pengekstrakan tepat alamat pool, token mint, dan vault
- **Sokongan pelbagai versi** - Berfungsi dengan pool Raydium V4 dan CPMM
- **🆕 Sokongan CPMM lengkap** - Pengesanan pool CPMM dengan penghuraian transaksi penuh

### 🔒 Analisis Keselamatan Lanjutan
- **Penghuraian SPL Token on-chain sebenar** - Pengesahan mint/freeze authority sebenar (bukan placeholder!)
- **Integrasi API RugCheck** - Penilaian risiko, status kunci LP, analisis pemegang teratas
- **Semakan keselamatan automatik** - Ambang boleh dikonfigurasi sebelum auto-buy

### ⚡ Sedia untuk Perlindungan MEV
- **Sokongan bundle Jito** - Pelaksanaan transaksi atomik
- **Tip keutamaan** - Amaun tip boleh dikonfigurasi untuk kemasukan lebih pantas
- **Bypass mempool** - Lindungi transaksi anda daripada front-running

---

## 📋 Kandungan

* [Ciri-ciri](#-ciri-ciri)
* [Seni Bina](#-seni-bina)
* [Keperluan](#-keperluan)
* [Pemasangan](#-pemasangan)
* [Konfigurasi](#-konfigurasi)
* [Penggunaan](#-penggunaan)
* [Keselamatan](#-keselamatan)
* [Soalan Lazim](#-soalan-lazim)
* [Penafian](#-penafian)

---

## ⭐ Ciri-ciri

### 🎯 Token Sniping
- Pantau Raydium untuk inisialisasi pool baharu secara masa nyata
- Pengesanan arahan `initialize2` yang betul (bukan padanan kata kunci)
- **🆕 Sokongan CPMM penuh** - Pengesanan pool CPMM dengan penghuraian transaksi JSON-RPC
- Beli token serta-merta apabila kecairan ditambah

### 🔄 Sokongan CPMM (Concentrated Liquidity)
- **Pengesanan Automatik** - Kenal pasti transaksi CPMM secara masa nyata
- **Penghuraian JSON-RPC** - Ambil data transaksi penuh tanpa pergantungan `solders.rpc.enums`
- **Pengekstrakan Tepat** - Dapatkan alamat pool, token mint, dan vault daripada arahan Initialize
- **Log Terperinci** - Jejaki proses penghuraian untuk debugging dan pengesahan

### 💰 Auto Take Profit
- Tetapkan sasaran keuntungan (contoh: 50%, 100%, 200%)
- Jualan automatik apabila harga mencapai sasaran
- Sokongan trailing stop-loss

### 🛡️ Perlindungan Rug-Pull
| Semakan | Penerangan |
|---------|------------|
| **Mint Authority** | Penghuraian on-chain sebenar akaun SPL Token Mint |
| **Freeze Authority** | Mengesan jika penerbit boleh membekukan token anda |
| **Kecairan** | Pengiraan baki vault sebenar |
| **Skor RugCheck** | Integrasi API untuk analisis menyeluruh |
| **Pemegang Teratas** | Analisis kepekatan daripada RugCheck |

### 📊 Statistik Pemantauan
- Transaksi dilihat
- Pool dikesan
- Pool dibeli
- Pool dilangkau (keselamatan)

---

## 🏗️ Seni Bina

```
solana_bot/
├── monitor.py          # Pemantau pool dipertingkat dengan pengesanan betul
├── pool_parser.py      # 🆕 Penghurai transaksi Raydium (V4 & CPMM)
├── security.py         # Analisis keselamatan sebenar (bukan placeholder!)
├── rugcheck_client.py  # 🆕 Integrasi API RugCheck
├── jito_client.py      # 🆕 Perlindungan MEV dengan bundle Jito
├── price_tracker.py    # Pemantauan harga masa nyata
├── triggers.py         # Logik Take profit / Stop loss
├── wallet.py           # Pengurusan dompet
├── config.py           # Konfigurasi bot
├── transaction.py      # Pembinaan transaksi
└── raydium/
    ├── swap.py         # Pembina arahan swap
    └── layouts.py      # Layout akaun Raydium

scripts/                # 🆕 Skrip utiliti
├── checkbalance.py     # Semak baki dompet
├── getwallet.py        # Jana dompet baharu
├── loadkey.py          # Muat kunci dompet
└── symbol.py           # Utiliti simbol

logs/                   # 🆕 Direktori log tersusun
├── bot_*.log          # Log bot utama
└── market_scanning_*.log # Log pemantauan pasaran

logs_archive/           # Arkib log lama
```

---

## 💻 Keperluan

### Keperluan Sistem
- **OS:** Windows 10/11, macOS 10.15+, atau Linux (Ubuntu 20.04+)
- **Python:** 3.11 atau lebih tinggi
- **RAM:** Minimum 4GB
- **Internet:** Sambungan stabil

### Kebergantungan
```
solana>=0.30.0
solders>=0.18.0
websockets>=12.0
aiohttp>=3.9.0
httpx>=0.25.0
construct>=2.10.0
base58>=2.1.1
requests>=2.31.0      # 🆕 Untuk penghuraian CPMM
```

### Kunci API Pilihan
| Perkhidmatan | Tujuan | Harga |
|--------------|--------|-------|
| **RugCheck** | Analisis keselamatan token | Tier percuma tersedia |
| **Helius** | Streaming Geyser (lebih pantas) | $49+/bulan |

---

## 📥 Pemasangan

### Mula Pantas

```bash
# Clone repositori
git clone git@github.com:yllvar/solana-bot-terbaek.git
cd solana-bot-terbaek

# Cipta virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Pasang kebergantungan
pip install -r requirements_safe.txt

# Jalankan bot
python main.py
```

### Pemasangan Windows

1. **Pasang Python 3.11+** dari [python.org](https://www.python.org/downloads/)
   - ⚠️ Tandakan "Add python.exe to PATH"
   
2. **Clone & Setup:**
   ```bash
   git clone git@github.com:yllvar/solana-bot-terbaek.git
   cd solana-bot-terbaek
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements_safe.txt
   ```

3. **Jalankan:**
   ```bash
   python main.py
   ```

### Pemasangan Mac/Linux

```bash
# Pasang Python (Mac)
brew install python@3.11

# Pasang Python (Ubuntu/Debian)
sudo apt update && sudo apt install python3.11 python3-pip

# Clone & Setup
git clone git@github.com:yllvar/solana-bot-terbaek.git
cd solana-bot-terbaek
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_safe.txt

# Jalankan
python3 main.py
```

---

## ⚙️ Konfigurasi

### Konfigurasi Bot (`bot_config.json`)

```json
{
  "rpc_endpoint": "https://api.mainnet-beta.solana.com",
  "ws_endpoint": "wss://api.mainnet-beta.solana.com",
  "buy_amount": 0.1,
  "buy_delay": 0,
  "take_profit_percent": 100,
  "stop_loss_percent": 50,
  "slippage_bps": 100,
  "use_jito": false,
  "jito_tip_lamports": 10000
}
```

### Konfigurasi Keselamatan

```python
from solana_bot.security import SecurityAnalyzer

security = SecurityAnalyzer(
    rpc_client=client,
    rugcheck_api_key="kunci_api_anda",  # Pilihan
    min_liquidity_sol=5.0,               # Minimum 5 SOL kecairan
    max_top_holder_pct=20.0,             # Max 20% untuk pemegang teratas
    max_risk_score=50                     # Ambang RugCheck
)
```

### Pilihan Konfigurasi

| Parameter | Penerangan | Lalai |
|-----------|------------|-------|
| `buy_amount` | Jumlah dalam SOL untuk dibeli | `0.1` |
| `buy_delay` | Saat menunggu selepas pengesanan pool | `0` |
| `take_profit_percent` | Sasaran keuntungan untuk auto-sell | `100` |
| `stop_loss_percent` | Ambang kerugian untuk auto-sell | `50` |
| `slippage_bps` | Toleransi slippage (basis points) | `100` |
| `use_jito` | Aktifkan bundle Jito untuk perlindungan MEV | `false` |
| `min_liquidity_sol` | Kecairan pool minimum diperlukan | `5.0` |
| `max_risk_score` | Skor RugCheck maksimum dibenarkan | `50` |

---

## 🎮 Penggunaan

### Menjalankan Bot

```bash
# Aktifkan virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Jalankan bot utama
python main.py

# Atau guna CLI
python solana_bot_cli.py
```

### Apa Yang Anda Akan Lihat

```
📝 Log file: logs/bot_20251205_190000.log
🔍 Memulakan pemantauan pool baharu...
📡 Connecting to WebSocket: wss://api.mainnet-beta.solana.com
🎯 Monitoring Raydium Program: 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8
🔌 WebSocket connected successfully
✅ Berjaya subscribe ke Raydium program
👀 Menunggu transaksi baharu... (Bot sedang aktif)
💓 Heartbeat #1 - Bot masih aktif dan memantau...

🆕 Potential new pool detected! Extracting info...
✅ Pool parsed successfully via pool_parser (V4/CPMM)
   Token: ABC123...
   Pool: XYZ789...
🔒 Running security checks for ABC123...
✅ Token passed security checks
🤖 Auto Buy enabled (Amount: 0.1 SOL)
✅ Auto Buy BERJAYA! TX: xxx...
```

### Semak Baki

```bash
python checkbalance.py
```

### Hentikan Bot

Tekan `Ctrl + C` untuk berhenti dengan selamat. Anda akan lihat statistik akhir:

```
📊 Monitoring Statistics:
   Transactions seen: 1523
   Pools detected: 12
   Pools bought: 8
   Pools skipped (security): 4
```

---

## 🔒 Keselamatan

### ⚠️ Amaran Penting

1. **Keselamatan Private Key:**
   - JANGAN SESEKALI kongsi private key anda
   - Bot berjalan secara lokal - kunci tidak dihantar ke mana-mana
   - Guna dompet khusus untuk bot

2. **Guna Dompet Berasingan:**
   - Cipta dompet baharu khusus untuk dagangan
   - Hanya deposit jumlah yang anda sanggup rugi
   - Mulakan dengan jumlah kecil (0.1 SOL)

3. **Semakan Keselamatan:**
   - Sentiasa aktifkan `CHECK RUG`
   - Semak laporan RugCheck sebelum dagangan manual
   - Tiada semakan keselamatan yang 100% pasti

### 🔐 Fail Dilindungi

Fail-fail ini ada dalam `.gitignore` dan tidak akan di-push:
- `snip_token.txt` - Konfigurasi token
- `LOG` - Fail log
- `data/` - Data runtime
- `*.key`, `*.pem` - Kunci peribadi
- `.env` - Pembolehubah persekitaran

---

## ❓ Soalan Lazim

### S: Bot menunjukkan "python is not recognized"
**J:** Python tiada dalam PATH. Pasang semula Python dan tandakan "Add to PATH".

### S: Bot mengesan pool tetapi tidak membeli
**J:** Semak jika semakan keselamatan gagal. Semak log untuk amaran.

### S: Bagaimana mendapatkan kunci API RugCheck?
**J:** Daftar di [rugcheck.xyz](https://rugcheck.xyz) dan jana kunci dari dashboard anda.

### S: Berapa minimum SOL diperlukan?
**J:** Minimum 0.1 SOL untuk ujian, 1-2 SOL disarankan untuk dagangan sebenar.

### S: Boleh jalankan pelbagai bot?
**J:** Ya, guna dompet dan fail konfigurasi berbeza untuk setiap satu.

---

## ⚖️ Penafian

### 📢 Penting - Sila Baca

1. **Bukan Nasihat Kewangan:**
   - Bot ini adalah alat automasi sahaja
   - Bukan nasihat pelaburan atau kewangan
   - Anda bertanggungjawab sepenuhnya atas keputusan dagangan anda

2. **Risiko Dagangan:**
   - Dagangan cryptocurrency melibatkan risiko tinggi
   - Anda mungkin kehilangan semua modal yang dilaburkan
   - Harga token boleh turun ke sifar (rug-pull)
   - Tiada jaminan keuntungan

3. **Tiada Waranti:**
   - Bot disediakan "SEBAGAIMANA ADANYA"
   - Tiada jaminan ia akan berfungsi tanpa ralat
   - Tiada jaminan keuntungan atau prestasi
   - Pembangun tidak bertanggungjawab atas sebarang kerugian

4. **Tidak Berkaitan:**
   - TIDAK berkaitan dengan Solana Foundation atau Solana Labs
   - Projek komuniti, bukan untuk keuntungan
   - Guna atas risiko anda sendiri

5. **Kod Tidak Diaudit:**
   - Kod belum diaudit oleh pihak ketiga
   - Mungkin ada bug atau kelemahan keselamatan
   - Sentiasa semak kod sebelum guna

6. **Pematuhan Undang-undang:**
   - Pastikan dagangan crypto adalah sah di negara anda
   - Patuhi semua undang-undang dan peraturan tempatan
   - Bayar cukai jika berkenaan

---

## 📞 Sokongan

1. Semak [Soalan Lazim](#-soalan-lazim) dahulu
2. Baca `CODEBASE_INDEX.md` untuk dokumentasi terperinci
3. Semak `QUICKSTART.md` untuk panduan mula pantas
4. Semak `LOGGING_GUIDE.md` untuk debugging

---

## 📄 Lesen

Projek ini adalah perisian sumber terbuka. Gunakan dengan bertanggungjawab.

---

---

## 🔧 Implementation Plan for Enhanced Trading Strategy

This section documents the current codebase review and the detailed implementation plan to achieve the specified trading bot requirements for automated risk management and token filtering.

### 📊 Current Implementation Summary

#### Core Components
- **PoolMonitor** (`monitor.py`): Real-time detection of new Raydium pools with enhanced CPMM support
- **TradeTriggers** (`triggers.py`): Basic take profit/stop loss execution with position tracking
- **PriceTracker** (`price_tracker.py`): Real-time price monitoring for open positions
- **SecurityAnalyzer** (`security.py`): Placeholder for token security analysis (needs enhancement)

#### Existing Features
- ✅ Auto-buy on new pool detection with configurable SOL amount
- ✅ Basic take profit (currently 100%) and stop loss (currently 50%) triggers
- ✅ Minimum liquidity checks (currently 5 SOL)
- ✅ Buy delay configuration
- ✅ Position tracking with entry price and time
- ✅ Enhanced pool detection with CPMM support
- ✅ Basic security placeholder (RugCheck integration)

#### Current Configuration (`bot_config.json`)
```json
{
  "bot_settings": {
    "buy_delay_seconds": 0,
    "buy_amount_sol": 0.1,
    "take_profit_percentage": 100,
    "stop_loss_percentage": 50,
    "slippage_bps": 500,
    "check_rug_pull": true,
    "max_buy_tax": 10,
    "max_sell_tax": 10,
    "min_liquidity_sol": 5
  }
}
```

### 🎯 Requirements Analysis

#### Trading Strategy Parameters (Target Configuration)
```json
{
  "take_profit_percentage": 30,
  "stop_loss_percentage": 15,
  "trailing_stop": 10,
  "max_trades_per_hour": 5,
  "min_liquidity_sol": 10,
  "min_volume_24h": 5000,
  "max_hold_time_hours": 4,
  "cooldown_after_sell": 60,
  "enable_trailing_stop": true
}
```

#### Token Filters (New Requirements)
```json
{
  "token_filters": {
    "max_supply": 1000000000,
    "min_holders": 100,
    "max_top_holder_percent": 20,
    "contract_verified": true,
    "renounced_ownership": true
  }
}
```

#### Gap Analysis
| Feature | Current Status | Implementation Required |
|---------|----------------|-------------------------|
| **Take Profit (30%)** | ✅ Configurable | Update default value |
| **Stop Loss (15%)** | ✅ Configurable | Update default value |
| **Trailing Stop (10%)** | ❌ Missing | New trigger logic |
| **Max Trades/Hour (5)** | ❌ Missing | Trade counter + rate limiting |
| **Min Volume 24h ($5000)** | ❌ Missing | Volume API integration |
| **Max Hold Time (4hr)** | ❌ Missing | Position timeout logic |
| **Cooldown After Sell (60s)** | ❌ Missing | Trade lockout mechanism |
| **Token Supply Filter** | ❌ Missing | On-chain supply validation |
| **Holder Distribution** | ❌ Missing | Holder analysis API |
| **Contract Verification** | ❌ Missing | Verification checks |
| **Ownership Status** | ❌ Missing | Renounce validation |

### 🛠️ Detailed Implementation Plan

#### Phase 1: Configuration Enhancement (2 hours)
**Objective**: Extend configuration to support all new parameters

**Files to Modify**:
- `bot_config.json`: Add new trading parameters and token filters
- `solana_bot/config.py`: Add new property methods for configuration access

**Implementation Steps**:
1. Update `bot_config.json` with new structure
2. Add property methods in `BotConfig` class:
   ```python
   @property
   def trailing_stop_percentage(self) -> float:
       return self.config['bot_settings']['trailing_stop_percentage']
   
   @property
   def max_trades_per_hour(self) -> int:
       return self.config['bot_settings']['max_trades_per_hour']
   
   @property
   def max_supply(self) -> int:
       return self.config['token_filters']['max_supply']
   ```

#### Phase 2: Trailing Stop Implementation (4 hours)
**Objective**: Add dynamic stop loss that trails profits

**Files to Modify**:
- `solana_bot/triggers.py`: Enhance `TradeTriggers` class

**Implementation Steps**:
1. Add `highest_price` tracking to position data
2. Modify `check_triggers` method:
   ```python
   # Update highest price
   if current_price > position['highest_price']:
       position['highest_price'] = current_price
   
   # Calculate trailing stop
   if config.enable_trailing_stop:
       trailing_stop_price = position['highest_price'] * (1 - config.trailing_stop_percentage/100)
       if current_price <= trailing_stop_price:
           await self.execute_sell(token_mint, "TRAILING_STOP", current_price)
   ```

#### Phase 3: Trade Rate Limiting (3 hours)
**Objective**: Implement max trades per hour and cooldown mechanisms

**Files to Modify**:
- `solana_bot/monitor.py`: Add trade counting and cooldown logic

**Implementation Steps**:
1. Add trade tracking variables to `PoolMonitor`:
   ```python
   self.trade_count = 0
   self.last_trade_reset = time.time()
   self.cooldowns = {}
   ```

2. Implement rate limiting in `execute_auto_buy`:
   ```python
   # Reset counter every hour
   if time.time() - self.last_trade_reset >= 3600:
       self.trade_count = 0
       self.last_trade_reset = time.time()
   
   # Check limits
   if self.trade_count >= config.max_trades_per_hour:
       logger.warning("Max trades per hour reached")
       return
   ```

#### Phase 4: Position Management Enhancements (4 hours)
**Objective**: Add max hold time and volume checks

**Files to Modify**:
- `solana_bot/triggers.py`: Add timeout and volume validation

**Implementation Steps**:
1. Add volume API integration (requires external API)
2. Add hold time check in `check_triggers`:
   ```python
   hold_hours = (time.time() - position['entry_time']) / 3600
   if hold_hours >= config.max_hold_time_hours:
       await self.execute_sell(token_mint, "MAX_HOLD_TIME", current_price)
   ```

3. Add volume check in `execute_auto_buy`:
   ```python
   volume = await dex_api.get_24h_volume(token_address)
   if volume < config.min_volume_24h:
       logger.warning(f"Volume too low: ${volume}")
       return
   ```

#### Phase 5: Token Security Filters (8 hours)
**Objective**: Implement comprehensive token validation

**Files to Modify**:
- `solana_bot/security.py`: Enhance `SecurityAnalyzer` class

**Implementation Steps**:
1. Add token metadata fetching
2. Implement supply validation:
   ```python
   async def check_supply(self, token_mint: str) -> bool:
       supply = await self.get_token_supply(token_mint)
       return supply <= self.config.max_supply
   ```

3. Add holder distribution analysis:
   ```python
   async def check_holders(self, token_mint: str) -> bool:
       holders = await self.get_holder_distribution(token_mint)
       return len(holders) >= self.config.min_holders and \
              holders[0]['percent'] <= self.config.max_top_holder_percent
   ```

4. Add contract verification checks

#### Phase 6: Integration & Testing (6 hours)
**Objective**: Connect all components and test functionality

**Implementation Steps**:
1. Update `SolanaSnipingBot` to use new security checks
2. Add comprehensive logging for new features
3. Create test scenarios for edge cases
4. Performance optimization and error handling

### 📈 Timeline & Milestones

| Phase | Duration | Status | Milestone |
|-------|----------|--------|-----------|
| **Configuration** | 2 hours | ✅ **COMPLETED** | Extended config structure |
| **Trailing Stop** | 4 hours | ✅ **COMPLETED** | Dynamic profit protection |
| **Rate Limiting** | 3 hours | ✅ **COMPLETED** | Trade frequency control |
| **Position Mgmt** | 4 hours | ✅ **COMPLETED** | Timeout and volume checks |
| **Security Filters** | 8 hours | ✅ **COMPLETED** | Token validation system |
| **Integration** | 6 hours | ✅ **COMPLETED** | Full system testing |
| **Total** | **27 hours** | **27/27 hours done** | **PRODUCTION READY!** |

### 🔍 Technical Considerations

#### API Dependencies
- **Volume Data**: Integration with DexScreener/Birdeye APIs for 24h volume
- **Holder Data**: On-chain holder analysis or external API
- **Contract Verification**: Solana program verification checks

#### Performance Impact
- Additional API calls may increase latency
- Holder analysis could be resource-intensive
- Need to implement caching for repeated checks

#### Risk Management
- Circuit breakers for API failures
- Fallback mechanisms for missing data
- Graceful degradation when checks fail

#### Security Enhancements
- Input validation for all new parameters
- Rate limiting for external API calls
- Error handling for failed validations

### 🎯 Success Criteria

1. **Functionality**: All specified parameters implemented and working
2. **Performance**: No significant impact on sniping speed (<100ms overhead)
3. **Reliability**: Robust error handling and fallback mechanisms
4. **Maintainability**: Clean code structure with proper documentation
5. **Safety**: Enhanced filtering prevents high-risk trades

### 📝 Next Steps

1. **Priority Implementation**: Start with configuration and trailing stop (high impact, low risk)
2. **Testing Strategy**: Implement unit tests for each new component
3. **Documentation**: Update README with new features and usage examples
4. **Monitoring**: Add metrics for trade filtering effectiveness

---

<p align="center">
  <strong>⚠️ INGAT: Jangan laburkan lebih daripada yang anda sanggup rugi! ⚠️</strong><br>
  <em>Selamat berdagang dan semoga beruntung! 🚀</em>
</p>
