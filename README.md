# 🚀 SOLANA SNIPER BOT

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Solana-Blockchain-purple.svg" alt="Solana">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg" alt="Platform">
</p>

<p align="center">
  <strong>Bot dagangan automatik untuk Raydium DEX di rangkaian Solana</strong><br>
  Beli token baharu dengan pantas, ambil keuntungan secara automatik, dan lindungi diri daripada rug-pull!
</p>

---

## 📋 Kandungan

* [Pengenalan](#-pengenalan)
* [Ciri-ciri Utama](#-ciri-ciri-utama)
* [Keperluan Sistem](#-keperluan-sistem)
* [Pemasangan](#-pemasangan)
  * [Untuk Pengguna Windows](#untuk-pengguna-windows)
  * [Untuk Pengguna Mac/Linux](#untuk-pengguna-maclinux)
* [Cara Penggunaan](#-cara-penggunaan)
* [Konfigurasi Bot](#-konfigurasi-bot)
* [Keselamatan](#-keselamatan)
* [Soalan Lazim (FAQ)](#-soalan-lazim-faq)
* [Penafian](#-penafian)

---

## 🎯 Pengenalan

**Solana Sniper Bot** adalah alat dagangan automatik yang direka khas untuk ekosistem Solana. Bot ini menyelesaikan masalah utama yang dihadapi oleh pedagang kripto:

- ❌ **Terlepas peluang** membeli token baharu yang baru dilancarkan
- ❌ **Lambat mengambil keuntungan** dan akhirnya rugi akibat token dump
- ❌ **Terkena rug-pull** kerana tidak sempat menyemak risiko token

Bot ini membolehkan anda:
- ✅ Membeli token **serta-merta** sebaik sahaja kecairan ditambah
- ✅ Menjual secara **automatik** apabila mencapai sasaran keuntungan
- ✅ **Menyemak risiko** token sebelum membeli (perlindungan rug-pull)

**Tersedia untuk Windows PC, Mac, dan Linux.**

![Solana Bot Demo](https://github.com/user-attachments/assets/8b825c7d-1f6e-4178-a68c-af6c4dc4877d)

---

## ⭐ Ciri-ciri Utama

### 🎯 Token Sniping
Beli token SPL secara automatik sebaik sahaja kecairan ditambah ke pool Raydium. Jadilah antara pembeli terawal!

### 💰 Take Profit Automatik
Tetapkan sasaran keuntungan (contoh: 50%, 100%, 200%) dan bot akan menjual token secara automatik apabila harga mencapai sasaran.

### 🔄 Pembelian/Penjualan Berulang
Laksanakan pembelian berulang untuk strategi **average down** atau **scale in** ke posisi anda.

### 📊 Sell Limit Order
Tetapkan harga jualan yang dikehendaki, dan bot akan menjual token secara automatik apabila harga mencapai tahap tersebut.

### 🛡️ Perlindungan Rug-Pull
Bot akan menyemak skor risiko token sebelum membeli untuk melindungi anda daripada projek penipuan.

### 🖥️ Antaramuka Mesra Pengguna
Mudah digunakan dengan arahan yang jelas di terminal/command prompt.

---

## 💻 Keperluan Sistem

### Untuk Windows PC:
- **Sistem Operasi:** Windows 10/11 (64-bit)
- **Python:** Versi 3.13 atau lebih tinggi
- **RAM:** Minimum 4GB
- **Sambungan Internet:** Stabil dan laju
- **Dompet Solana:** Private key dalam format Base58

### Untuk Mac/Linux:
- **Sistem Operasi:** macOS 10.15+ atau Linux (Ubuntu 20.04+)
- **Python:** Versi 3.13 atau lebih tinggi
- **RAM:** Minimum 4GB
- **Sambungan Internet:** Stabil dan laju
- **Dompet Solana:** Private key dalam format Base58

---

## 📥 Pemasangan

### Untuk Pengguna Windows

#### Langkah 1: Muat Turun dan Pasang Python

1. Lawati laman web rasmi Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Muat turun **Python 3.13.7** atau versi terkini
3. Jalankan fail pemasangan (`.exe`)
4. **⚠️ SANGAT PENTING:** Semasa pemasangan, pastikan anda **TANDAKAN** kedua-dua pilihan ini:
   - ✅ **"Add python.exe to PATH"**
   - ✅ **"Use admin privileges when installing py.exe"**
5. Klik **"Install Now"** dan tunggu sehingga selesai

#### Langkah 2: Sahkan Pemasangan Python

1. Tekan kekunci **Windows + R**
2. Taip `cmd` dan tekan **Enter** untuk membuka Command Prompt
3. Taip arahan berikut dan tekan **Enter**:
   ```bash
   python --version
   ```
4. Anda sepatutnya melihat output seperti: `Python 3.13.7`

#### Langkah 3: Muat Turun Projek Bot

**Pilihan A: Menggunakan Git (Disarankan)**

1. Jika anda belum ada Git, muat turun dari: [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Buka **Command Prompt** (Windows + R, taip `cmd`)
3. Pergi ke folder di mana anda mahu simpan projek (contoh: Desktop):
   ```bash
   cd Desktop
   ```
4. Clone projek ini:
   ```bash
   git clone https://github.com/0xKronus/SOLANA_SNIPER_BOT.git
   ```
5. Masuk ke folder projek:
   ```bash
   cd SOLANA_SNIPER_BOT
   ```

**Pilihan B: Muat Turun ZIP**

1. Pergi ke halaman GitHub projek ini
2. Klik butang **"Code"** (hijau)
3. Pilih **"Download ZIP"**
4. Ekstrak fail ZIP ke lokasi yang anda mahu (contoh: Desktop)
5. Buka **Command Prompt**
6. Pergi ke folder projek:
   ```bash
   cd Desktop\SOLANA_SNIPER_BOT
   ```

**💡 Tip Windows:** Anda juga boleh buka folder projek dalam File Explorer, kemudian taip `cmd` di address bar dan tekan Enter untuk buka Command Prompt terus di folder tersebut!

#### Langkah 4: Kemas Kini pip

Dalam Command Prompt (pastikan anda berada di folder projek), jalankan:
```bash
python -m pip install --upgrade pip
```

#### Langkah 5: Pasang Keperluan Perpustakaan

Jalankan arahan berikut untuk memasang semua perpustakaan yang diperlukan:
```bash
pip install -r requirements.txt
```

Tunggu sehingga semua perpustakaan selesai dipasang. Anda akan melihat mesej seperti:
- `solders`
- `solana`
- `base58`
- `requests`
- `colorama`

#### Langkah 6: Jalankan Bot! 🎉

```bash
python main.py
```

Bot akan mula berjalan dan meminta anda memasukkan **private key** dompet Solana anda.

---

### Untuk Pengguna Mac/Linux

#### Langkah 1: Pasang Python

**Mac:**
```bash
# Menggunakan Homebrew (jika belum ada, pasang dari https://brew.sh)
brew install python@3.13
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.13 python3-pip
```

#### Langkah 2: Sahkan Pemasangan
```bash
python3 --version
```

#### Langkah 3: Clone Projek
```bash
cd ~/Desktop
git clone https://github.com/0xKronus/SOLANA_SNIPER_BOT.git
cd SOLANA_SNIPER_BOT
```

#### Langkah 4: Kemas Kini pip
```bash
python3 -m pip install --upgrade pip
```

#### Langkah 5: Pasang Keperluan
```bash
pip3 install -r requirements.txt
```

#### Langkah 6: Jalankan Bot
```bash
python3 main.py
```

---

## 🎮 Cara Penggunaan

### 1️⃣ Sediakan Dompet Solana Anda

Sebelum menggunakan bot, anda memerlukan:
- **Dompet Solana** (contoh: Phantom, Solflare)
- **Private Key** dompet dalam format Base58
- **SOL** dalam dompet untuk bayaran gas dan dagangan

⚠️ **AMARAN KESELAMATAN:**
- Jangan SESEKALI kongsi private key anda dengan sesiapa
- Gunakan dompet berasingan untuk bot (jangan guna dompet utama)
- Mula dengan jumlah kecil untuk ujian

### 2️⃣ Dapatkan Private Key Anda

**Dari Phantom Wallet:**
1. Buka Phantom wallet
2. Klik ikon tetapan (gear icon)
3. Pilih "Security & Privacy"
4. Pilih "Export Private Key"
5. Masukkan password anda
6. Salin private key (format Base58)

**Dari Solflare:**
1. Buka Solflare
2. Pergi ke Settings → Security
3. Klik "Export Private Key"
4. Salin private key

### 3️⃣ Jalankan Bot

1. Buka terminal/command prompt di folder projek
2. Jalankan: `python main.py` (Windows) atau `python3 main.py` (Mac/Linux)
3. Bot akan meminta private key anda:
   ```
   Please enter your private key: 
   ```
4. Tampal private key anda dan tekan **Enter**
5. Bot akan paparkan alamat dompet dan baki SOL anda
6. Ikut arahan di skrin untuk konfigurasi bot

### 4️⃣ Semak Baki

Untuk menyemak baki dompet anda:
```bash
python checkbalance.py
```

---

## ⚙️ Konfigurasi Bot

Apabila bot berjalan, anda boleh tetapkan parameter berikut:

### 💰 BALANCE
- **Fungsi:** Papar baki SOL dan keuntungan semasa
- **Cara guna:** Pilih opsyen "Check Balance" dalam menu

### ⏱️ BUY DELAY
- **Fungsi:** Masa kelewatan (dalam saat) selepas token dilancarkan sebelum bot membeli
- **Tetapan:**
  - `0` = Beli **serta-merta** sebaik token dilancarkan
  - `5` = Tunggu 5 saat selepas pelancaran
  - `10` = Tunggu 10 saat selepas pelancaran
- **Cadangan:** Tetapkan `0` untuk sniping agresif

### 🎯 TAKE PROFIT
- **Fungsi:** Peratus keuntungan sasaran untuk jualan automatik
- **Contoh:**
  - `50` = Jual apabila untung 50%
  - `100` = Jual apabila untung 100% (2x)
  - `200` = Jual apabila untung 200% (3x)
- **Cadangan:** Mulakan dengan 50-100% untuk keuntungan yang realistik

### ⏰ SELL DELAY
- **Fungsi:** Masa kelewatan (dalam saat) sebelum menjual token selepas dibeli
- **Tetapan:**
  - `0` = Jual **serta-merta** selepas beli (jika take profit tercapai)
  - `30` = Tunggu 30 saat sebelum jual
  - `60` = Tunggu 1 minit sebelum jual
- **Cadangan:** Tetapkan `0` untuk take profit automatik

### 🛡️ CHECK RUG
- **Fungsi:** Semak skor risiko token sebelum membeli (perlindungan rug-pull)
- **Tetapan:**
  - `true` = **Aktifkan** pemeriksaan risiko (DISARANKAN)
  - `false` = Matikan pemeriksaan risiko (BERISIKO!)
- **Cadangan:** Sentiasa tetapkan `true` untuk keselamatan

### 📊 Contoh Konfigurasi

**Untuk Sniping Agresif:**
```
BUY DELAY: 0
TAKE PROFIT: 100
SELL DELAY: 0
CHECK RUG: true
```

**Untuk Dagangan Konservatif:**
```
BUY DELAY: 5
TAKE PROFIT: 50
SELL DELAY: 30
CHECK RUG: true
```

---

## 🔒 Keselamatan

### ⚠️ Amaran Penting

1. **Private Key:**
   - JANGAN SESEKALI kongsi private key anda
   - Bot ini TIDAK menghantar private key ke mana-mana pelayan
   - Private key hanya digunakan secara lokal di komputer anda

2. **Gunakan Dompet Berasingan:**
   - Buat dompet baharu khusus untuk bot
   - Jangan guna dompet utama yang ada banyak aset
   - Hantar hanya jumlah yang anda sanggup rugi

3. **Mula Dengan Kecil:**
   - Uji bot dengan jumlah kecil dahulu (contoh: 0.1 SOL)
   - Fahami cara bot berfungsi sebelum guna jumlah besar
   - Pantau bot secara aktif semasa operasi awal

4. **Risiko Rug-Pull:**
   - Walaupun ada pemeriksaan risiko, tiada jaminan 100%
   - Sentiasa buat kajian sendiri (DYOR)
   - Jangan melabur lebih daripada yang anda sanggup rugi

5. **Fail Sensitif:**
   - Fail `snip_token.txt`, `LOG`, dan folder `data/` mengandungi maklumat sensitif
   - Fail-fail ini sudah dilindungi oleh `.gitignore`
   - Jangan kongsi fail-fail ini dengan sesiapa

### 🔐 Fail Yang Dilindungi

Fail berikut **TIDAK** akan disimpan dalam Git (selamat):
- `snip_token.txt` - Konfigurasi token
- `LOG` - Fail log
- `data/` - Data runtime
- `*.key`, `*.pem` - Kunci peribadi
- `.env` - Pembolehubah persekitaran

---

## ❓ Soalan Lazim (FAQ)

### Q1: Bot tidak dapat berjalan, muncul error "python is not recognized"
**A:** Ini bermakna Python tidak ditambah ke PATH semasa pemasangan.
- **Penyelesaian Windows:** Pasang semula Python dan pastikan tandakan "Add python.exe to PATH"
- **Atau:** Guna `py` sebagai ganti `python` (contoh: `py main.py`)

### Q2: Error "pip is not recognized" atau "pip: command not found"
**A:** pip tidak dijumpai dalam sistem.
- **Windows:** Guna `python -m pip` sebagai ganti `pip`
- **Mac/Linux:** Guna `pip3` sebagai ganti `pip`

### Q3: Error semasa install requirements "Microsoft Visual C++ required"
**A:** Untuk Windows, anda perlu pasang Microsoft Visual C++ Build Tools.
- Muat turun dari: [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Pilih "Desktop development with C++" semasa pemasangan

### Q4: Bot beli token tetapi tidak jual walaupun sudah untung
**A:** Semak tetapan TAKE PROFIT dan SELL DELAY anda.
- Pastikan TAKE PROFIT ditetapkan dengan betul
- Pastikan SELL DELAY tidak terlalu tinggi
- Semak sambungan internet anda

### Q5: Bagaimana cara hentikan bot?
**A:** Tekan `Ctrl + C` di terminal/command prompt untuk hentikan bot dengan selamat.

### Q6: Bolehkah saya guna bot ini di telefon?
**A:** Bot ini direka untuk PC/Mac/Linux. Untuk telefon, anda perlu gunakan aplikasi terminal seperti Termux (Android) tetapi tidak disarankan kerana prestasi terhad.

### Q7: Berapa banyak SOL yang diperlukan untuk mula?
**A:** Minimum 0.1 SOL untuk ujian, tetapi disarankan 1-2 SOL untuk dagangan sebenar (termasuk gas fees).

### Q8: Bot membeli token yang salah!
**A:** Pastikan anda tetapkan alamat token yang betul dalam konfigurasi. Sentiasa semak dua kali sebelum jalankan bot.

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

3. **Tiada Jaminan:**
   - Bot ini disediakan "SEBAGAIMANA ADANYA"
   - Tiada jaminan ia akan berfungsi tanpa ralat
   - Tiada jaminan keuntungan atau prestasi
   - Pembangun tidak bertanggungjawab atas sebarang kerugian

4. **Tidak Berkaitan Dengan Solana:**
   - Projek ini TIDAK berkaitan dengan Solana Foundation atau Solana Labs
   - Ini adalah projek komuniti bukan keuntungan
   - Gunakan atas risiko anda sendiri

5. **Kod Tidak Diaudit:**
   - Kod ini belum diaudit oleh pihak ketiga
   - Mungkin ada bug atau kelemahan keselamatan
   - Sentiasa semak kod sebelum guna

6. **Undang-undang Tempatan:**
   - Pastikan dagangan cryptocurrency adalah sah di negara anda
   - Patuhi semua undang-undang dan peraturan tempatan
   - Bayar cukai jika berkenaan

### 🎓 Tujuan Pendidikan

Bot ini dibuat untuk tujuan pendidikan dan pembelajaran. Gunakan dengan bijak dan bertanggungjawab.

---

## 📞 Sokongan & Komuniti

Jika anda menghadapi masalah atau ada soalan:

1. Semak bahagian [FAQ](#-soalan-lazim-faq) dahulu
2. Baca dokumentasi lengkap di `CODEBASE_INDEX.md`
3. Semak fail `QUICKSTART.md` untuk panduan pantas

---

## 📄 Lesen

Projek ini adalah perisian sumber terbuka. Gunakan dengan bertanggungjawab.

---

<p align="center">
  <strong>⚠️ INGAT: Jangan laburkan lebih daripada yang anda sanggup rugi! ⚠️</strong><br>
  <em>Selamat berdagang dan semoga beruntung! 🚀</em>
</p>

---

**Versi:** 1.0.0  
**Kemaskini Terakhir:** 4 Disember 2025  
**Bahasa:** Bahasa Malaysia