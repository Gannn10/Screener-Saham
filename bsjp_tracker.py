"""
BSJP Morning Tracker
Jalan otomatis jam 09.30 WIB setiap hari
Tugasnya:
  1. Baca hasil screener kemarin dari CSV
  2. Ambil harga open & current hari ini
  3. Hitung apakah prediksi benar (naik/turun)
  4. Kirim laporan akurasi ke Telegram
"""

import os, sys, glob, time, warnings
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "8604469961:AAFk_K-EzJ6wiJp7oZoBQHVouwYmMOmEB1Y")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5465692885")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# ═══════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════

def kirim_telegram(pesan: str) -> bool:
    if not HAS_REQUESTS or not TELEGRAM_TOKEN:
        print(pesan)
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": pesan,
                  "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False


# ═══════════════════════════════════════════════════
# BACA CSV KEMARIN
# ═══════════════════════════════════════════════════

def cari_csv_kemarin() -> pd.DataFrame | None:
    """
    Cari file CSV hasil screener kemarin
    Format nama: bsjp_hasil_YYYYMMDD_HHMM.csv
    """
    # Cari semua CSV di folder
    files = glob.glob("bsjp_hasil_*.csv")
    if not files:
        print("  Tidak ada file CSV hasil screener ditemukan.")
        return None

    # Sort by waktu modifikasi, ambil yang terbaru
    files.sort(key=os.path.getmtime, reverse=True)
    latest = files[0]

    print(f"  Membaca hasil screener dari: {latest}")
    try:
        df = pd.read_csv(latest)
        print(f"  Ditemukan {len(df)} saham dari screener kemarin")
        return df
    except Exception as e:
        print(f"  Gagal baca CSV: {e}")
        return None


# ═══════════════════════════════════════════════════
# AMBIL HARGA HARI INI
# ═══════════════════════════════════════════════════

def ambil_harga_hari_ini(ticker: str) -> dict | None:
    """
    Ambil data harga terbaru hari ini
    Return: open, current, high, low, chg_dari_kemarin
    """
    try:
        stk  = yf.Ticker(f"{ticker}.JK")
        hist = stk.history(period="2d", auto_adjust=True)

        if hist is None or len(hist) < 1:
            return None

        # Harga kemarin (close) dan hari ini
        close_kemarin = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else None
        open_hari_ini = float(hist["Open"].iloc[-1])
        high_hari_ini = float(hist["High"].iloc[-1])
        low_hari_ini  = float(hist["Low"].iloc[-1])
        close_skrg    = float(hist["Close"].iloc[-1])

        chg_dari_kemarin = 0.0
        if close_kemarin and close_kemarin > 0:
            chg_dari_kemarin = (close_skrg - close_kemarin) / close_kemarin * 100

        chg_dari_open = 0.0
        if open_hari_ini > 0:
            chg_dari_open = (close_skrg - open_hari_ini) / open_hari_ini * 100

        return {
            "ticker":          ticker,
            "close_kemarin":   close_kemarin,
            "open_hari_ini":   open_hari_ini,
            "high_hari_ini":   high_hari_ini,
            "low_hari_ini":    low_hari_ini,
            "close_skrg":      close_skrg,
            "chg_dari_kemarin": round(chg_dari_kemarin, 2),
            "chg_dari_open":   round(chg_dari_open, 2),
        }
    except Exception as e:
        print(f"  Error ambil data {ticker}: {e}")
        return None


# ═══════════════════════════════════════════════════
# EVALUASI PREDIKSI
# ═══════════════════════════════════════════════════

