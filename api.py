from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import time

# Import fungsi-fungsi core dari bsjp_bot.py
import bsjp_bot

app = FastAPI(title="BSJP Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cache untuk menyimpan hasil scan terbaru
SCAN_CACHE = {}

@app.get("/")
def read_root():
    # Arahkan / ke index.html
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

@app.get("/api/weather")
def get_weather():
    """Mengambil status cuaca IHSG terbaru"""
    market_status = bsjp_bot.analisis_ihsg_trend()
    return market_status

@app.get("/api/scan")
def run_scan(mode: str = "normal"):
    """
    Menjalankan proses screening berdasarkan mode.
    Proses ini disederhanakan dari main() di bsjp_bot.py
    """
    if mode not in ["safe", "normal", "gorengan"]:
        mode = "normal"
        
    market_status = bsjp_bot.analisis_ihsg_trend()
    idx_cache = bsjp_bot.ambil_idx_stock_summary()
    
    scan_list = bsjp_bot.WATCHLIST
    if mode == "gorengan" and idx_cache:
        sorted_aktif = sorted(idx_cache.items(), key=lambda x: x[1].get("volume", 0), reverse=True)
        g_list = [k for k, v in sorted_aktif[:250]]
        scan_list = list(set(bsjp_bot.WATCHLIST + g_list))
        
    results_raw = []
    results = []
    for ticker in scan_list:
        try:
            r = bsjp_bot.analisis_saham(ticker, mode, idx_cache, market_status)
            if r:
                SCAN_CACHE[ticker] = r  # Simpan data mentah
                results_raw.append(r)
                # Karena return object bsjp_bot ada dict kompleks, kita hanya ambil yang perlu
                results.append({
                    "ticker": r["ticker"],
                    "sektor": r["sektor"],
                    "close": r["close"],
                    "chg": r["chg"],
                    "score": r["score"],
                    "signal": r["signal"].strip(),
                    "hint": r["hint"],
                    "panduan": r["panduan"]
                })
        except Exception:
            pass
        # Jeda agar tidak diblokir Yahoo Finance
        time.sleep(0.2)
        
    # Sort berdasarkan skor tertinggi
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    
    # Simpan hasil scan ke CSV agar tersimpan setiap hari
    if results_raw:
        try:
            bsjp_bot.simpan_csv(results_raw, mode)
        except Exception as e:
            print(f"Gagal menyimpan CSV hasil scan: {e}")
            
    return {
        "status": "success",
        "mode": mode.upper(),
        "total_scan": len(scan_list),
        "total_lolos": len(results),
        "market_status": market_status,
        "results": results
    }

def fetch_idx_broker(ticker: str):
    try:
        from curl_cffi import requests as cf_requests
        from datetime import datetime, timedelta
        
        base_date = datetime.now()
        dates_to_try = [(base_date - timedelta(days=i)).strftime("%Y%m%d") for i in range(5)]
        url = "https://www.idx.co.id/primary/TradingSummary/GetBrokerSummary"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-broker/",
            "Accept": "application/json",
        }
        
        for date_str in dates_to_try:
            params = {"date": date_str, "stockCode": ticker, "start": "0", "length": "50"}
            r = cf_requests.get(url, headers=headers, params=params, timeout=5, impersonate="chrome")
            if r.status_code == 200:
                data = r.json()
                items = data.get("data", [])
                if items:
                    # Sort by Value descending (Top Brokers by Value)
                    items = sorted(items, key=lambda x: x.get("Value", 0), reverse=True)
                    top_5 = items[:5]
                    results = []
                    for it in top_5:
                        vol = it.get("Volume", 0)
                        val = it.get("Value", 0)
                        avg = (val / vol) if vol > 0 else 0
                        results.append({
                            "broker": it.get("IDFirm", ""),
                            "type": "ACTIVE",
                            "volume": f"{int(vol/100):,} Lot",
                            "avg_price": f"Rp {int(avg):,}"
                        })
                    return results
    except Exception:
        pass
    return []

