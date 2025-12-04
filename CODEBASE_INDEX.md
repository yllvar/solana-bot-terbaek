# Indeks Kod - Solana Sniping Bot

## Gambaran Keseluruhan Projek
Bot dagangan automatik Solana yang direka untuk sniping token dan dagangan automatik di Raydium DEX. Bot ini menyediakan ciri seperti pembelian token segera semasa pelancaran, automasi ambil keuntungan, dan perlindungan rug-pull.

## Timbunan Teknologi
- **Bahasa**: Python 3.13+
- **Blockchain**: Solana
- **DEX**: Raydium
- **Perpustakaan Utama**: solders, solana, base58, requests, colorama

## Struktur Projek

### Direktori Akar
```
/Users/apple/solana-sniping-bot-main/
├── main.py                 # Titik masuk utama
├── requirements.txt        # Kebergantungan Python
├── README.md              # Dokumentasi projek (Bahasa Malaysia)
├── QUICKSTART.md          # Panduan pantas (Bahasa Malaysia)
├── CODEBASE_INDEX.md      # Fail ini - indeks kod lengkap
├── checkbalance.py        # Utiliti semakan baki SOL
├── getwallet.py           # Pengurusan dompet dari kunci peribadi
├── loadkey.py             # Utiliti pemuatan kunci
├── symbol.py              # Pengendalian simbol token
├── snip_token.txt         # Konfigurasi token (dilindungi gitignore)
├── LOG                    # Fail log (dilindungi gitignore)
└── .gitignore            # Peraturan git ignore
```

### Modul Teras

#### `/raydium/` - Integrasi Raydium DEX
Direktori ini mengandungi semua kod untuk berinteraksi dengan protokol Raydium.

- **Raydium.py** (2.9KB): Antara muka protokol Raydium teras
  - Fungsi untuk sambungan ke Raydium
  - Pengurusan pool dan AMM
  - Pengambilan maklumat pasaran

- **buy_swap.py** (5.3KB): Logik pembelian/swap token
  - Fungsi untuk membeli token SPL
  - Pengiraan slippage dan harga
  - Pengesahan transaksi pembelian

- **sell_swap.py** (5.1KB): Logik penjualan/swap token
  - Fungsi untuk menjual token SPL
  - Pengiraan harga jualan optimum
  - Pengesahan transaksi penjualan

- **async_txn.py** (3.2KB): Pengendalian transaksi asinkron
  - Pengurusan transaksi async/await
  - Pengendalian berbilang transaksi serentak
  - Retry logic untuk transaksi gagal

- **create_close_account.py** (10.3KB): Penciptaan dan penutupan akaun
  - Buat akaun token baharu
  - Tutup akaun yang tidak digunakan
  - Pengurusan akaun terkait (ATA - Associated Token Account)

- **layouts.py** (358B): Struktur data untuk Raydium
  - Layout data untuk AMM
  - Layout data untuk pool
  - Format data untuk transaksi

- **new_pool_address_identifier.py** (558B): Pengesanan alamat pool
  - Kenal pasti pool baharu
  - Dapatkan alamat pool dari token
  - Validasi pool

#### `/utils/` - Fungsi Utiliti
Direktori ini mengandungi fungsi pembantu dan utiliti.

- **__init__.py** (7B): Inisialisasi pakej
  
- **_core.py** (7.2KB): Fungsi utiliti teras
  - Fungsi pembantu umum
  - Pengendalian data
  - Konversi format

- **contract.py** (8.6KB): Interaksi kontrak pintar
  - Fungsi untuk panggil kontrak Solana
  - Pengurusan program ID
  - Pengesahan transaksi kontrak
  - **Fungsi `main()`** - titik masuk utama aplikasi

- **checkbalance.py** (447B): Utiliti semakan baki
  - Semak baki SOL
  - Semak baki token SPL
  - Format paparan baki

