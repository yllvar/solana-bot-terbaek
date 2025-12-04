# 🚀 Bot Solana Sniping - Versi Selamat

## ✅ Apa Yang Baharu?

Bot ini adalah **versi selamat** yang dibina dari awal untuk menggantikan kod asal yang mengandungi malware.

### 🛡️ Keselamatan Terjamin:
- ✅ **Tiada kod tersembunyi** - Semua kod terbuka dan boleh diaudit
- ✅ **Tiada pencurian data** - Private key hanya digunakan secara lokal
- ✅ **Tiada sambungan luar** - Hanya ke RPC Solana rasmi
- ✅ **Kod bersih** - Ditulis dari awal tanpa kod warisan berbahaya

---

## 📋 Ciri-ciri

### ✅ Sudah Dilaksanakan:
1. **Pengurusan Dompet** - Muat private key dengan selamat
2. **Semak Baki** - Papar baki SOL dan token
3. **Konfigurasi** - Tetapan boleh disesuaikan melalui JSON
4. **Analisis Keselamatan** - Detect rug pull dengan check:
   - Mint authority
   - Freeze authority
   - Kecairan pool
   - Pengedaran token
5. **Monitor Pool** - WebSocket untuk detect pool baharu
6. **CLI Interaktif** - Menu mudah digunakan

### 🔄 Dalam Pembangunan:
1. **Auto Buy** - Pembelian automatik apabila pool baharu dijumpai
2. **Take Profit** - Jual automatik pada peratus sasaran
3. **Stop Loss** - Hentikan kerugian pada tahap tertentu
4. **Swap Integration** - Integrasi penuh dengan Raydium
5. **Price Monitoring** - Pemantauan harga real-time

---

## 🚀 Cara Penggunaan

### 1. Pasang Kebergantungan

```bash
pip3 install -r requirements_safe.txt
```

### 2. Konfigurasi Bot

Edit `bot_config.json` untuk tetapan anda:

```json
{
  "bot_settings": {
    "buy_amount_sol": 0.1,          // Jumlah SOL untuk beli
    "take_profit_percentage": 100,   // Take profit pada 100% (2x)
    "stop_loss_percentage": 50,      // Stop loss pada -50%
    "slippage_bps": 500,             // Slippage 5%
    "check_rug_pull": true,          // Aktifkan check rug pull
    "min_liquidity_sol": 5           // Kecairan minimum 5 SOL
  }
}
```

### 3. Jalankan Bot

```bash
python3 safe_bot_cli.py
```

### 4. Masukkan Private Key

Bot akan meminta private key anda. **AMARAN**: Gunakan dompet ujian dahulu!

### 5. Pilih Opsyen

```
📋 MENU UTAMA
1. Mulakan Bot (Monitor & Snipe)
2. Lihat Konfigurasi
3. Ubah Tetapan
4. Semak Baki Dompet
5. Keluar
```

---

## ⚙️ Struktur Projek

```
safe_bot/
├── __init__.py          # Inisialisasi pakej
├── config.py            # Pengurusan konfigurasi
├── wallet.py            # Pengurusan dompet
├── monitor.py           # Monitor pool baharu
└── security.py          # Analisis keselamatan token

bot_config.json          # Fail konfigurasi
safe_bot_cli.py          # CLI utama
requirements_safe.txt    # Kebergantungan
```

---

## 🔒 Keselamatan

### Amalan Terbaik:
1. ✅ **Gunakan dompet ujian** untuk percubaan pertama
2. ✅ **Jangan guna dompet utama** yang ada banyak aset
3. ✅ **Mula dengan jumlah kecil** (0.1-0.5 SOL)
4. ✅ **Audit kod sendiri** - Semua kod terbuka
5. ✅ **Backup private key** di tempat selamat

### Fail Yang Dilindungi:
- `bot.log` - Fail log (dilindungi gitignore)
- Private key tidak disimpan dalam fail
- Tiada data dihantar ke pelayan luar

---

## 📊 Status Pembangunan

| Modul | Status | Keterangan |
|-------|--------|------------|
| Wallet Management | ✅ Siap | Muat key, semak baki |
| Configuration | ✅ Siap | JSON config dengan validation |
| Security Analyzer | ✅ Siap | Rug pull detection |
| Pool Monitor | 🔄 Asas | WebSocket subscription |
| Auto Buy | 🔄 Dalam Pembangunan | Swap integration diperlukan |
| Take Profit | 🔄 Dalam Pembangunan | Price monitoring diperlukan |
| Stop Loss | 🔄 Dalam Pembangunan | Price monitoring diperlukan |

**Legend:**
- ✅ Siap dan berfungsi
- 🔄 Dalam pembangunan
- ⏳ Dirancang

---

## 🎯 Roadmap

### Fasa 1: Asas (SIAP) ✅
- [x] Pengurusan dompet
- [x] Konfigurasi
- [x] CLI interaktif
- [x] Analisis keselamatan asas

### Fasa 2: Monitoring (DALAM PEMBANGUNAN) 🔄
- [x] WebSocket subscription
- [ ] Parse pool data
- [ ] Detect new pools
- [ ] Price monitoring

### Fasa 3: Trading (DIRANCANG) ⏳
- [ ] Raydium swap integration
- [ ] Auto buy logic
- [ ] Take profit execution
- [ ] Stop loss execution

### Fasa 4: Advanced (DIRANCANG) ⏳
- [ ] Multi-wallet support
- [ ] Webhook notifications
- [ ] Advanced rug pull detection
- [ ] Backtesting

---

## ⚠️ Penafian

**PENTING - SILA BACA:**

1. **Risiko Dagangan:**
   - Dagangan cryptocurrency melibatkan risiko tinggi
   - Anda mungkin kehilangan semua modal
   - Tiada jaminan keuntungan

2. **Tujuan Pendidikan:**
   - Bot ini untuk tujuan pendidikan
   - Bukan nasihat kewangan
   - Gunakan atas risiko sendiri

3. **Kod Dalam Pembangunan:**
   - Beberapa ciri masih dalam pembangunan
   - Mungkin ada bug atau error
   - Sentiasa uji dengan jumlah kecil

4. **Tidak Berkaitan:**
   - Tidak berkaitan dengan Solana Foundation
   - Tidak berkaitan dengan Raydium
   - Projek komuniti bebas

---

## 🆘 Sokongan

Jika anda menghadapi masalah:

1. Semak fail `bot.log` untuk error
2. Pastikan kebergantungan dipasang dengan betul
3. Semak konfigurasi dalam `bot_config.json`
4. Pastikan RPC endpoint berfungsi

---

## 📝 Changelog

### Versi 1.0.0 (2025-12-04)
- ✅ Versi pertama yang selamat
- ✅ Pengurusan dompet
- ✅ Konfigurasi JSON
- ✅ Analisis keselamatan asas
- ✅ CLI interaktif
- ✅ WebSocket monitoring (asas)

---

## 🙏 Terima Kasih

Terima kasih kerana menggunakan bot ini. Selamat berdagang dengan selamat! 🚀

**Ingat: Jangan laburkan lebih daripada yang anda sanggup rugi!**

---

**Versi:** 1.0.0  
**Tarikh:** 4 Disember 2025  
**Status:** Dalam Pembangunan Aktif  
**Lesen:** MIT (untuk kegunaan pendidikan)
