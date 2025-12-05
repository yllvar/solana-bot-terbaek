# 🚀 SOLANA SNIPER BOT TERBAEK

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Solana-Blockchain-purple.svg" alt="Solana">
  <img src="https://img.shields.io/badge/Raydium-DEX-green.svg" alt="Raydium">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <strong>Advanced automated trading bot for Raydium DEX on Solana blockchain</strong><br>
  Snipe new tokens instantly, auto-take profit, and protect yourself from rug-pulls with enhanced security!
</p>

---

## 🆕 What's New - Enhanced Monitoring System

This bot features a **completely rewritten** pool detection and security analysis system:

### ✨ Enhanced Pool Detection
- **Proper `initialize2` instruction parsing** - No more false positives from naive keyword matching
- **Structured `ray_log` decoding** - Accurate extraction of pool addresses, token mints, and vaults
- **Multi-version support** - Works with Raydium V4 pools and handles layout variations

### 🔒 Advanced Security Analysis
- **Real on-chain SPL Token parsing** - Actual mint/freeze authority verification (not placeholders!)
- **RugCheck API integration** - Risk scoring, LP lock status, top holder analysis
- **Automated safety checks** - Configurable thresholds before auto-buy

### ⚡ MEV Protection Ready
- **Jito bundle support** - Atomic transaction execution
- **Priority tips** - Configurable tip amounts for faster inclusion
- **Bypass mempool** - Protect your transactions from front-running

---

## 📋 Table of Contents