- **getwallet.py** (254B): Utiliti dompet
  - Muat dompet dari kunci peribadi Base58
  - Validasi kunci peribadi
  - Dapatkan alamat awam

- **layouts.py** (4.6KB): Struktur data
  - Layout untuk pelbagai jenis data
  - Format untuk parsing data blockchain
  - Struktur untuk transaksi

- **features.py** (317B): Bendera ciri dan konfigurasi
  - Tetapan ciri bot
  - Konfigurasi runtime
  - Feature flags

- **test_*.py**: Fail ujian untuk pelbagai komponen
  - `test_async_client.py` (2.1KB): Ujian klien async
  - `test_memo_program.py` (382B): Ujian program memo
  - `test_security_txt.py` (3.7KB): Validasi keselamatan
  - `test_spl_token_instructions.py` (13.8KB): Ujian arahan token SPL
  - `test_token_client.py` (15.7KB): Ujian klien token
  - `test_transaction.py` (16.1KB): Ujian transaksi
  - `test_vote_program.py` (3.3KB): Ujian program undian

#### `/monitoring_price/` - Pemantauan Harga
- **monitor_price_strategy.py**: Strategi pemantauan harga dan pelaksanaan
  - Pantau perubahan harga token
  - Laksanakan strategi dagangan berdasarkan harga
  - Trigger untuk take profit dan stop loss

#### `/py_modules/` - Modul Python Tambahan
Koleksi besar modul pemantauan dan integrasi (96 item):

