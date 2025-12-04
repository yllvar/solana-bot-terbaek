# 📝 Bot Logging Guide

## Log Files

Setiap kali bot dijalankan, fail log baharu akan dicipta dengan format:
```
bot_YYYYMMDD_HHMMSS.log
```

Contoh: `bot_20251204_225030.log`

## Log Levels

Bot menggunakan beberapa tahap logging:

- **INFO**: Maklumat penting (pool baharu, transaksi, status)
- **DEBUG**: Maklumat terperinci untuk debugging
- **WARNING**: Amaran (data tidak lengkap, ralat kecil)
- **ERROR**: Ralat kritikal

## Real-time Monitoring

### Console Output
Bot akan memaparkan log secara real-time di console semasa berjalan.

### Heartbeat Messages
Setiap 30 saat, bot akan memaparkan mesej heartbeat untuk menunjukkan ia masih aktif:
```
💓 Heartbeat #1 - Bot masih aktif dan memantau...
💓 Heartbeat #2 - Bot masih aktif dan memantau...
```

### Log File
Semua output juga disimpan ke fail log. Anda boleh membuka fail log dalam terminal lain untuk melihat real-time:

```bash
tail -f bot_*.log
```

## Typical Log Flow

Apabila bot berjalan dengan jayanya, anda akan melihat:

```
📝 Log file: bot_20251204_225030.log
🔍 Memulakan pemantauan pool baharu...
📡 Connecting to WebSocket: wss://api.mainnet-beta.solana.com
🎯 Monitoring Raydium Program: 675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8
🔌 WebSocket connected successfully
✅ Berjaya subscribe ke Raydium program
👀 Menunggu transaksi baharu... (Bot sedang aktif)
💡 Heartbeat akan dipaparkan setiap 30 saat untuk menunjukkan bot masih berjalan
💓 Heartbeat #1 - Bot masih aktif dan memantau...
```

## Debugging

Jika bot kelihatan "blank" atau tidak ada output:

1. **Semak fail log terkini:**
   ```bash
   ls -lt bot_*.log | head -1
   cat bot_YYYYMMDD_HHMMSS.log
   ```

2. **Enable DEBUG logging** (edit `solana_bot_cli.py`):
   ```python
   logging.basicConfig(
       level=logging.DEBUG,  # Tukar dari INFO ke DEBUG
       ...
   )
   ```

3. **Monitor real-time:**
   ```bash
   tail -f bot_*.log
   ```

## Common Log Messages

| Message | Meaning |
|---------|---------|
| `🔌 WebSocket connected successfully` | Bot berjaya sambung ke Solana |
| `✅ Berjaya subscribe` | Bot sedang mendengar transaksi |
| `💓 Heartbeat` | Bot masih aktif (setiap 30s) |
| `🆕 Potential new pool detected` | Pool baharu mungkin dijumpai |
| `✨ Pool baharu dijumpai!` | Pool baharu disahkan |
| `🤖 Auto Buy enabled` | Bot akan cuba membeli |
| `❌ Error` | Sesuatu tidak kena (semak details) |

## Troubleshooting

### Bot tidak memaparkan apa-apa
- Semak fail log untuk ralat
- Pastikan RPC endpoint berfungsi
- Cuba dengan `--debug` flag (jika ada)

### Terlalu banyak log
- Tukar `level=logging.INFO` ke `logging.WARNING`
- Matikan debug logging untuk libraries

### Log file terlalu besar
- Log files dicipta setiap run (tidak append)
- Boleh delete log lama secara manual