def evaluasi_prediksi(row: pd.Series, harga: dict) -> dict:
    """
    Bandingkan prediksi kemarin vs aktual hari ini

    Prediksi BSJP dianggap BENAR jika:
    - Harga open hari ini >= close kemarin (gap up atau flat)
    - ATAU harga hari ini lebih tinggi dari close kemarin minimal 0.5%

    Prediksi SALAH jika:
    - Harga open turun lebih dari 1% dari close kemarin
    """
    close_kemarin = float(row.get("close", 0))
    est_low       = float(row.get("est_low", 0))
    est_mid       = float(row.get("est_mid", 0))
    est_high      = float(row.get("est_high", 0))
    est_arah      = str(row.get("est_arah", "SIDEWAYS"))

    open_aktual   = harga["open_hari_ini"]
    close_aktual  = harga["close_skrg"]
    chg_aktual    = harga["chg_dari_kemarin"]

    # Apakah arah prediksi benar?
    if est_arah == "NAIK":
        arah_benar = chg_aktual >= 0.5   # naik minimal 0.5%
    elif est_arah == "TURUN":
        arah_benar = chg_aktual <= -0.5
    else:
        arah_benar = abs(chg_aktual) < 2  # sideways = gerak kurang dari 2%

    # Apakah harga masuk range estimasi?
    dalam_range = est_low <= close_aktual <= est_high if est_low > 0 else False

    # Profit jika beli di close kemarin, jual di open hari ini (BSJP)
    profit_pct = 0.0
    if close_kemarin > 0:
        profit_pct = (open_aktual - close_kemarin) / close_kemarin * 100

    # Status
    if arah_benar and profit_pct >= 0.5:
        status = "✅ BENAR"
        emoji  = "✅"
    elif arah_benar:
        status = "⚡ TIPIS"
        emoji  = "⚡"
    else:
        status = "❌ SALAH"
        emoji  = "❌"

    return {
        "ticker":        row.get("ticker", "?"),
        "score_kemarin": int(row.get("score", 0)),
        "signal_kemarin":str(row.get("signal", "-")).strip(),
        "est_arah":      est_arah,
        "est_mid":       est_mid,
        "close_kemarin": close_kemarin,
        "open_aktual":   open_aktual,
        "close_aktual":  close_aktual,
        "chg_aktual":    chg_aktual,
        "profit_bsjp":   round(profit_pct, 2),
        "dalam_range":   dalam_range,
        "arah_benar":    arah_benar,
        "status":        status,
        "emoji":         emoji,
    }


# ═══════════════════════════════════════════════════
# FORMAT PESAN TELEGRAM
# ═══════════════════════════════════════════════════

def format_laporan(hasil_eval: list, tgl_kemarin: str) -> str:
    if not hasil_eval:
        return (
            f"📊 <b>BSJP Morning Tracker</b>\n"
            f"{datetime.now().strftime('%d %b %Y %H:%M WIB')}\n\n"
            f"⚠️ Tidak ada data prediksi untuk dievaluasi."
        )

    # Hitung statistik
    total     = len(hasil_eval)
    benar     = sum(1 for h in hasil_eval if "BENAR" in h["status"])
    tipis     = sum(1 for h in hasil_eval if "TIPIS" in h["status"])
    salah     = sum(1 for h in hasil_eval if "SALAH" in h["status"])
    win_rate  = round((benar + tipis) / total * 100) if total > 0 else 0
    avg_profit= round(sum(h["profit_bsjp"] for h in hasil_eval) / total, 2) if total > 0 else 0

    # Header
    baris = [
        f"📊 <b>BSJP Morning Tracker</b>",
        f"Evaluasi prediksi: {tgl_kemarin}",
        f"{datetime.now().strftime('%d %b %Y %H:%M WIB')}\n",
        f"📈 Win rate: <b>{win_rate}%</b> ({benar} benar + {tipis} tipis dari {total})",
        f"💰 Avg profit BSJP: <b>{avg_profit:+.2f}%</b>\n",
        f"━━━━━━━━━━━━━━━━━━━━━━\n",
    ]

    # Detail per saham
    for h in sorted(hasil_eval, key=lambda x: x["profit_bsjp"], reverse=True):
        profit_str = f"{h['profit_bsjp']:+.2f}%"
        baris.append(
            f"{h['emoji']} <b>{h['ticker']}</b> "
            f"(Score:{h['score_kemarin']})\n"
            f"   Prediksi: {h['est_arah']} → Est mid: {h['est_mid']:,.0f}\n"
            f"   Aktual: Open {h['open_aktual']:,.0f} | "
            f"Now {h['close_aktual']:,.0f} ({h['chg_aktual']:+.2f}%)\n"
            f"   Profit BSJP: <b>{profit_str}</b> "
            f"{'📈' if h['profit_bsjp'] > 0 else '📉'}\n"
        )

    # Footer motivasi
    if win_rate >= 70:
        baris.append(f"\n🔥 Rumus sedang ON FIRE! Win rate {win_rate}%")
    elif win_rate >= 50:
        baris.append(f"\n✅ Performa oke! Lanjutkan evaluasi.")
    else:
        baris.append(f"\n⚠️ Win rate rendah. Perlu tune parameter.")

    baris.append(f"\n<i>Disclaimer: Bukan rekomendasi investasi</i>")
    return "\n".join(baris)