- **beanstalk/**: Integrasi Beanstalk
- **bind_xml/**: Utiliti pengikatan XML
- **elasticsearch/**: Integrasi Elasticsearch
- **mongodb/**: Integrasi MongoDB
- **jenkins/**: Integrasi Jenkins
- **memcached_maxage/**: Utiliti Memcached
- **nginx/**: Pemantauan status Nginx
- **twemproxy/**: Pemantauan Twemproxy
- **unbound/**: Pemantauan Unbound DNS
- **usbrh/**: Pemantauan sensor USB
- **vmax/**: Pemantauan VMAX
- **xenstats/**: Statistik Xen
- Dan banyak lagi...

**Nota**: Modul-modul ini kebanyakannya adalah modul pemantauan legacy yang mungkin tidak digunakan secara aktif dalam bot. Mereka mungkin boleh dikeluarkan dalam pembersihan masa depan.

#### `/data/` - Penyimpanan Data
- Mengandungi data runtime dan konfigurasi (2 item)
- **Dilindungi oleh gitignore** - tidak akan di-commit ke repositori

#### `/.github/` - Konfigurasi GitHub
- GitHub Actions dan konfigurasi repositori (2 item)
- Workflow automasi
- Konfigurasi CI/CD

## Komponen Utama

### Aliran Aplikasi Utama
1. **Titik Masuk**: `main.py` mengimport dari `utils.contract` dan memanggil `main()`
2. **Persediaan Dompet**: Menggunakan `getwallet.py` untuk muat dompet dari kunci peribadi
3. **Semakan Baki**: Mengesahkan baki SOL melalui `checkbalance.py`
4. **Logik Dagangan**: Dilaksanakan melalui modul integrasi Raydium

### Struktur Data

#### SWAP_LAYOUT
Format arahan swap yang mentakrifkan:
```python
- instruction: Jenis arahan (Int8ul)
- amount_in: Jumlah input (Int64ul)
- min_amount_out: Jumlah output minimum (Int64ul)
```

#### AMM_INFO_LAYOUT_V4
Struktur maklumat pool AMM Raydium:
```python
- status: Status pool
- nonce: Nonce untuk keselamatan
- order_num: Nombor pesanan
- depth: Kedalaman pool
- base_decimal: Perpuluhan token asas
- quote_decimal: Perpuluhan token sebut harga
- state: Keadaan pool
- swap_fee_numerator: Pengangka yuran swap
- swap_fee_denominator: Penyebut yuran swap
- Dan banyak lagi...
```

#### MARKET_STATE_LAYOUT_V3
Struktur data keadaan pasaran untuk Serum/OpenBook.

#### POOL_INFO_LAYOUT
Layout maklumat pool untuk Raydium.

### Ciri-ciri Teras

#### 1. Sniping Token
- **Fungsi**: Beli serta-merta apabila kecairan ditambah
- **Implementasi**: Pemantauan pool baharu melalui WebSocket
- **Konfigurasi**: BUY DELAY (0 = serta-merta)

#### 2. Ambil Keuntungan (Take Profit)
- **Fungsi**: Jual automatik pada peratus keuntungan sasaran
- **Implementasi**: Pemantauan harga berterusan
- **Konfigurasi**: TAKE PROFIT (peratus)

#### 3. Beli/Jual Berbilang Kali
- **Fungsi**: Pesanan berulang untuk strategi DCA
- **Implementasi**: Loop pembelian/penjualan
- **Konfigurasi**: Bilangan kali dan selang masa

#### 4. Pesanan Had Jual
- **Fungsi**: Jual pada harga yang telah ditentukan
- **Implementasi**: Pemantauan harga dengan trigger
- **Konfigurasi**: Harga sasaran

#### 5. Perlindungan Rug Pull
- **Fungsi**: Semak skor risiko sebelum beli
- **Implementasi**: Analisis kontrak dan kecairan
- **Konfigurasi**: CHECK RUG (true/false)

### Parameter Konfigurasi

#### BALANCE
- **Tujuan**: Papar baki dan keuntungan
- **Jenis**: Display/Query
- **Penggunaan**: Semakan status kewangan

#### BUY DELAY
- **Tujuan**: Kelewatan selepas pelancaran token
- **Jenis**: Integer (saat)
- **Nilai**: 
  - `0` = Beli serta-merta
  - `>0` = Tunggu X saat
- **Cadangan**: 0 untuk sniping agresif

#### TAKE PROFIT
- **Tujuan**: Peratus keuntungan sasaran
- **Jenis**: Integer/Float (peratus)
- **Nilai**: 
  - `50` = Jual pada 50% untung
  - `100` = Jual pada 100% untung (2x)
  - `200` = Jual pada 200% untung (3x)
- **Cadangan**: 50-100% untuk realistik

#### SELL DELAY
- **Tujuan**: Kelewatan sebelum menjual
- **Jenis**: Integer (saat)
- **Nilai**:
  - `0` = Jual serta-merta selepas beli
  - `>0` = Tunggu X saat
- **Cadangan**: 0 untuk take profit automatik

#### CHECK RUG
- **Tujuan**: Aktifkan pemeriksaan risiko
- **Jenis**: Boolean
- **Nilai**:
  - `true` = Semak risiko (DISARANKAN)
  - `false` = Tidak semak (BERISIKO)
- **Cadangan**: Sentiasa `true`

## Integrasi WebSocket

Bot menggunakan WebSocket untuk kemas kini masa nyata:

### Fungsi WebSocket Utama

#### `__init__(self, *args, **kwargs)`
Inisialisasi klien WebSocket dengan:
- `subscriptions`: Dict untuk langganan aktif
- `sent_subscriptions`: Dict untuk langganan yang dihantar
- `failed_subscriptions`: Dict untuk langganan gagal
- `request_counter`: Counter untuk ID permintaan

#### `increment_counter_and_get_id()`
Dapatkan ID unik untuk setiap permintaan WebSocket.

#### `send_data(message)`
Hantar data melalui WebSocket:
- Sokongan untuk mesej tunggal atau berbilang
- Tracking langganan yang dihantar
- Format JSON automatik

#### `account_subscribe(pubkey, commitment, encoding)`
Langgan kemas kini akaun:
- Pantau perubahan baki
- Pantau perubahan keadaan akaun
- Konfigurasi commitment dan encoding

#### `account_unsubscribe(subscription)`
Batal langganan akaun:
- Hentikan pemantauan
- Bersihkan sumber
- Keluarkan dari dict langganan

### Kegunaan WebSocket
- Pemantauan pool baharu secara real-time
- Tracking status transaksi
- Kemas kini harga token
- Notifikasi perubahan kecairan

## Pengurusan Nod RPC

Bot mempunyai sistem pengurusan nod RPC yang canggih:

### `get_all_rpc_ips()`
Dapatkan senarai nod RPC yang tersedia:
- Query `getClusterNodes` dari RPC
- Tapis mengikut versi (jika ditetapkan)
- Sokongan untuk RPC awam dan peribadi
- Blacklist IP untuk nod bermasalah
- Keluarkan duplikat

### Pembolehubah Global
- `DISCARDED_BY_VERSION`: Kiraan nod ditolak kerana versi
- `DISCARDED_BY_TIMEOUT`: Kiraan nod ditolak kerana timeout
- `DISCARDED_BY_UNKNW_ERR`: Kiraan nod ditolak kerana error lain

### Konfigurasi RPC
- `RPC`: URL RPC utama
- `SPECIFIC_VERSION`: Versi nod yang dikehendaki (opsional)
- `WITH_PRIVATE_RPC`: Aktifkan sokongan RPC peribadi
- `IP_BLACKLIST`: Senarai IP untuk dielakkan

### `do_request(url, method, data, timeout, headers)`
Fungsi utiliti untuk permintaan HTTP:
- Sokongan GET, POST, HEAD
- Pengendalian timeout
- Pengendalian error dengan tracking
- Header boleh dikonfigurasi

### `get_current_slot()`
Dapatkan slot semasa blockchain:
- Query `getSlot` dari RPC
- Pengendalian error
- Retry logic

## Pengendalian Error

Bot mempunyai sistem pengendalian error yang komprehensif:

### Jenis Error
1. **Timeout Errors**: `ReadTimeout`, `ConnectTimeout`, `Timeout`
2. **Connection Errors**: `ConnectionError`, `HTTPError`
3. **Unknown Errors**: Error yang tidak dijangka

### Tracking Error
- Counter global untuk setiap jenis error
- Logging untuk debugging
- Graceful degradation

### Strategi Recovery
- Retry automatik untuk transaksi gagal
- Failover ke nod RPC lain
- Notifikasi pengguna untuk error kritikal

## Kebergantungan

### Perpustakaan Utama

#### solders
- **Tujuan**: Solana SDK untuk Python
- **Kegunaan**: Interaksi dengan blockchain Solana
- **Fungsi**: Transaksi, kunci, tandatangan

#### solana
- **Tujuan**: Klien Python Solana
- **Kegunaan**: RPC calls, WebSocket
- **Fungsi**: Query blockchain, hantar transaksi

#### base58
- **Tujuan**: Pengekodan Base58
- **Kegunaan**: Format kunci dan alamat
- **Fungsi**: Encode/decode

#### requests
- **Tujuan**: Perpustakaan HTTP
- **Kegunaan**: Permintaan RPC
- **Fungsi**: GET, POST, pengendalian response

#### colorama
- **Tujuan**: Warna terminal
- **Kegunaan**: Output berwarna di CLI
- **Fungsi**: Meningkatkan pengalaman pengguna

### Perpustakaan Tambahan (dari py_modules)
- **construct**: Parsing struktur data binari
- Pelbagai perpustakaan pemantauan (legacy)

## Pertimbangan Keselamatan

### Perlindungan Data Sensitif
- Kunci peribadi disimpan dalam persekitaran/config (dilindungi gitignore)
- Alamat dompet hanya didedahkan bila perlu
- Tandatangan transaksi dikendalikan dengan selamat
- Validasi endpoint RPC

### Fail Dilindungi (.gitignore)
```
# Kunci peribadi dan data sensitif
*.key
*.pem
private_key.txt
wallet.json
snip_token.txt

# Data runtime
data/
*.db
*.sqlite
LOG

# Cache dan build
__pycache__/
*.pyc
build/
dist/

# Persekitaran
.env
.env.local
venv/
```

### Amalan Keselamatan Terbaik
1. Jangan sesekali commit kunci peribadi
2. Gunakan dompet berasingan untuk bot
3. Mula dengan jumlah kecil
4. Aktifkan CHECK RUG
5. Pantau bot secara aktif
6. Kemas kini kebergantungan secara berkala

## Nota Pembangunan

### Ciri Python
- Menggunakan Python 3.13+ features
- Pattern async/await untuk operasi serentak
- Perpustakaan Construct untuk struktur data binari
- Type hints untuk kejelasan kod

### Corak Reka Bentuk
- Pemisahan kebimbangan (separation of concerns)
- Modular architecture
- Pengendalian error yang kukuh
- Logging yang komprehensif

### Prestasi
- Operasi asinkron untuk kelajuan
- Connection pooling untuk RPC
- Caching untuk data yang kerap diakses
- Optimisasi untuk latency rendah

## Pengujian

### Fail Ujian di `/utils/`

#### test_async_client.py (2.1KB)
- Ujian untuk klien asinkron
- Ujian sambungan WebSocket
- Ujian langganan

#### test_memo_program.py (382B)
- Ujian program memo Solana
- Validasi format memo

#### test_security_txt.py (3.7KB)
- Ujian keselamatan
- Validasi konfigurasi
- Semakan kerentanan

#### test_spl_token_instructions.py (13.8KB)
- Ujian arahan token SPL
- Ujian transfer, mint, burn
- Validasi format arahan

#### test_token_client.py (15.7KB)
- Ujian klien token
- Ujian operasi token
- Ujian pengendalian error

#### test_transaction.py (16.1KB)
- Ujian pembinaan transaksi
- Ujian tandatangan
- Ujian penghantaran

#### test_vote_program.py (3.3KB)
- Ujian program undian
- Validasi vote account

### Menjalankan Ujian
```bash
# Jalankan semua ujian
python -m pytest utils/

# Jalankan ujian spesifik
python -m pytest utils/test_transaction.py

# Dengan output verbose
python -m pytest -v utils/
```

## Statistik Fail

### Ringkasan
- **Jumlah Fail Python**: 60+
- **Aplikasi Utama**: ~267 baris (main.py)
- **Utils Teras**: ~7KB (_core.py), ~8.6KB (contract.py)
- **Liputan Ujian**: 7 fail ujian
- **Jumlah Baris Kod**: ~50,000+ (termasuk py_modules)

### Saiz Fail Utama
```
main.py                    9.4 KB
utils/contract.py          8.6 KB
utils/_core.py             7.2 KB
raydium/create_close_account.py  10.3 KB
raydium/buy_swap.py        5.3 KB
raydium/sell_swap.py       5.1 KB
utils/test_transaction.py 16.1 KB
utils/test_token_client.py 15.7 KB
```

## Langkah Seterusnya untuk Pembangunan

### Keutamaan Tinggi
1. ✅ Semak dan kemas kini kebergantungan dalam requirements.txt
2. ✅ Implementasi logging error yang komprehensif
3. ✅ Tambah sokongan fail konfigurasi (.env)
4. 🔄 Tingkatkan liputan ujian
5. 🔄 Dokumentasi API endpoints dan kaedah RPC

### Keutamaan Sederhana
6. 🔄 Tambah pemantauan dan alerting
7. 🔄 Implementasi rate limiting untuk panggilan RPC
8. 🔄 Optimisasi prestasi untuk transaksi pantas
9. 🔄 Tambah sokongan untuk berbilang strategi dagangan
10. 🔄 Buat dashboard web untuk pemantauan

### Keutamaan Rendah
11. 📋 Bersihkan modul py_modules yang tidak digunakan
12. 📋 Refactor kod untuk maintainability lebih baik
13. 📋 Tambah sokongan untuk DEX lain (selain Raydium)
14. 📋 Implementasi backtesting untuk strategi
15. 📋 Buat dokumentasi API lengkap

### Penambahbaikan Keselamatan
- Implementasi enkripsi untuk kunci peribadi
- Tambah 2FA untuk operasi kritikal
- Audit keselamatan kod
- Penetration testing
- Implementasi rate limiting untuk elakkan abuse

## Repositori Git

### Status Semasa
- **Status**: Dimulakan dengan bersih
- **Cawangan**: main (default)
- **Remote**: Tidak dikonfigurasi
- **Fail Diabaikan**: Kunci peribadi, log, data, fail cache

### Sejarah Commit
```
3a15e84 (HEAD -> main) docs: Kemas kini README.md dalam Bahasa Malaysia
e8367eb docs: Add quick start guide for easy onboarding
6579538 Initial commit: Solana Sniping Bot - Fresh start
```

### Arahan Git Berguna
```bash
# Lihat status
git status

# Lihat perubahan
git diff

# Tambah fail
git add <file>

# Commit
git commit -m "mesej"

# Lihat sejarah
git log --oneline

# Buat cawangan
git checkout -b feature/nama-ciri

# Tukar cawangan
git checkout main

# Gabung cawangan
git merge feature/nama-ciri
```

## Glosari Istilah

### Blockchain & Solana
- **SPL Token**: Solana Program Library Token - standard token di Solana
- **AMM**: Automated Market Maker - protokol pertukaran automatik
- **DEX**: Decentralized Exchange - pertukaran terdesentralisasi
- **Liquidity Pool**: Pool kecairan untuk dagangan
- **Slippage**: Perbezaan antara harga jangkaan dan sebenar
- **RPC**: Remote Procedure Call - cara komunikasi dengan blockchain
- **Slot**: Unit masa di Solana blockchain

### Dagangan
- **Sniping**: Membeli token serta-merta semasa pelancaran
- **Take Profit**: Mengambil keuntungan pada harga sasaran
- **Stop Loss**: Hentikan kerugian pada harga tertentu
- **DCA**: Dollar Cost Averaging - strategi pembelian berulang
- **Rug Pull**: Penipuan di mana pembangun lari dengan dana

### Teknikal
- **WebSocket**: Protokol komunikasi dua hala real-time
- **Async/Await**: Corak pengaturcaraan asinkron
- **Base58**: Format pengekodan untuk alamat dan kunci
- **Private Key**: Kunci peribadi untuk kawalan dompet
- **Public Key**: Alamat awam dompet

## Sokongan & Sumber

### Dokumentasi
- `README.md` - Panduan pengguna lengkap (Bahasa Malaysia)
- `QUICKSTART.md` - Panduan pantas (Bahasa Malaysia)
- `CODEBASE_INDEX.md` - Fail ini - dokumentasi kod

### Sumber Luaran
- [Dokumentasi Solana](https://docs.solana.com/)
- [Dokumentasi Raydium](https://docs.raydium.io/)
- [Dokumentasi Python](https://docs.python.org/)
- [Solana Cookbook](https://solanacookbook.com/)

### Komuniti
- Solana Discord
- Raydium Telegram
- GitHub Issues (untuk bug reports)

---

<p align="center">
  <strong>Dokumentasi Kod Lengkap</strong><br>
  <em>Untuk pembangun dan penyumbang</em>
</p>

---

**Versi Indeks:** 2.0.0  
**Kemaskini Terakhir:** 4 Disember 2025  
**Bahasa:** Bahasa Malaysia  
**Penyelenggara:** Komuniti Solana Bot