* [Features](#-features)
* [Architecture](#-architecture)
* [Requirements](#-requirements)
* [Installation](#-installation)
* [Configuration](#-configuration)
* [Usage](#-usage)
* [Security](#-security)
* [FAQ](#-faq)
* [Disclaimer](#-disclaimer)

---

## ⭐ Features

### 🎯 Token Sniping
- Monitor Raydium for new pool initializations in real-time
- Proper `initialize2` instruction detection (not keyword matching)
- Buy tokens instantly when liquidity is added

### 💰 Auto Take Profit
- Set profit targets (e.g., 50%, 100%, 200%)
- Automatic selling when price reaches target
- Trailing stop-loss support

### 🛡️ Rug-Pull Protection
| Check | Description |
|-------|-------------|
| **Mint Authority** | Real on-chain parsing of SPL Token Mint account |
| **Freeze Authority** | Detects if issuer can freeze your tokens |
| **Liquidity** | Actual vault balance calculation |
| **RugCheck Score** | API integration for comprehensive analysis |
| **Top Holders** | Concentration analysis from RugCheck |

### 📊 Monitoring Statistics
- Transactions seen
- Pools detected
- Pools bought
- Pools skipped (security)

---

## 🏗️ Architecture

```
solana_bot/
├── monitor.py          # Enhanced pool monitor with proper detection
├── pool_parser.py      # 🆕 Raydium transaction parser (initialize2)
├── security.py         # Real security analysis (not placeholders!)
├── rugcheck_client.py  # 🆕 RugCheck API integration
├── jito_client.py      # 🆕 MEV protection with Jito bundles
├── price_tracker.py    # Real-time price monitoring
├── triggers.py         # Take profit / Stop loss logic
├── wallet.py           # Wallet management
├── config.py           # Bot configuration
├── transaction.py      # Transaction building
└── raydium/
    ├── swap.py         # Swap instruction builder
    └── layouts.py      # Raydium account layouts
```

---

## 💻 Requirements

### System Requirements
- **OS:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python:** 3.11 or higher
- **RAM:** Minimum 4GB
- **Internet:** Stable connection

### Dependencies
```
solana>=0.30.0
solders>=0.18.0
websockets>=12.0
aiohttp>=3.9.0
httpx>=0.25.0
construct>=2.10.0
base58>=2.1.1
```

### Optional API Keys
| Service | Purpose | Pricing |
|---------|---------|---------|
| **RugCheck** | Token security analysis | Free tier available |
| **Helius** | Geyser streaming (faster) | $49+/mo |

---

## 📥 Installation

### Quick Start

```bash
# Clone the repository
git clone git@github.com:yllvar/solana-bot-terbaek.git
cd solana-bot-terbaek

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_safe.txt

# Run the bot
python main.py
```

### Windows Installation

1. **Install Python 3.11+** from [python.org](https://www.python.org/downloads/)
   - ⚠️ Check "Add python.exe to PATH"
   
2. **Clone & Setup:**
   ```bash
   git clone git@github.com:yllvar/solana-bot-terbaek.git
   cd solana-bot-terbaek
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements_safe.txt
   ```

3. **Run:**
   ```bash
   python main.py
   ```

### Mac/Linux Installation

```bash
# Install Python (Mac)
brew install python@3.11

# Install Python (Ubuntu/Debian)
sudo apt update && sudo apt install python3.11 python3-pip

# Clone & Setup
git clone git@github.com:yllvar/solana-bot-terbaek.git
cd solana-bot-terbaek
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_safe.txt

# Run
python3 main.py
```

---

## ⚙️ Configuration

### Bot Configuration (`bot_config.json`)

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

### Security Configuration

```python
from solana_bot.security import SecurityAnalyzer

security = SecurityAnalyzer(
    rpc_client=client,
    rugcheck_api_key="your_api_key",  # Optional
    min_liquidity_sol=5.0,            # Minimum 5 SOL liquidity
    max_top_holder_pct=20.0,          # Max 20% for top holder
    max_risk_score=50                  # RugCheck threshold
)
```

### Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `buy_amount` | Amount in SOL to spend per buy | `0.1` |
| `buy_delay` | Seconds to wait after pool detection | `0` |
| `take_profit_percent` | Profit target to auto-sell | `100` |
| `stop_loss_percent` | Loss threshold to auto-sell | `50` |
| `slippage_bps` | Slippage tolerance (basis points) | `100` |
| `use_jito` | Enable Jito bundles for MEV protection | `false` |
| `min_liquidity_sol` | Minimum pool liquidity required | `5.0` |
| `max_risk_score` | Maximum RugCheck score to allow | `50` |

---

## 🎮 Usage

### Running the Bot

```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Run main bot
python main.py

# Or use CLI
python solana_bot_cli.py
```

### What You'll See

```
📝 Log file: bot_20251205_190000.log
🔍 Memulakan pemantauan pool baharu...
📡 Connecting to WebSocket: wss://api.mainnet-beta.solana.com
🎯 Monitoring Raydium Program: 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8
🔌 WebSocket connected successfully
✅ Berjaya subscribe ke Raydium program
👀 Menunggu transaksi baharu... (Bot sedang aktif)
💓 Heartbeat #1 - Bot masih aktif dan memantau...

🆕 Potential new pool detected! Extracting info...
✅ Pool parsed successfully via pool_parser
   Token: ABC123...
   Pool: XYZ789...
🔒 Running security checks for ABC123...
✅ Token passed security checks
🤖 Auto Buy enabled (Amount: 0.1 SOL)
✅ Auto Buy BERJAYA! TX: xxx...
```

### Check Balance

```bash
python checkbalance.py
```

### Stop the Bot

Press `Ctrl + C` to stop safely. You'll see final statistics:

```
📊 Monitoring Statistics:
   Transactions seen: 1523
   Pools detected: 12
   Pools bought: 8
   Pools skipped (security): 4
```

---

## 🔒 Security

### ⚠️ Important Warnings

1. **Private Key Safety:**
   - NEVER share your private key
   - Bot runs locally - keys are not sent anywhere
   - Use a dedicated wallet for the bot

2. **Use Separate Wallet:**
   - Create a new wallet specifically for trading
   - Only deposit what you can afford to lose
   - Start with small amounts (0.1 SOL)

3. **Security Checks:**
   - Always keep `CHECK RUG` enabled
   - Review RugCheck reports before manual trades
   - No security check is 100% foolproof

### 🔐 Protected Files

These files are in `.gitignore` and won't be pushed:
- `snip_token.txt` - Token configurations
- `LOG` - Log files
- `data/` - Runtime data
- `*.key`, `*.pem` - Private keys
- `.env` - Environment variables

---

## ❓ FAQ

### Q: Bot shows "python is not recognized"
**A:** Python not in PATH. Reinstall Python and check "Add to PATH".

### Q: Bot detects pool but doesn't buy
**A:** Check if security checks are failing. Review logs for warnings.

### Q: How do I get a RugCheck API key?
**A:** Sign up at [rugcheck.xyz](https://rugcheck.xyz) and generate a key from your dashboard.

### Q: What's the minimum SOL needed?
**A:** Minimum 0.1 SOL for testing, 1-2 SOL recommended for real trading.

### Q: Can I run multiple bots?
**A:** Yes, use different wallets and config files for each.

---

## ⚖️ Disclaimer

### 📢 Important - Please Read

1. **Not Financial Advice:**
   - This bot is an automation tool only
   - Not investment or financial advice
   - You are fully responsible for your trading decisions

2. **Trading Risks:**
   - Cryptocurrency trading involves high risk
   - You may lose all invested capital
   - Token prices can go to zero (rug-pull)
   - No guarantee of profits

3. **No Warranties:**
   - Bot provided "AS IS"
   - No guarantee it will work without errors
   - No guarantee of profits or performance
   - Developer not responsible for any losses

4. **Not Affiliated:**
   - NOT affiliated with Solana Foundation or Solana Labs
   - Community project, not for profit
   - Use at your own risk

5. **Unaudited Code:**
   - Code has not been audited by third parties
   - May contain bugs or security vulnerabilities
   - Always review code before using

6. **Legal Compliance:**
   - Ensure crypto trading is legal in your jurisdiction
   - Comply with all local laws and regulations
   - Pay applicable taxes

---

## 📞 Support

1. Check [FAQ](#-faq) first
2. Read `CODEBASE_INDEX.md` for detailed documentation
3. Check `QUICKSTART.md` for quick start guide
4. Review `LOGGING_GUIDE.md` for debugging

---

## 📄 License

This project is open-source software. Use responsibly.

---

<p align="center">
  <strong>⚠️ REMEMBER: Never invest more than you can afford to lose! ⚠️</strong><br>
  <em>Happy trading and good luck! 🚀</em>
</p>
