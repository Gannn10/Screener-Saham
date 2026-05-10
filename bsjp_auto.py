"""
BSJP Auto Runner — khusus untuk GitHub Actions
Versi non-interactive, langsung scan + kirim Telegram
Jalankan: python bsjp_auto.py
"""

import os, sys, time, warnings
warnings.filterwarnings("ignore")

# Ambil token dari environment variable (GitHub Secrets)
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Kalau tidak ada di env, coba dari file config
if not TELEGRAM_TOKEN:
    TELEGRAM_TOKEN   = "8604469961:AAFk_K-EzJ6wiJp7oZoBQHVouwYmMOmEB1Y"
    TELEGRAM_CHAT_ID = "5465692885"

# Inject ke CONFIG sebelum import utama
import importlib, types

# ── Import fungsi dari screener utama ─────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import requests
    from datetime import datetime
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError as e:
    print(f"Library kurang: {e}")
    print("Jalankan: pip install yfinance pandas numpy colorama requests beautifulsoup4")
    sys.exit(1)

# Import screener v6
spec = importlib.util.spec_from_file_location(
    "screener",
    os.path.join(os.path.dirname(__file__), "bsjp_bot.py")
)
screener = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screener)

# Override token dari env
screener.CONFIG["TELEGRAM_TOKEN"]   = TELEGRAM_TOKEN
screener.CONFIG["TELEGRAM_CHAT_ID"] = TELEGRAM_CHAT_ID
screener.CONFIG["AUTO_MODE"]        = "normal"

def main():
    print(f"\n{'='*60}")
    print(f"  BSJP Auto Screener — GitHub Actions")
    print(f"  {datetime.now().strftime('%d %B %Y %H:%M WIB')}")
    print(f"{'='*60}\n")

    # Kirim notif mulai
    screener.telegram_kirim(
        f"🤖 <b>BSJP Auto-Scan dimulai</b>\n"
        f"{datetime.now().strftime('%d %b %Y %H:%M WIB')}\n"
        f"Scanning {len(screener.WATCHLIST)} saham IHSG...\n"
        f"<i>Hasil dikirim dalam ~3-5 menit</i>"
    )

    # Scan semua saham
    mode    = "normal"
    results = []
    errors  = 0
    total   = len(screener.WATCHLIST)

    print(f"  Scanning {total} saham mode {mode.upper()}...\n")

    # Fetch IDX broker/whale data sekali
    idx_cache = screener.ambil_idx_stock_summary()

    for idx, ticker in enumerate(screener.WATCHLIST):
        pct = int((idx+1) / total * 40)
        bar = "█" * pct + "░" * (40-pct)
        print(f"\r  [{bar}] {idx+1}/{total} {ticker:<8}", end="", flush=True)
        try:
            r = screener.analisis_saham(ticker, mode, idx_cache)
            if r:
                results.append(r)
        except Exception:
            errors += 1
        time.sleep(screener.CONFIG["REQUEST_DELAY"])

    print(f"\r  Scan selesai! {len(results)} lolos dari {total} ({errors} error){' '*20}\n")

    if not results:
        screener.telegram_kirim(
            f"⚠️ <b>BSJP Screener — {datetime.now().strftime('%d %b %Y')}</b>\n\n"
            f"Tidak ada saham lolos filter hari ini.\n"
            f"Mode: NORMAL — Coba besok atau longgarkan filter."
        )
        print("  Tidak ada hasil. Notif kosong terkirim.")
        return

    # Analisis sentimen top 5
    sentimen_cache = {}
    top5 = sorted(results, key=lambda x: x["score"], reverse=True)[:5]
    print("  Mengambil sentimen berita...")
    for r in top5:
        try:
            sentimen_cache[r["ticker"]] = screener.ambil_sentimen(r["ticker"])
            time.sleep(1.5)
        except Exception:
            pass

    # Tampilkan di log GitHub Actions
    screener.print_results(results, mode)
    screener.print_top3_dengan_sentimen(results, sentimen_cache)

    # Simpan CSV sebagai artifact
    screener.simpan_csv(results, mode)

    # Kirim ke Telegram
    screener.kirim_notif_telegram(results, mode, sentimen_cache)

    print(f"\n  {'='*50}")
    print(f"  Auto-scan selesai!")
    print(f"  {'='*50}\n")

if __name__ == "__main__":
    main()
