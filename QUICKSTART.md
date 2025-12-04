# Panduan Pantas - Solana Sniping Bot

## ✅ Status Repositori
- **Git Dimulakan**: ✓ Repositori baharu
- **Cawangan**: main
- **Commit**: 3 (sejarah bersih)
- **Fail Dijejaki**: 128 fail
- **Fail Python**: 60

## 📁 Struktur Projek

### Fail Utama
```
main.py                    # Titik permulaan - jalankan ini untuk mulakan bot
requirements.txt           # Kebergantungan untuk dipasang
CODEBASE_INDEX.md         # Dokumentasi lengkap kod
README.md                 # Dokumentasi projek (Bahasa Malaysia)
.gitignore                # Peraturan git ignore (melindungi data sensitif)
```

### Direktori Utama
```
/raydium/                 # Integrasi Raydium DEX (7 fail)
/utils/                   # Fungsi utiliti (15 fail)
/monitoring_price/        # Strategi pemantauan harga
/py_modules/              # Modul tambahan (96 item)
/data/                    # Data runtime (dilindungi gitignore)
```

## 🚀 Bermula

### 1. Pasang Python
Muat turun Python 3.13+ dari https://www.python.org/downloads/

**Untuk Windows:**
- ✓ Tandakan "Add python.exe to PATH"
- ✓ Tandakan "Use admin privileges when installing py.exe"

**Untuk Mac:**
```bash
brew install python@3.13
```

**Untuk Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.13 python3-pip
```

### 2. Pasang Kebergantungan

**Windows:**
```bash
cd C:\Users\NamaAnda\Desktop\solana-sniping-bot-main
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
cd ~/Desktop/solana-sniping-bot-main
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

### 3. Sediakan Dompet Anda
- Sediakan kunci peribadi (private key) dompet Solana anda dalam format Base58
- Bot akan meminta kunci ini semasa dijalankan pertama kali
- **JANGAN SESEKALI commit kunci peribadi anda ke git!**

### 4. Jalankan Bot

**Windows:**
```bash
python main.py
```

**Mac/Linux:**
```bash
python3 main.py
```

## 🔧 Konfigurasi

### Tetapan Bot
- **BALANCE**: Papar baki & keuntungan
- **BUY DELAY**: Saat selepas pelancaran (0 = serta-merta)
- **TAKE PROFIT**: Peratus keuntungan sasaran
- **SELL DELAY**: Saat sebelum menjual (0 = serta-merta)
- **CHECK RUG**: Aktifkan perlindungan rug pull (true/false)

## 📦 Kebergantungan
```
solders       # Solana SDK untuk Python
solana        # Klien Python Solana
base58        # Pengekodan/penyahkodan Base58
requests      # Perpustakaan HTTP
colorama      # Warna terminal
```

## 🔒 Nota Keselamatan

### Fail Yang Dilindungi (gitignore)
- `snip_token.txt` - Konfigurasi token
- `LOG` - Fail log
- `/data/` - Data runtime
- `__pycache__/` - Cache Python
- `.env` - Pembolehubah persekitaran
- Sebarang fail `.key` atau `.pem`

### Amalan Terbaik
1. Jangan kongsi kunci peribadi anda
2. Gunakan dompet khusus untuk dagangan bot
3. Mulakan dengan jumlah kecil untuk ujian
4. Pantau bot secara aktif semasa operasi
5. Pastikan kebergantungan sentiasa dikemas kini

## 🎯 Ciri-ciri

### Sniping Token
Laksanakan transaksi beli serta-merta apabila kecairan ditambah kepada token SPL.

### Ambil Keuntungan (Take Profit)
Jual token secara automatik pada peratus keuntungan yang telah ditetapkan.

### Beli/Jual X Kali
Laksanakan pesanan beli berulang untuk purata turun atau scale ke posisi.

### Pesanan Had Jual (Sell Limit Order)
Tetapkan token untuk dijual secara automatik pada harga yang telah ditentukan.

### Perlindungan Rug Pull
Semak skor risiko sebelum melaksanakan dagangan.

## 📊 Pemantauan

### Semak Baki
**Windows:**
```bash
python checkbalance.py
```

**Mac/Linux:**
```bash
python3 checkbalance.py
```