# ═══════════════════════════════════════════════════
# SIMPAN HASIL TRACKING
# ═══════════════════════════════════════════════════

def simpan_tracking(hasil_eval: list):
    if not hasil_eval:
        return
    fn  = f"bsjp_tracking_{datetime.now().strftime('%Y%m%d')}.csv"
    df  = pd.DataFrame(hasil_eval)
    df["tgl_evaluasi"] = datetime.now().strftime("%Y-%m-%d")
    df.to_csv(fn, index=False)
    print(f"  Hasil tracking disimpan: {fn}")


# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

def main():
    print(f"\n{'='*55}")
    print(f"  BSJP Morning Tracker")
    print(f"  {datetime.now().strftime('%d %B %Y %H:%M WIB')}")
    print(f"{'='*55}\n")

    # Baca CSV kemarin
    df_kemarin = cari_csv_kemarin()
    if df_kemarin is None or len(df_kemarin) == 0:
        kirim_telegram(
            f"⚠️ <b>BSJP Morning Tracker</b>\n"
            f"Tidak ada data screener kemarin untuk dievaluasi.\n"
            f"Screener mungkin tidak jalan kemarin (hari libur?)."
        )
        return

    tgl_kemarin = str(df_kemarin["tanggal"].iloc[0]) if "tanggal" in df_kemarin.columns else "kemarin"

    # Ambil harga hari ini untuk semua saham
    print(f"\n  Mengambil harga hari ini untuk {len(df_kemarin)} saham...")
    hasil_eval = []

    for idx, row in df_kemarin.iterrows():
        ticker = str(row.get("ticker", ""))
        if not ticker:
            continue

        print(f"  Cek {ticker}...", end="", flush=True)
        harga = ambil_harga_hari_ini(ticker)

        if harga is None:
            print(" skip (no data)")
            continue

        eval_result = evaluasi_prediksi(row, harga)
        hasil_eval.append(eval_result)

        print(
            f" Open:{harga['open_hari_ini']:,.0f} "
            f"Now:{harga['close_skrg']:,.0f} "
            f"({harga['chg_dari_kemarin']:+.1f}%) "
            f"→ {eval_result['status']}"
        )
        time.sleep(0.3)

    # Cetak ringkasan di log
    print(f"\n  {'='*50}")
    total    = len(hasil_eval)
    benar    = sum(1 for h in hasil_eval if "BENAR" in h["status"])
    tipis    = sum(1 for h in hasil_eval if "TIPIS" in h["status"])
    win_rate = round((benar + tipis) / total * 100) if total > 0 else 0
    avg_pnl  = round(sum(h["profit_bsjp"] for h in hasil_eval) / total, 2) if total > 0 else 0

    print(f"  Win rate   : {win_rate}% ({benar} benar + {tipis} tipis dari {total})")
    print(f"  Avg profit : {avg_pnl:+.2f}%")
    print(f"  {'='*50}\n")

    # Simpan ke CSV
    simpan_tracking(hasil_eval)

    # Kirim laporan ke Telegram
    pesan = format_laporan(hasil_eval, tgl_kemarin)
    ok    = kirim_telegram(pesan)
    if ok:
        print("  ✅ Laporan terkirim ke Telegram!")
    else:
        print("  ❌ Gagal kirim Telegram")
        print(pesan)


if __name__ == "__main__":
    main()