@app.get("/api/detail/{ticker}")
def get_stock_detail(ticker: str):
    """
    Mengambil detail spesifik saham: berita mentah, breakdown indikator, 
    dan bandarmologi broker.
    """
    ticker = ticker.upper()
    
    # 1. Ambil data broker spesifik
    broker_data = bsjp_bot.ambil_broker_summary(ticker)
    
    # 2. Ambil berita lengkap
    sentimen = bsjp_bot.ambil_sentimen(ticker)
    
    # 3. Score Breakdown & Aggregate Whale (dari cache)
    r = SCAN_CACHE.get(ticker, {})
    breakdown = []
    aggregate_whale = {}
    
    if r:
        candle_pola = r.get('candle', {}).get('pola')
        breakdown = [
            {"label": "VSpike (Lonjakan Vol)", "value": f"{r.get('vspike', 0):.0f}%"},
            {"label": "RSI (Momentum)", "value": f"{r.get('rsi', 0):.1f}"},
            {"label": "MACD Trend", "value": r.get('macd', {}).get('status', '-')},
            {"label": "Whale Flow", "value": r.get('whale', {}).get('status', '-')},
            {"label": "Posisi VWAP", "value": r.get('vwap', {}).get('status', '-')},
            {"label": "Candlestick", "value": candle_pola[0] if candle_pola else "-"}
        ]
        
        # Fallback jika scraping broker spesifik gagal
        net_f = r.get('whale', {}).get('net_foreign_val', 0)
        net_f_str = f"+{net_f/1e9:.2f} Miliar" if net_f > 0 else f"{net_f/1e9:.2f} Miliar"
        if abs(net_f) < 1e9:
            net_f_str = f"+{net_f/1e6:.0f} Juta" if net_f > 0 else f"{net_f/1e6:.0f} Juta"
            
        aggregate_whale = {
            "status": r.get('whale', {}).get('status', '-'),
            "net_foreign": net_f_str,
            "foreign_pct": f"{r.get('whale', {}).get('foreign_pct', 0)}%"
        }
    
    return {
        "ticker": ticker,
        "broker_summary": broker_data,
        "aggregate_whale": aggregate_whale,
        "breakdown": breakdown,
        "news": sentimen.get("berita_list", [])
    }

@app.get("/api/config")
def get_config():
    return bsjp_bot.CONFIG

class ConfigModel(BaseModel):
    TELEGRAM_TOKEN: str
    TELEGRAM_CHAT_ID: str
    SAFE_VSPIKE_MIN: int
    NORMAL_VSPIKE_MIN: int
    AGGRESSIVE_VSPIKE_MIN: int
    SAFE_RSI_MAX: int
    NORMAL_RSI_MAX: int
    AGGRESSIVE_RSI_MAX: int

@app.post("/api/config")
def update_config(config_data: ConfigModel):
    bsjp_bot.CONFIG.update(config_data.dict())
    bsjp_bot.save_config()
    return {"status": "success", "message": "Config updated"}

@app.get("/api/chart/{ticker}")
def get_chart_data(ticker: str):
    import yfinance as yf
    try:
        stk = yf.Ticker(f"{ticker}.JK")
        df = stk.history(period="3mo", auto_adjust=True)
        if df.empty:
            return []
        
        # Format ke bentuk yang dibutuhkan Lightweight Charts: {time: 'YYYY-MM-DD', open, high, low, close}
        import pandas as pd
        chart_data = []
        seen_dates = set()
        
        for date, row in df.iterrows():
            if pd.isna(row["Open"]) or pd.isna(row["Close"]): continue
            
            d_str = date.strftime("%Y-%m-%d")
            if d_str in seen_dates: continue
            seen_dates.add(d_str)
            
            chart_data.append({
                "time": d_str,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"])
            })
            
        # Pastikan terurut dari tanggal paling lama ke paling baru (ascending)
        chart_data = sorted(chart_data, key=lambda x: x["time"])
        return chart_data
    except Exception as e:
        return []