### Dapatkan Maklumat Dompet
**Windows:**
```bash
python getwallet.py
```

**Mac/Linux:**
```bash
python3 getwallet.py
```

## 🧪 Pengujian

Fail ujian terletak di `/utils/`:
- `test_async_client.py` - Ujian klien async
- `test_token_client.py` - Ujian klien token
- `test_transaction.py` - Ujian transaksi
- `test_spl_token_instructions.py` - Ujian arahan token SPL
- Dan banyak lagi...

## 📝 Arahan Git

### Lihat Status
```bash
git status
```

### Lihat Sejarah
```bash
git log --oneline
```

### Buat Cawangan Baharu
```bash
git checkout -b feature/nama-ciri-anda
```

### Stage Perubahan
```bash
git add .
```

### Commit Perubahan
```bash
git commit -m "Mesej commit anda"
```

### Lihat Perubahan
```bash
git diff
```

## 🔍 Navigasi Kod

Untuk maklumat terperinci tentang struktur kod, lihat:
- `CODEBASE_INDEX.md` - Dokumentasi projek lengkap
- `README.md` - README projek asal dalam Bahasa Malaysia

## ⚠️ Penafian

- Bot ini untuk tujuan pendidikan
- Dagangan cryptocurrency melibatkan risiko
- Tidak berkaitan dengan Solana Foundation atau Solana Labs
- Kod tidak diaudit - gunakan atas risiko sendiri
- Sentiasa uji dengan jumlah kecil dahulu

## 📞 Sokongan

Jika anda menghadapi masalah atau ada soalan:

1. Semak bahagian [FAQ di README.md](README.md#-soalan-lazim-faq) dahulu
2. Baca dokumentasi lengkap di `CODEBASE_INDEX.md`
3. Semak kod di direktori `/raydium/` dan `/utils/`

## 🎉 Anda Sudah Bersedia!

Repositori anda kini:
- ✅ Diindeks dan didokumentasikan
- ✅ Git dimulakan dengan sejarah bersih
- ✅ Dilindungi dengan .gitignore yang betul
- ✅ Bersedia untuk pembangunan

## 🚨 Penyelesaian Masalah Pantas

### Error: "python is not recognized"
**Windows:**
```bash
# Gunakan 'py' sebagai ganti 'python'
py main.py

# Atau tambah Python ke PATH secara manual
```

### Error: "pip is not recognized"
**Windows:**
```bash
python -m pip install -r requirements.txt
```

**Mac/Linux:**
```bash
pip3 install -r requirements.txt
```

### Error: "Microsoft Visual C++ required" (Windows)
- Muat turun dan pasang [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Pilih "Desktop development with C++" semasa pemasangan

### Bot tidak membeli/menjual
1. Semak sambungan internet anda
2. Pastikan anda ada baki SOL yang mencukupi
3. Semak konfigurasi BUY DELAY dan SELL DELAY
4. Pastikan CHECK RUG tidak menyekat transaksi

### Cara hentikan bot
Tekan `Ctrl + C` di terminal/command prompt

## 💡 Tips Berguna

### Untuk Pengguna Windows
- Buka folder projek dalam File Explorer
- Taip `cmd` di address bar
- Tekan Enter untuk buka Command Prompt terus di folder tersebut

### Untuk Pengguna Mac
- Buka Terminal
- Seret folder projek ke Terminal untuk dapatkan path
- Atau gunakan `cd` untuk navigasi

### Untuk Semua Pengguna
- Gunakan virtual environment untuk keselamatan lebih:
  ```bash
  python -m venv venv
  # Windows: venv\Scripts\activate
  # Mac/Linux: source venv/bin/activate
  ```

## 📚 Sumber Tambahan

- [Dokumentasi Python](https://docs.python.org/)
- [Dokumentasi Solana](https://docs.solana.com/)
- [Raydium Docs](https://docs.raydium.io/)
- [Git Basics](https://git-scm.com/doc)

---

<p align="center">
  <strong>Selamat berdagang! 🚀</strong><br>
  <em>Ingat: Jangan laburkan lebih daripada yang anda sanggup rugi!</em>
</p>

---

**Versi:** 1.0.0  
**Kemaskini Terakhir:** 4 Disember 2025  
**Hash Repositori:** 3a15e84  
**Bahasa:** Bahasa Malaysia
