"""
Script untuk melakukan backfill data historis BSJP.
Menyimpan simulasi hasil screener ke dalam screener_history.csv dengan tipe 'backfill'.
"""

import os
import sys
import time
import warnings
from datetime import datetime
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# Import module screener
import bsjp_bot as screener

# Coba import curl_cffi untuk request IDX (Whale Flow)
try:
    from curl_cffi import requests as cf_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    print("Warning: curl_cffi tidak ada, whale flow akan kosong")

# --- Konfigurasi Backfill ---
LOOKBACK_DAYS = 30
WATCHLIST = screener.WATCHLIST

# --- Fungsi untuk fetch IDX data historis (Try/Except Error Handling) ---
def fetch_idx_for_date(date_str):
    if not HAS_CURL_CFFI: return {}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-broker/",
        "Accept": "application/json",
    }
    url = "https://www.idx.co.id/primary/TradingSummary/GetStockSummary"
    
    try:
        params = {"date": date_str, "start": "0", "length": "2000"}
        r = cf_requests.get(
            url, headers=headers, params=params,
            timeout=20, impersonate="chrome"
        )
        if r.status_code != 200:
            return {}

        data = r.json()
        items = data.get("data", [])
        if not items: return {}

        cache = {}
        for item in items:
            code = item.get("StockCode", "").strip()
            if not code: continue
            fb = float(item.get("ForeignBuy", 0) or 0)
            fs = float(item.get("ForeignSell", 0) or 0)
            vol = float(item.get("Volume", 0) or 0)
            val = float(item.get("Value", 0) or 0)
            close = float(item.get("Close", 0) or 0)
            chg = float(item.get("Change", 0) or 0)

            net_foreign = fb - fs
            net_foreign_val = net_foreign * close if close > 0 else 0
            foreign_pct = ((fb + fs) / vol * 100) if vol > 0 else 0

            cache[code] = {
                "foreign_buy":      fb,
                "foreign_sell":     fs,
                "net_foreign":      net_foreign,
                "net_foreign_val":  net_foreign_val,
                "foreign_pct":      round(foreign_pct, 1),
                "volume":           vol,
                "value":            val,
                "close":            close,
                "change":           chg,
                "date":             date_str,
            }
        return cache
    except Exception as e:
        print(f"    [Error] Gagal fetch IDX {date_str}: {e}")
        return {}

def main():
    print(f"==================================================")
    print(f"[START] MEMULAI BACKFILL HISTORY BSJP ({LOOKBACK_DAYS} HARI) [START]")
    print(f"==================================================")
    
    # 1. Pre-fetch data YFinance untuk cache agar tidak perlu memanggil 30x
    print("\n1. Mengunduh data historis YFinance untuk cache...")
    history_cache = {}
    
    total_wl = len(WATCHLIST)
    for idx, t in enumerate(WATCHLIST):
        print(f"\r   Downloading {idx+1}/{total_wl}: {t}", end="")
        try:
            df = yf.Ticker(f"{t}.JK").history(period="6mo", auto_adjust=True)
            if df is not None and not df.empty and len(df) >= 35:
                history_cache[t] = df
        except Exception:
            pass
            
    print(f"\n   => Berhasil cache {len(history_cache)} saham dari total {total_wl}.")
    
    # 2. Cek kalender hari kerja bursa berdasarkan histori pergerakan IHSG
    print("\n2. Mengidentifikasi hari bursa aktif...")
    try:
        ihsg = yf.Ticker("^JKSE").history(period="3mo", auto_adjust=True)
        bursa_dates = [d.date() for d in ihsg.index]
        today_date = datetime.now().date()
        target_dates = [d for d in bursa_dates if d < today_date and (today_date - d).days <= LOOKBACK_DAYS]
    except Exception as e:
        print(f"Gagal baca kalender IHSG: {e}")
        return

    print(f"   => Ditemukan {len(target_dates)} hari bursa dalam {LOOKBACK_DAYS} hari terakhir.")
    
    # 3. Looping Backfill
    all_results = []
    
    for d in target_dates:
        date_str = d.strftime("%Y-%m-%d")
        idx_date_str = d.strftime("%Y%m%d")
        
        print(f"\n[•] Simulasi Backfill untuk tanggal: {date_str}")
        
        # Ambil Whale flow untuk hari tsb, exception handled
        idx_cache = fetch_idx_for_date(idx_date_str)
        if not idx_cache:
            print(f"    [!] Data Whale Flow IDX kosong, menggunakan data netral.")
            
        market_status = {"status": "NORMAL", "defensive": False, "chg_pct": 0, "label": "Backfill Mock"}
        day_results = []
        
        # Mock / Replace fungsi `ambil_data` agar memberikan data saham yang dipotong sampai `date_str`
        def mock_ambil_data(ticker):
            if ticker not in history_cache: return None
            df_full = history_cache[ticker]
            # Potong df sampai tanggal d (inklusif)
            slice_mask = df_full.index.date <= d
            df_slice = df_full[slice_mask]
            
            if len(df_slice) >= 35:
                return df_slice
            return None
            
        screener.ambil_data = mock_ambil_data
        
        # Jalankan screening seperti normal, namun datanya berasal dari fungsi `mock_ambil_data` kita
        for ticker in WATCHLIST:
            try:
                r = screener.analisis_saham(ticker, "normal", idx_cache, market_status)
                if r:
                    day_results.append(r)
            except Exception:
                pass
                
        print(f"    [OK] Ditemukan {len(day_results)} sinyal lolos screener pada {date_str}.")
        
        # Tandai sebagai backfill dan update struktur
        for r in day_results:
            r_dict = r.copy()
            r_dict["tanggal"] = date_str
            r_dict["jam"] = "15:30"
            r_dict["data_type"] = "backfill"
            all_results.append(r_dict)
            
        time.sleep(1) # Delay biar aman

    print(f"\n==================================================")
    print(f"[DONE] BACKFILL SELESAI! Total Sinyal: {len(all_results)}")
    
    # 4. Simpan ke CSV
    if all_results:
        history_file = "screener_history.csv"
        df_history = pd.DataFrame(all_results)
        
        # Atur urutan kolom supaya rapi (tanggal, jam, data_type berada di awal)
        cols = df_history.columns.tolist()
        for c in ['data_type', 'jam', 'tanggal']:
            if c in cols: cols.remove(c)
        cols = ['tanggal', 'jam', 'data_type'] + cols
        df_history = df_history[cols]
        
        file_exists = os.path.isfile(history_file)
        df_history.to_csv(history_file, mode='a', header=not file_exists, index=False)
        
        print(f"[OK] Berhasil menyimpan {len(df_history)} baris data historis (backfill) ke {history_file}")
    else:
        print("Tidak ada sinyal yang lolos filter selama periode tersebut.")

if __name__ == "__main__":
    main()