@app.get("/api/history")
def get_history(file: str = None):
    import glob, os, pandas as pd
    import yfinance as yf
    
    if file:
        latest_csv = file
    else:
        files = glob.glob("bsjp_hasil_*.csv")
        if not files:
            return {"status": "error", "message": "Belum ada file history CSV"}
        files.sort(key=os.path.getmtime, reverse=True)
        latest_csv = files[0]
        
    if not os.path.exists(latest_csv):
        return {"status": "error", "message": f"File {latest_csv} tidak ditemukan"}
    
    try:
        df = pd.read_csv(latest_csv)
        results = []
        win_count = 0
        
        for _, row in df.iterrows():
            ticker = row.get("Ticker", row.get("ticker", ""))
            if not ticker: continue
            
            # Mendukung format kolom lama (Buy Ideal, Close) dan baru (close, est_low)
            if "Buy Ideal" in row:
                buy_price = float(row["Buy Ideal"])
            elif "buy_ideal" in row:
                buy_price = float(row["buy_ideal"])
            elif "Close" in row:
                buy_price = float(row["Close"])
            elif "close" in row:
                buy_price = float(row["close"])
            else:
                buy_price = float(row.get("close", 0))
                
            target_price = float(row.get("Target", row.get("target", row.get("Target", buy_price * 1.05))))
            
            # Ambil harga saat ini
            stk = yf.Ticker(f"{ticker}.JK")
            hist = stk.history(period="1d", auto_adjust=True)
            if not hist.empty:
                current_price = hist["Close"].iloc[-1]
                profit_pct = ((current_price - buy_price) / buy_price) * 100
                is_win = profit_pct > 0
                if is_win: win_count += 1
                
                results.append({
                    "ticker": ticker,
                    "buy_price": buy_price,
                    "current_price": current_price,
                    "target_price": target_price,
                    "profit_pct": round(profit_pct, 2),
                    "is_win": is_win,
                    "tanggal_scan": os.path.basename(latest_csv).replace("bsjp_hasil_", "").replace(".csv", "")
                })
        
        win_rate = (win_count / len(results) * 100) if results else 0
        return {
            "status": "success",
            "file": os.path.basename(latest_csv),
            "win_rate": round(win_rate, 2),
            "data": results
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/history/files")
def get_history_files():
    import glob, os
    from datetime import datetime
    files = glob.glob("bsjp_hasil_*.csv")
    if not files:
        return []
    
    files.sort(key=os.path.getmtime, reverse=True)
    
    result = []
    for f in files:
        base = os.path.basename(f)
        try:
            # Format: bsjp_hasil_YYYYMMDD_HHMM.csv
            parts = base.replace("bsjp_hasil_", "").replace(".csv", "").split("_")
            dt = datetime.strptime(parts[0] + "_" + parts[1], "%Y%m%d_%H%M")
            date_str = dt.strftime("%d %B %Y, %H:%M")
        except:
            mtime = os.path.getmtime(f)
            date_str = datetime.fromtimestamp(mtime).strftime("%d %B %Y, %H:%M")
            
        result.append({
            "filename": base,
            "label": date_str
        })
    return result

if __name__ == "__main__":
    import uvicorn
    import threading
    import requests
    
    # ---------------------------------------------------------
    # SETUP AUTO-SCANNER 15:45 WIB (Hanya Hari Kerja Bursa)
    # ---------------------------------------------------------
    def start_scheduler():
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            from datetime import datetime
            import pytz
            import holidays
            
            def run_auto_scan():
                now = datetime.now(pytz.timezone('Asia/Jakarta'))
                
                # Cek libur nasional Indonesia
                id_holidays = holidays.ID(years=now.year)
                if now.date() in id_holidays:
                    print(f"⏳ Auto-scan dilewati: Hari Libur Nasional ({id_holidays.get(now.date())})")
                    return
                
                print(f"🚀 [{now.strftime('%H:%M:%S')}] Memulai Auto-Scan ke-3 Mode (Safe, Normal, Gorengan)...")
                try:
                    requests.get("http://localhost:8000/api/scan?mode=safe", timeout=300)
                    requests.get("http://localhost:8000/api/scan?mode=normal", timeout=300)
                    requests.get("http://localhost:8000/api/scan?mode=gorengan", timeout=300)
                    print("✅ Auto-scan harian selesai dan berhasil disimpan!")
                except Exception as e:
                    print(f"❌ Error saat Auto-scan: {e}")

            scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Jakarta'))
            # Jadwalkan jam 15:45 setiap hari Senin - Jumat (cron)
            scheduler.add_job(run_auto_scan, CronTrigger(day_of_week='mon-fri', hour=15, minute=45))
            scheduler.start()
            print("🕒 Auto-Scanner Aktif: Dijadwalkan setiap 15:45 WIB (Senin-Jumat, Non-Libur)")
        except ImportError:
            print("⚠️ Modul 'apscheduler' atau 'holidays' belum terinstall. Auto-scanner dimatikan.")
            
    # Jalankan scheduler di background thread
    threading.Thread(target=start_scheduler, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
