# 🤖 Solana Trading Bot - Sniper Bot Pintar

[![GitHub Repo](https://img.shields.io/badge/GitHub-yllvar/solana--bot--terbaek-blue?style=for-the-badge&logo=github)](https://github.com/yllvar/solana--bot-terbaek)
[![Python](https://img.shields.io/badge/Python-3.12+-green?style=for-the-badge&logo=python)](https://python.org)
[![Solana](https://img.shields.io/badge/Solana-Blockchain-purple?style=for-the-badge&logo=solana)](https://solana.com)

> **Bot perdagangan Solana automatik dengan teknologi AI untuk mengesan dan membeli token baharu pada DEX Raydium dengan cepat dan selamat.**

## 📋 Kandungan

- [🤖 Solana Trading Bot - Sniper Bot Pintar](#-solana-trading-bot---sniper-bot-pintar)
  - [📋 Kandungan](#-kandungan)
  - [✨ Ciri-ciri Utama](#-ciri-ciri-utama)
  - [🎯 Bagaimana Bot Berfungsi](#-bagaimana-bot-berfungsi)
  - [🛡️ Sistem Keselamatan](#️-sistem-keselamatan)
  - [📊 Analisis Data Pintar](#-analisis-data-pintar)
  - [⚙️ Konfigurasi](#️-konfigurasi)
  - [🚀 Pemasangan](#-pemasangan)
  - [📖 Cara Penggunaan](#-cara-penggunaan)
  - [🧪 Ujian](#-ujian)
  - [📈 Status Pembangunan](#-status-pembangunan)
  - [🤝 Sumbangan](#-sumbangan)
  - [📄 Lesen](#-lesen)
  - [⚠️ Penafian](#️-penafian)
- [🤖 Solana Trading Bot - Sniper Bot Pintar](#-solana-trading-bot---sniper-bot-pintar)
  - [📋 Kandungan](#-kandungan)
  - [✨ Ciri-ciri Utama](#-ciri-ciri-utama)
  - [🎯 Bagaimana Bot Berfungsi](#-bagaimana-bot-berfungsi)
  - [🛡️ Sistem Keselamatan](#️-sistem-keselamatan)
  - [📊 Analisis Data Pintar](#-analisis-data-pintar)
  - [⚙️ Konfigurasi](#️-konfigurasi)
  - [🚀 Pemasangan](#-pemasangan)
  - [📖 Cara Penggunaan](#-cara-penggunaan)
  - [🧪 Ujian](#-ujian)
  - [📈 Status Pembangunan](#-status-pembangunan)
  - [🤝 Sumbangan](#-sumbangan)
  - [📄 Lesen](#-lesen)
  - [⚠️ Penafian](#️-penafian)

## ✨ Ciri-ciri Utama

### 🎯 **Pengesanan Token Baharu**
- **Pemantauan masa nyata** transaksi Raydium menggunakan WebSocket
- **Pengesanan corak** untuk token baharu yang dilancarkan
- **Penapisan automatik** berdasarkan kriteria keselamatan
- **Respons pantas** - beli dalam beberapa saat selepas pelancaran

### 💰 **Analisis Volum Pintar**
- **Pengesahan pelbagai sumber** menggunakan Birdeye + DexScreener
- **Skor keyakinan** untuk ketepatan data
- **Purata wajaran** dari berbilang API
- **Pengesahan statistik** untuk konsistensi data

### 💧 **Analisis Kecairan Pool**
- **Pengiraan impak harga** sebelum berdagang
- **Had impak maksimum** (lalai: 5%)
- **Pengesahan kecairan** dari berbilang sumber
- **Sekatan dagangan** untuk pool dengan kecairan rendah

### 📈 **Pemantauan Volatiliti Harga**
- **Kiraan volatiliti** menggunakan data sejarah harga
- **Had perubahan harga** 24 jam (lalai: ±50%)
- **Analisis statistik** turun naik harga
- **Penapisan token** yang terlalu tidak stabil

### 🔒 **Sistem Keselamatan Berlapis**
- **Semakan bekalan token** (maksimum 1 bilion)
- **Analisis pemegang** (minimum 100 pemegang)
- **Semakan kuasa undi** (pemilikan tidak boleh direnounce)
- **Had kadar dagangan** (maksimum 5 dagangan per jam)

### 🎛️ **Konfigurasi Fleksibel**
- **Bendera ciri** boleh togol untuk setiap komponen
- **Had boleh laras** untuk semua parameter keselamatan
- **Keseimbangan risiko** boleh disesuaikan
- **Mod ujian** untuk pembangunan selamat

## 🎯 Bagaimana Bot Berfungsi

### 📡 **Aliran Kerja Utama**

```
1. 🔍 Pemantauan WebSocket → 2. 📊 Analisis Transaksi → 3. 🎯 Pengesanan Pool Baharu
      ↓                              ↓                              ↓
4. 💰 Pengesahan Volum → 5. 💧 Analisis Kecairan → 6. 📈 Semakan Volatiliti
      ↓                              ↓                              ↓
7. 🔒 Tapisan Keselamatan → 8. 💸 Pembelian Automatik → 9. 📊 Pengurusan Posisi
```

### 🔍 **Pemantauan Masa Nyata**
Bot menyambung ke WebSocket Solana dan memantau semua transaksi pada program Raydium CPMM. Ia menganalisis log transaksi untuk mengesan corak pelancaran token baharu.

### 🎯 **Pengesanan Token Pintar**
- **Corak Initialize** dalam log transaksi
- **Penapisan alamat** untuk menghilangkan program sistem
- **Pengesahan struktur pool** Raydium
- **Pengeluaran token** dari data transaksi

### 💰 **Pengesahan Volum Pelbagai Sumber**
```python
# Contoh pengesahan volum
volume_sources = [
    {'birdeye': 100000, 'confidence': 0.8},
    {'dexscreener': 95000, 'confidence': 0.7}
]
weighted_volume = (100000 * 0.8 + 95000 * 0.7) / (0.8 + 0.7)
confidence_score = calculate_consistency(volume_sources)
```

### 💧 **Analisis Kecairan Pool**
```python
# Kira impak harga
price_impact = (trade_amount_sol / pool_liquidity_usd) * 100
if price_impact > max_allowed_impact:
    skip_trade("Impak harga terlalu tinggi")
```

### 📈 **Pemantauan Volatiliti**
```python
# Kira volatiliti harga
returns = [abs(price[i] - price[i-1]) / price[i-1] for i in range(1, len(prices))]
volatility = stdev(returns) / mean(returns)
if volatility > max_volatility_threshold:
    skip_trade("Harga terlalu tidak stabil")
```

### 🔒 **Sistem Keselamatan**
Bot menjalankan berbilang semakan keselamatan sebelum membuat dagangan:
- ✅ Volum dagangan 24 jam minimum
- ✅ Kecairan pool mencukupi
- ✅ Volatiliti harga dalam had
- ✅ Bekalan token dalam julat selamat
- ✅ Bilangan pemegang minimum
- ✅ Pemilikan direnounce

## 🛡️ Sistem Keselamatan

### 🏗️ **Pertahanan Berlapis**
1. **Tahap Rangkaian**: Had kadar API dan backoff eksponen
2. **Tahap Data**: Pengesahan pelbagai sumber dan skor keyakinan
3. **Tahap Dagangan**: Had amaun, harga, dan frekuensi
4. **Tahap Portfolio**: Pengurusan risiko dan had kerugian

### ⚠️ **Pengesanan Risiko**
- **Token baru** dengan sejarah terhad
- **Volum palsu** dari manipulasi
- **Kecairan rendah** yang menyebabkan slippage tinggi
- **Volatiliti ekstrem** yang menunjukkan risiko

### 🔄 **Pengendalian Ralat**
- **Fallback automatik** untuk kegagalan API
- **Had masa tamat** untuk semua permintaan
- **Pengulangan pintar** dengan backoff
- **Pencatatan terperinci** untuk debug

## 📊 Analisis Data Pintar

### 🎯 **Sumber Data**
- **Birdeye API**: Data pasaran komprehensif dengan API key
- **DexScreener**: Data DEX percuma tanpa had
- **RPC Solana**: Data on-chain untuk pengesahan

### 📈 **Metrik Analisis**
- **Volum dagangan** dengan pengesahan konsistensi
- **Kecairan pool** dari berbilang sumber
- **Volatiliti harga** menggunakan statistik
- **Taburan pemegang** untuk analisis risiko
- **Sejarah harga** untuk corak pasaran

### 🤖 **Algoritma Pintar**
- **Purata wajaran** untuk gabungan data
- **Kiraan statistik** untuk pengesahan data
- **Analisis corak** untuk pengesanan manipulasi
- **Penilaian risiko** berasaskan berbilang faktor

## ⚙️ Konfigurasi

### 📄 **Fail Konfigurasi Utama**
```json
{
  "rpc_endpoint": "https://api.mainnet-beta.solana.com",
  "websocket_endpoint": "wss://api.mainnet-beta.solana.com",
  "raydium_program_id": "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",

  "api_keys": {
    "birdeye": "your_birdeye_api_key",
    "rugcheck": ""
  },

  "bot_settings": {
    "buy_amount_sol": 0.1,
    "take_profit_percentage": 30,
    "stop_loss_percentage": 15,
    "max_trades_per_hour": 5,
    "min_volume_24h": 5000
  },

  "advanced_features": {
    "multi_source_volume": true,
    "pool_liquidity_analysis": true,
    "price_volatility_filter": true
  },

  "validation_thresholds": {
    "min_volume_confidence": 0.3,
    "max_price_impact": 0.05,
    "max_volatility_threshold": 0.3
  },

  "token_filters": {
    "max_supply": 1000000000,
    "min_holders": 100,
    "contract_verified": true,
    "renounced_ownership": true
  }
}
```

### 🎛️ **Opsyen Konfigurasi Utama**

| Kategori | Tetapan | Penerangan | Lalai |
|----------|---------|------------|--------|
| **Dagangan** | `buy_amount_sol` | Amaun SOL untuk setiap belian | 0.1 |
| **Dagangan** | `max_trades_per_hour` | Had dagangan maksimum per jam | 5 |
| **Dagangan** | `min_volume_24h` | Volum minimum 24 jam ($) | 5000 |
| **Keselamatan** | `max_price_impact` | Impak harga maksimum (%) | 5.0 |
| **Keselamatan** | `max_volatility_threshold` | Had volatiliti maksimum | 0.3 |
| **Token** | `max_supply` | Bekalan maksimum token | 1B |
| **Token** | `min_holders` | Pemegang minimum | 100 |

## 🚀 Pemasangan

### � **Prasyarat**
- Python 3.12+
- Akaun Solana dengan SOL
- Kunci API Birdeye (pilihan, untuk data lanjutan)

### 📦 **Pemasangan Automatik**
```bash
# Klon repositori
git clone https://github.com/yllvar/solana-bot-terbaek.git
cd solana-bot-terbaek

# Pasang dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Pasang dalam mod pembangunan
pip install -e .
```

### 🔧 **Persediaan Manual**
```bash
# Cipta environment Python
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Pasang dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### ⚙️ **Konfigurasi Bot**
```bash
# Salin fail konfigurasi
cp config/bot_config.json config/my_config.json

# Edit konfigurasi mengikut keperluan
nano config/my_config.json

# Tetapkan kunci API Birdeye (jika ada)
# Tetapkan alamat wallet dan tetapan dagangan
```

## � Cara Penggunaan

### 🚀 **Menjalankan Bot**
```bash
# Mod interaktif (disyorkan untuk permulaan)
python main.py

# Atau gunakan CLI
solana-bot --config config/bot_config.json
```

### 📊 **Memantau Bot**
Bot akan memaparkan maklumat masa nyata:
```
🔍 Memulakan pemantauan pool baharu...
📡 Disambungkan ke WebSocket: wss://api.mainnet-beta.solana.com
🎯 Memantau Raydium Program: CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C

💓 Heartbeat #1 - Bot masih aktif dan memantau...
📊 Status: Aktif | Transaksi dilihat: 1,247
🎯 Pool dikesan: 3 | Pool dibeli: 1
```

### 🎛️ **Menu Interaktif**
Bot menyediakan menu interaktif untuk:
- ✅ Mulakan/Matikan pemantauan
- ✅ Lihat statistik masa nyata
- ✅ Kemaskini konfigurasi
- ✅ Semak baki wallet
- ✅ Lihat sejarah dagangan

### 🔐 **Keselamatan Wallet**
- **Kunci persendirian** diminta pada permulaan
- **Tidak disimpan** dalam fail atau database
- **Sahaja dalam memori** semasa sesi
- **Disahkan dengan RPC** sebelum dagangan

## 🧪 Ujian

### 🏃‍♂️ **Jalankan Ujian Penuh**
```bash
# Ujian unit sahaja
pytest tests/unit/ -v

# Ujian E2E sahaja
pytest tests/e2e/ -v

# Semua ujian
pytest tests/ -v

# Dengan laporan coverage
pytest tests/ --cov=src/solana_bot --cov-report=html
```

### 📊 **Coverage Ujian**
- ✅ **Unit Tests**: 98+ ujian untuk komponen individu
- ✅ **Integration Tests**: Ujian aliran dagangan lengkap
- ✅ **E2E Tests**: Ujian dari hujung ke hujung
- ✅ **Performance Tests**: Ujian kelajuan dan keteguhan

### � **Jenis Ujian**
- **Pengesanan Pool**: Validasi pengesanan token baharu
- **Analisis Keselamatan**: Semakan tapisan token
- **Dagangan Eksekusi**: Aliran belian automatik
- **Pengendalian Ralat**: Respons kepada kegagalan
- **Prestasi**: Skalabiliti dan kelajuan

## � Status Pembangunan

### ✅ **Fasa 1 - Lengkap (High Priority)**
- ✅ **Pengesahan Volum Pelbagai Sumber** - Birdeye + DexScreener
- ✅ **Analisis Kecairan Pool** - Impak harga dan had kecairan
- ✅ **Pemantauan Volatiliti Harga** - Had perubahan harga
- ✅ **Suite Ujian Komprehensif** - 98+ ujian automatik

### 🎯 **Fasa 2 - Dalam Perancangan (Medium Priority)**
- 🔄 **Pengesahan Umur Token** - Elak token baharu terlalu
- 🔄 **Analisis Pemegang Lanjutan** - Taburan pemegang sebenar
- 🔄 **Operasi API Batch** - Prestasi dipertingkatkan

### 🚀 **Fasa 3 - Masa Depan (Future)**
- 🤖 **AI untuk Ramalan** - Analisis corak pasaran
- 📊 **Arbitraj Cross-DEX** - Peluang arbitrage automatik
- 🎛️ **Pengurusan Portfolio** - Pengimbangan risiko

## 🤝 Sumbangan

### 💡 **Bagaimana Menyumbang**
1. **Fork** repositori
2. **Cipta branch ciri** (`git checkout -b feature/AmazingFeature`)
3. **Commit perubahan** (`git commit -m 'Add some AmazingFeature'`)
4. **Push ke branch** (`git push origin feature/AmazingFeature`)
5. **Buka Pull Request**

### 📝 **Garispanduan Sumbangan**
- Ikut **PEP 8** untuk gaya kod Python
- Tambah **ujian** untuk ciri baharu
- Kemas kini **dokumentasi** jika perlu
- Pastikan **semua ujian lulus** sebelum PR
- Gunakan **commit message yang bermakna**

### 🐛 **Melaporkan Bug**
- Gunakan **GitHub Issues** dengan template bug
- Sertakan **langkah untuk reproduce**
- Tambah **log ralat** dan **versi sistem**
- Nyatakan **perlakuan yang dijangka vs sebenar**

## 📄 Lesen

Projek ini menggunakan lesen **MIT**. Lihat fail [LICENSE](LICENSE) untuk butiran lengkap.

```
MIT License

Copyright (c) 2025 yllvar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## ⚠️ Penafian

**PENTING:** Bot ini adalah untuk tujuan pendidikan dan penyelidikan sahaja.

- ⚠️ **Risiko Kewangan**: Dagangan kripto melibatkan risiko tinggi
- ⚠️ **Tiada Jaminan**: Tiada jaminan keuntungan atau pulangan modal
- ⚠️ **Kepatuhan Undang-undang**: Pastikan mematuhi undang-undang tempatan
- ⚠️ **Tanggungjawab**: Gunakan atas risiko sendiri
- ⚠️ **Pendidikan**: Fahami sepenuhnya sebelum menggunakan

### 🚨 **Amaran Risiko**
- **Potensi Kerugian**: Boleh kehilangan semua modal
- **Volatiliti Pasaran**: Harga boleh berubah dengan cepat
- **Kegagalan Teknikal**: Sistem boleh gagal atau dimanipulasi
- **Risiko Keselamatan**: Kunci persendirian boleh dicuri

---

## 📞 Hubungi & Sokongan

- **GitHub Issues**: Untuk bug dan ciri baharu
- **Discussions**: Untuk soalan umum dan sokongan
- **Wiki**: Dokumentasi terperinci dan panduan

---

## 🙏 Penghargaan

Terima kasih kepada komuniti open-source dan penyumbang yang membuat projek ini mungkin:

- **Solana Labs** - Untuk blockchain Solana yang hebat
- **Raydium** - Untuk DEX yang inovatif
- **Birdeye** - Untuk API data pasaran
- **DexScreener** - Untuk data DEX percuma

---

**🔥 Dibangunkan dengan ❤️ untuk komuniti Solana**

**Sumber terbuka, selamat, dan boleh dipercayai untuk dagangan automatik!** 🚀✨

---

*Repositori: [https://github.com/yllvar/solana-bot-terbaek](https://github.com/yllvar/solana--bot-terbaek)*