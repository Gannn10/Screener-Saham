"""
╔══════════════════════════════════════════════════════════════╗
║           BSJP SCREENER v6.0 — IHSG                         ║
║       Beli Sore Jual Pagi — by Claude (Anthropic)           ║
║                                                              ║
║  UPDATE v6.0:                                                ║
║  + Sentiment Berita AI (scrape IDX + analisis Claude AI)     ║
║  + Notifikasi Telegram otomatis                              ║
║  + Auto-scheduler jam 15.15 WIB setiap hari                 ║
║  + Tidak perlu buka laptop — hasil langsung ke HP!           ║
║                                                              ║
║  SETUP PERTAMA KALI:                                         ║
║  1. pip install yfinance pandas numpy colorama               ║
║       requests schedule beautifulsoup4                       ║
║  2. Isi TELEGRAM_TOKEN & TELEGRAM_CHAT_ID di CONFIG          ║
║  3. python bsjp_screener_v6.py → pilih mode 5 (auto)        ║
╚══════════════════════════════════════════════════════════════╝
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time, sys, warnings, json, re, threading
warnings.filterwarnings("ignore")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import schedule
    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN=RED=YELLOW=CYAN=WHITE=MAGENTA=BLUE=RESET=""
    class Style:
        BRIGHT=RESET_ALL=DIM=""

# ═══════════════════════════════════════════════════════════════
# SEKTOR — mapping ticker ke sektor IDX
# ═══════════════════════════════════════════════════════════════
SEKTOR = {
    # Perbankan
    "BBCA":"Perbankan","BBRI":"Perbankan","BMRI":"Perbankan",
    "BBNI":"Perbankan","BRIS":"Perbankan","BBTN":"Perbankan",
    "BNGA":"Perbankan","NISP":"Perbankan","BDMN":"Perbankan",
    "BJBR":"Perbankan","BJTM":"Perbankan","MAYA":"Perbankan",
    "NOBU":"Perbankan","ARTO":"Perbankan","PNBS":"Perbankan",
    "BTPS":"Perbankan","BBYB":"Perbankan","BBKP":"Perbankan",
    # Energi & Batubara
    "ADRO":"Energi","PTBA":"Energi","ITMG":"Energi",
    "HRUM":"Energi","BUMI":"Energi","PGAS":"Energi",
    "MEDC":"Energi","ELSA":"Energi","ENRG":"Energi",
    "BIPI":"Energi","ESSA":"Energi","DEWA":"Energi",
    "AKRA":"Energi","CUAN":"Energi","RATU":"Energi",
    "TOBA":"Energi","BSSR":"Energi","PTRO":"Energi",
    "AADI":"Energi",
    # Tambang & Nikel
    "INCO":"Tambang","ANTM":"Tambang","TINS":"Tambang",
    "MDKA":"Tambang","NCKL":"Tambang","AMMN":"Tambang",
    "MBMA":"Tambang","DOID":"Tambang","PGEO":"Tambang",
    "TPMA":"Tambang","MCOL":"Tambang","BRMS":"Tambang",
    # Teknologi & Telko
    "TLKM":"Telko","EXCL":"Telko","ISAT":"Telko",
    "LINK":"Telko","TOWR":"Telko","TBIG":"Telko",
    "MTEL":"Telko","EDGE":"Telko","DCII":"Telko",
    "INET":"Telko","GOTO":"Teknologi","BUKA":"Teknologi",
    "EMTK":"Teknologi","MCAS":"Teknologi",
    # Consumer & Retail
    "UNVR":"Consumer","ICBP":"Consumer","INDF":"Consumer",
    "KLBF":"Consumer","SIDO":"Consumer","HMSP":"Consumer",
    "GGRM":"Consumer","MYOR":"Consumer","ULTJ":"Consumer",
    "CLEO":"Consumer","GOOD":"Consumer","CAMP":"Consumer",
    "CMRY":"Consumer","KINO":"Consumer","MAPI":"Consumer",
    "LPPF":"Consumer","ACES":"Consumer","AMRT":"Consumer",
    "MIDI":"Consumer","CSAP":"Consumer","RALS":"Consumer",
    "AVIA":"Consumer","BOBA":"Consumer","KEJU":"Consumer",
    "COCO":"Consumer",
    # Properti & Konstruksi
    "BSDE":"Properti","CTRA":"Properti","PWON":"Properti",
    "SMRA":"Properti","LPKR":"Properti","KPIG":"Properti",
    "PANI":"Properti","WIKA":"Konstruksi","WSKT":"Konstruksi",
    "PTPP":"Konstruksi","ADHI":"Konstruksi","WTON":"Konstruksi",
    # Industri & Lain
    "ASII":"Industri","SMGR":"Industri","MNCN":"Media",
    "SCMA":"Media","FILM":"Media","BULL":"Logistik",
    "MINA":"Perikanan","DOOH":"Media","TAPG":"Agribisnis",
    "SOCI":"Agribisnis","HUMI":"Agribisnis","BKSL":"Properti",
    "KRYA":"Teknologi","NICE":"Industri","SMMT":"Industri",
    "RELI":"Keuangan","CGAS":"Energi","BREN":"Energi",
    "AMAR":"Keuangan","BANK":"Perbankan","ADMF":"Keuangan",
    "BFIN":"Keuangan","WOMF":"Keuangan","GTSI":"Teknologi",
    "CBMF":"Consumer",
}

# ═══════════════════════════════════════════════════════════════
# WATCHLIST v3.0
# ═══════════════════════════════════════════════════════════════
WATCHLIST = list(dict.fromkeys([
    "BBCA","BBRI","BMRI","BBNI","BRIS","TLKM","ASII","UNVR","ICBP","INDF",
    "SMGR","GGRM","HMSP","KLBF","SIDO","EXCL","ISAT","MNCN","SCMA","EMTK",
    "ADRO","PTBA","ITMG","HRUM","BUMI","INCO","ANTM","TINS","MDKA","NCKL",
    "PGAS","MEDC","ELSA","ENRG","BIPI","ESSA","DEWA","AKRA","CUAN","RATU",
    "BSDE","CTRA","PWON","SMRA","LPKR","WIKA","WSKT","PTPP","ADHI","WTON",
    "MAPI","LPPF","ACES","AMRT","MIDI","CSAP","RALS","KINO","ULTJ","MYOR",
    "CLEO","GOOD","CAMP","AVIA","CMRY","BBTN","BNGA","NISP","BDMN","BJBR",
    "BJTM","ADMF","BFIN","WOMF","MAYA","NOBU","ARTO","PNBS","BTPS","BBYB",
    "GOTO","BUKA","DCII","INET","LINK","TOWR","TBIG","MTEL","EDGE",
    "AMMN","MBMA","DOID","PGEO","TPMA","MCOL","GTSI","AADI","PTRO",
    "BRMS","BULL","MINA","DOOH","BBKP","TAPG","SOCI","HUMI","BKSL","KPIG",
    "PANI","FILM","MSIN","KRYA","NICE","BOBA","KEJU","COCO","SMMT","RELI",
    "CGAS","BREN","AMAR","BANK","TOBA","BSSR","MCAS","CBMF",
]))

# ═══════════════════════════════════════════════════════════════
# KONFIGURASI
# ═══════════════════════════════════════════════════════════════
CONFIG = {
    "SAFE_VSPIKE_MIN": 150, "NORMAL_VSPIKE_MIN": 100, "AGGRESSIVE_VSPIKE_MIN": 50,
    "SAFE_RSI_MAX": 60,     "NORMAL_RSI_MAX": 65,     "AGGRESSIVE_RSI_MAX": 70,
    "RSI_MIN": 30,          "CHG_MIN": 1.0,           "SAFE_CHG_MAX": 15.0,
    "VOL_AVG_PERIOD": 20,   "RSI_PERIOD": 14,         "ATR_PERIOD": 14,
    "MACD_FAST": 12,        "MACD_SLOW": 26,          "MACD_SIGNAL": 9,
    "BB_PERIOD": 20,        "BB_STD": 2.0,
    "MIN_VOLUME": 500_000,  "TOP_N": 10,              "REQUEST_DELAY": 0.3,

    # ── Telegram (isi dengan data kamu) ──────────────────────
    # Cara dapat token & chat_id: lihat panduan di README
    "TELEGRAM_TOKEN":   "8604469961:AAFk_K-EzJ6wiJp7oZoBQHVouwYmMOmEB1Y",
    "TELEGRAM_CHAT_ID": "5465692885",

    # ── Auto-scheduler ────────────────────────────────────────
    # Jam otomatis kirim sinyal setiap hari (format HH:MM WIB)
    "JADWAL_JAM":  "15:20",
    # Mode default untuk auto-scheduler
    "AUTO_MODE":   "normal",
    # Kirim notif juga kalau tidak ada sinyal kuat?
    "NOTIF_KOSONG": True,
}

# ═══════════════════════════════════════════════════════════════
# INDIKATOR TEKNIKAL
# ═══════════════════════════════════════════════════════════════

def hitung_rsi(closes, period=14):
    if len(closes) < period + 1: return 50.0
    delta    = closes.diff().dropna()
    avg_gain = delta.clip(lower=0).rolling(period, min_periods=period).mean().iloc[-1]
    avg_loss = (-delta.clip(upper=0)).rolling(period, min_periods=period).mean().iloc[-1]
    if avg_loss == 0: return 100.0
    return round(float(100 - 100 / (1 + avg_gain / avg_loss)), 2)


def hitung_vspike(volumes, avg_period=20):
    if len(volumes) < avg_period + 1: return 0.0
    avg = volumes.iloc[-(avg_period+1):-1].mean()
    return round(float(volumes.iloc[-1] / avg * 100), 1) if avg else 0.0


def hitung_chg(closes):
    if len(closes) < 2: return 0.0
    prev = closes.iloc[-2]
    return round(float((closes.iloc[-1] - prev) / prev * 100), 2) if prev else 0.0


def hitung_atr(df, period=14):
    if len(df) < period + 1: return 0.0
    h, l, c = df["High"], df["Low"], df["Close"]
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return round(float(tr.rolling(period).mean().iloc[-1]), 2)


def hitung_sr(df, lookback=20):
    if len(df) < lookback + 1: return 0.0, 0.0
    w = df.iloc[-(lookback+1):-1]
    return round(float(w["Low"].min()), 0), round(float(w["High"].max()), 0)


def cek_waktu_scan() -> dict:
    """
    Validasi waktu scan — apakah data sudah final atau belum
    ──────────────────────────────────────────────────────────
    Jam bursa IDX:
      09.00–11.30 → Sesi 1 (data BELUM final)
      11.30–13.30 → Istirahat (data BELUM final)
      13.30–15.00 → Sesi 2 (data BELUM final)
      15.00–15.15 → Pre-closing / lelang penutupan
      15.15+      → Close FINAL ✅ — waktu ideal scan
    """
    now  = datetime.now()
    jam  = now.hour
    mnt  = now.minute
    total_mnt = jam * 60 + mnt  # menit dari tengah malam

    BUKA_1    = 9  * 60        # 09:00
    TUTUP_1   = 11 * 60 + 30   # 11:30
    BUKA_2    = 13 * 60 + 30   # 13:30
    CLOSING   = 15 * 60        # 15:00
    FINAL     = 15 * 60 + 15   # 15:15 — close FINAL

    if total_mnt < BUKA_1:
        status = "BEFORE_OPEN"
        label  = "Bursa belum buka hari ini"
        aman   = False
        warna  = "RED"
    elif BUKA_1 <= total_mnt < TUTUP_1:
        sisa   = FINAL - total_mnt
        status = "SESI_1"
        label  = f"Sesi 1 sedang berjalan — data belum final (sisa ~{sisa} menit)"
        aman   = False
        warna  = "RED"
    elif TUTUP_1 <= total_mnt < BUKA_2:
        sisa   = FINAL - total_mnt
        status = "ISTIRAHAT"
        label  = f"Jam istirahat — sesi 2 belum mulai (sisa ~{sisa} menit ke close)"
        aman   = False
        warna  = "YELLOW"
    elif BUKA_2 <= total_mnt < CLOSING:
        sisa   = FINAL - total_mnt
        status = "SESI_2"
        label  = f"Sesi 2 sedang berjalan — data belum final (sisa ~{sisa} menit)"
        aman   = False
        warna  = "RED"
    elif CLOSING <= total_mnt < FINAL:
        status = "PRE_CLOSING"
        label  = "Pre-closing/lelang — hampir final, tunggu 15.15 WIB"
        aman   = False
        warna  = "YELLOW"
    else:
        status = "FINAL"
        label  = "Harga close FINAL ✅ — waktu ideal scan!"
        aman   = True
        warna  = "GREEN"

    return {
        "status": status,
        "label":  label,
        "aman":   aman,
        "warna":  warna,
        "jam_str": now.strftime("%H:%M"),
    }


def hitung_arah_volume(df, lookback: int = 5) -> dict:
    """
    Deteksi arah volume — AKUMULASI vs DISTRIBUSI
    ──────────────────────────────────────────────
    Logika:
      • Candle HIJAU (close > open) dengan volume besar = Akumulasi (beli)
      • Candle MERAH (close < open) dengan volume besar = Distribusi (jual)

    Cara hitung:
      vol_beli    = total volume di candle hijau N hari terakhir
      vol_jual    = total volume di candle merah N hari terakhir
      rasio_beli  = vol_beli / (vol_beli + vol_jual) × 100

    Sinyal:
      rasio_beli >= 65% → AKUMULASI kuat  ✅
      rasio_beli >= 55% → AKUMULASI lemah ✅
      rasio_beli >= 45% → NETRAL          ⚠️
      rasio_beli <  45% → DISTRIBUSI      ❌ — hindari!
      rasio_beli <  35% → DISTRIBUSI kuat ❌❌ — bahaya!

    Ini adalah filter utama pencegah kasus seperti PTPP:
    Volume spike besar tapi ternyata volume JUAL dominan.
    """
    if len(df) < lookback + 1:
        return {"rasio_beli": 50, "status": "INSUFFICIENT",
                "label": "Data kurang", "aman": True}

    window = df.tail(lookback).copy()

    # Deteksi candle hijau/merah dari open vs close
    # Jika tidak ada kolom Open, gunakan close vs prev close
    if "Open" in window.columns:
        is_hijau = window["Close"] >= window["Open"]
    else:
        is_hijau = window["Close"] >= window["Close"].shift(1).fillna(window["Close"])

    vol_beli = float(window.loc[is_hijau,  "Volume"].sum())
    vol_jual = float(window.loc[~is_hijau, "Volume"].sum())
    total    = vol_beli + vol_jual

    rasio = round((vol_beli / total * 100), 1) if total > 0 else 50.0

    # Hari ini khusus — candle hari ini hijau atau merah?
    close_today = float(df["Close"].iloc[-1])
    if "Open" in df.columns:
        open_today = float(df["Open"].iloc[-1])
    else:
        open_today = float(df["Close"].iloc[-2]) if len(df) >= 2 else close_today

    candle_hari_ini = "HIJAU 🟢" if close_today >= open_today else "MERAH 🔴"

    # Volume hari ini vs rata-rata
    vol_today   = float(df["Volume"].iloc[-1])
    vol_avg     = float(df["Volume"].iloc[-CONFIG["VOL_AVG_PERIOD"]-1:-1].mean())
    vol_ratio   = round(vol_today / vol_avg, 1) if vol_avg > 0 else 1.0

    # Bahaya jika: volume besar tapi candle merah
    distribusi_hari_ini = (close_today < open_today) and (vol_ratio >= 2.0)

    if distribusi_hari_ini:
        status, label, aman = "DISTRIBUSI_HARI_INI", "🚨 Distribusi hari ini! Volume besar + candle MERAH", False
    elif rasio >= 65:
        status, label, aman = "AKUMULASI_KUAT",  "✅ Akumulasi kuat",    True
    elif rasio >= 55:
        status, label, aman = "AKUMULASI",       "✅ Akumulasi",         True
    elif rasio >= 45:
        status, label, aman = "NETRAL",           "⚠️ Netral",           True
    elif rasio >= 35:
        status, label, aman = "DISTRIBUSI",      "❌ Distribusi — hati-hati", False
    else:
        status, label, aman = "DISTRIBUSI_KUAT", "🚨 Distribusi kuat — hindari!", False

    return {
        "rasio_beli":          rasio,
        "vol_beli":            vol_beli,
        "vol_jual":            vol_jual,
        "status":              status,
        "label":               label,
        "aman":                aman,
        "candle_hari_ini":     candle_hari_ini,
        "distribusi_hari_ini": distribusi_hari_ini,
    }


def deteksi_candlestick(df) -> dict:
    """
    Deteksi 8 Pola Candlestick Bullish untuk BSJP
    ══════════════════════════════════════════════
    Semua pola dideteksi dari 3 candle terakhir (hari ini + 2 hari sebelumnya).
    Pola bullish = potensi harga naik besok pagi.

    POLA YANG DIDETEKSI:
    ────────────────────
    1. HAMMER          ⚒️
       Badan kecil di atas, sumbu bawah panjang (>2x badan)
       Artinya: seller mencoba turunkan harga tapi buyer berhasil
       dorong balik → sinyal reversal naik

    2. INVERTED HAMMER 🔨
       Badan kecil di bawah, sumbu atas panjang (>2x badan)
       Muncul setelah downtrend → potensi balik naik

    3. BULLISH ENGULFING 🟢
       Candle merah kemarin, hari ini candle hijau LEBIH BESAR
       (open lebih rendah, close lebih tinggi dari kemarin)
       Artinya: buyer mengambil alih sepenuhnya dari seller

    4. MORNING STAR     ⭐
       3 candle: merah besar → doji/kecil → hijau besar
       Pola paling kuat untuk reversal dari downtrend

    5. DOJI             ✚
       Open ≈ Close (selisih < 5% dari range)
       Artinya: ketidakpastian — pasar sedang memutuskan arah
       Di konteks uptrend = lanjut naik

    6. PIERCING LINE    📍
       Candle merah besar kemarin, hari ini hijau yang
       menembus > 50% badan candle kemarin dari bawah

    7. THREE WHITE SOLDIERS 🪖
       3 candle hijau berturut-turut, masing-masing
       close lebih tinggi dari sebelumnya → trend naik kuat

    8. DRAGONFLY DOJI   🐉
       Open = Close = High, sumbu bawah sangat panjang
       Versi ekstrem dari Hammer → sinyal reversal sangat kuat
    """
    pola_ditemukan = []
    skor_candle    = 0

    if len(df) < 3:
        return {
            "pola":       [],
            "skor":       0,
            "label":      "Data kurang",
            "ada_bullish": False,
        }

    # Ambil 3 candle terakhir
    c  = df.tail(3).copy()

    # Hitung open dari pergeseran close jika kolom Open tidak ada
    if "Open" in c.columns:
        o0, o1, o2 = float(c["Open"].iloc[0]),  float(c["Open"].iloc[1]),  float(c["Open"].iloc[2])
    else:
        # Estimasi open dari close sebelumnya
        o0 = float(df["Close"].iloc[-4]) if len(df) >= 4 else float(c["Close"].iloc[0])
        o1 = float(c["Close"].iloc[0])
        o2 = float(c["Close"].iloc[1])

    h0, h1, h2 = float(c["High"].iloc[0]),  float(c["High"].iloc[1]),  float(c["High"].iloc[2])
    l0, l1, l2 = float(c["Low"].iloc[0]),   float(c["Low"].iloc[1]),   float(c["Low"].iloc[2])
    c0, c1, c2 = float(c["Close"].iloc[0]), float(c["Close"].iloc[1]), float(c["Close"].iloc[2])

    # Properti candle
    body2    = abs(c2 - o2)                    # badan hari ini
    body1    = abs(c1 - o1)                    # badan kemarin
    body0    = abs(c0 - o0)                    # badan 2 hari lalu
    range2   = h2 - l2                         # range hari ini (high - low)
    range1   = h1 - l1
    range0   = h0 - l0

    upper_shadow2 = h2 - max(c2, o2)           # sumbu atas hari ini
    lower_shadow2 = min(c2, o2) - l2           # sumbu bawah hari ini
    upper_shadow1 = h1 - max(c1, o1)
    lower_shadow1 = min(c1, o1) - l1

    is_green2 = c2 >= o2                       # hari ini hijau?
    is_red2   = c2 < o2
    is_green1 = c1 >= o1                       # kemarin hijau?
    is_red1   = c1 < o1
    is_red0   = c0 < o0                        # 2 hari lalu merah?

    tol = 0.001                                # toleransi floating point

    # ── 1. HAMMER ──────────────────────────────────────────────
    # Badan kecil (<30% range), sumbu bawah > 2x badan, sumbu atas kecil
    if (range2 > 0 and body2 < range2 * 0.35
            and lower_shadow2 >= body2 * 2.0
            and upper_shadow2 <= body2 * 0.5):
        pola_ditemukan.append("Hammer ⚒️")
        skor_candle += 20

    # ── 2. INVERTED HAMMER ─────────────────────────────────────
    if (range2 > 0 and body2 < range2 * 0.35
            and upper_shadow2 >= body2 * 2.0
            and lower_shadow2 <= body2 * 0.5
            and is_green2):
        pola_ditemukan.append("Inv.Hammer 🔨")
        skor_candle += 15

    # ── 3. BULLISH ENGULFING ────────────────────────────────────
    # Kemarin merah, hari ini hijau yang lebih besar
    if (is_red1 and is_green2
            and o2 <= c1 + tol
            and c2 >= o1 - tol
            and body2 > body1 * 0.9):
        pola_ditemukan.append("Bull.Engulfing 🟢")
        skor_candle += 25

    # ── 4. MORNING STAR ─────────────────────────────────────────
    # 2 hari lalu merah besar, kemarin badan kecil, hari ini hijau besar
    if (is_red0 and body0 > range0 * 0.5
            and body1 < range1 * 0.3
            and is_green2 and body2 > range2 * 0.4
            and c2 > (o0 + c0) / 2):
        pola_ditemukan.append("Morning Star ⭐")
        skor_candle += 30  # Paling kuat!

    # ── 5. DOJI ─────────────────────────────────────────────────
    # Badan sangat kecil (<5% dari range)
    if range2 > 0 and body2 < range2 * 0.05:
        pola_ditemukan.append("Doji ✚")
        skor_candle += 10

    # ── 6. PIERCING LINE ────────────────────────────────────────
    # Kemarin merah, hari ini hijau buka di bawah low kemarin
    # dan close menembus > 50% badan kemarin
    mid_body1 = (o1 + c1) / 2
    if (is_red1 and is_green2
            and o2 < l1
            and c2 > mid_body1
            and c2 < o1):
        pola_ditemukan.append("Piercing Line 📍")
        skor_candle += 20

    # ── 7. THREE WHITE SOLDIERS ─────────────────────────────────
    # 3 candle hijau berturut, close makin tinggi, badan cukup besar
    if (is_green2 and is_green1 and (c0 >= o0)
            and c2 > c1 > c0
            and body2 > range2 * 0.4
            and body1 > range1 * 0.4
            and body0 > range0 * 0.4):
        pola_ditemukan.append("3 White Soldiers 🪖")
        skor_candle += 28

    # ── 8. DRAGONFLY DOJI ───────────────────────────────────────
    # Open ≈ Close ≈ High, sumbu bawah sangat panjang
    if (range2 > 0
            and body2 < range2 * 0.05
            and upper_shadow2 < range2 * 0.05
            and lower_shadow2 > range2 * 0.8):
        pola_ditemukan.append("Dragonfly Doji 🐉")
        skor_candle += 25

    # Batasi skor max 40
    skor_candle = min(skor_candle, 40)

    if not pola_ditemukan:
        label      = "Tidak ada pola khusus"
        ada_bullish = False
    elif skor_candle >= 25:
        label       = f"{'  +  '.join(pola_ditemukan)}"
        ada_bullish = True
    else:
        label       = f"{'  +  '.join(pola_ditemukan)}"
        ada_bullish = True

    return {
        "pola":        pola_ditemukan,
        "skor":        skor_candle,
        "label":       label,
        "ada_bullish": ada_bullish,
    }


def hitung_macd(closes):
    """
    MACD — Moving Average Convergence Divergence
    ─────────────────────────────────────────────
    MACD Line   = EMA(12) - EMA(26)
    Signal Line = EMA(9) dari MACD Line
    Histogram   = MACD Line - Signal Line

    Sinyal BSJP:
    • GOLDEN CROSS : MACD line baru naik melewati signal line → beli
    • BULLISH      : MACD line > signal line (tren naik sedang jalan)
    • BEARISH      : MACD line < signal line (hindari)
    """
    if len(closes) < CONFIG["MACD_SLOW"] + CONFIG["MACD_SIGNAL"] + 2:
        return {"macd": 0, "signal": 0, "hist": 0,
                "status": "INSUFFICIENT", "label": "Data kurang"}

    ema_fast   = closes.ewm(span=CONFIG["MACD_FAST"],   adjust=False).mean()
    ema_slow   = closes.ewm(span=CONFIG["MACD_SLOW"],   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_ln  = macd_line.ewm(span=CONFIG["MACD_SIGNAL"], adjust=False).mean()
    histogram  = macd_line - signal_ln

    macd_now   = float(macd_line.iloc[-1])
    macd_prev  = float(macd_line.iloc[-2])
    sig_now    = float(signal_ln.iloc[-1])
    sig_prev   = float(signal_ln.iloc[-2])
    hist_now   = float(histogram.iloc[-1])
    hist_prev  = float(histogram.iloc[-2])

    # Deteksi golden cross: MACD baru saja melewati signal dari bawah
    golden_cross = (macd_prev < sig_prev) and (macd_now > sig_now)

    # Histogram makin besar = momentum naik menguat
    hist_growing = hist_now > hist_prev > 0

    if golden_cross:
        status, label = "GOLDEN_CROSS", "🟢 Golden Cross!"
    elif macd_now > sig_now and hist_growing:
        status, label = "BULLISH_STRONG", "🟢 Bullish kuat"
    elif macd_now > sig_now:
        status, label = "BULLISH", "🟡 Bullish"
    elif macd_now < sig_now and hist_now < hist_prev < 0:
        status, label = "BEARISH_STRONG", "🔴 Bearish kuat"
    else:
        status, label = "BEARISH", "🔴 Bearish"

    return {
        "macd":         round(macd_now, 4),
        "signal":       round(sig_now, 4),
        "hist":         round(hist_now, 4),
        "status":       status,
        "label":        label,
        "golden_cross": golden_cross,
        "hist_growing": hist_growing,
    }


def hitung_bollinger(closes):
    """
    Bollinger Bands — Volatilitas & Posisi Harga
    ─────────────────────────────────────────────
    Upper Band  = SMA(20) + 2×StdDev
    Middle Band = SMA(20)
    Lower Band  = SMA(20) - 2×StdDev
    %B          = (Close - Lower) / (Upper - Lower) × 100

    Sinyal BSJP:
    • SQUEEZE    : Band sangat sempit → harga mau breakout (beli antisipasi)
    • BREAKOUT_UP: Close baru tembus Upper Band ke atas → momentum kuat
    • LOWER_TOUCH: Close menyentuh/lewati Lower Band → potensi rebound
    • MIDDLE     : Harga di sekitar SMA(20) → netral
    """
    period = CONFIG["BB_PERIOD"]
    std_m  = CONFIG["BB_STD"]

    if len(closes) < period + 5:
        return {"upper": 0, "middle": 0, "lower": 0,
                "pct_b": 50, "bw": 0, "status": "INSUFFICIENT", "label": "Data kurang"}

    sma    = closes.rolling(window=period).mean()
    std    = closes.rolling(window=period).std()
    upper  = sma + std_m * std
    lower  = sma - std_m * std

    up_now  = float(upper.iloc[-1])
    mid_now = float(sma.iloc[-1])
    lo_now  = float(lower.iloc[-1])
    cl_now  = float(closes.iloc[-1])
    cl_prev = float(closes.iloc[-2])

    # %B: posisi harga di dalam band (0=lower, 100=upper)
    bw   = up_now - lo_now
    pct_b = round(((cl_now - lo_now) / bw * 100), 1) if bw > 0 else 50

    # Bandwidth relatif — untuk deteksi squeeze
    # Squeeze = bandwidth sekarang lebih kecil dari rata-rata 20 hari terakhir
    bw_series = (upper - lower) / sma * 100
    bw_avg    = float(bw_series.iloc[-20:].mean())
    bw_now_pct= float(bw_series.iloc[-1])
    is_squeeze= bw_now_pct < bw_avg * 0.85  # 15% lebih sempit dari rata-rata

    # Breakout: close baru menembus upper band dari bawah
    breakout_up   = (cl_prev <= float(upper.iloc[-2])) and (cl_now > up_now)
    lower_touch   = cl_now <= lo_now * 1.01  # dalam 1% dari lower band

    if is_squeeze:
        status, label = "SQUEEZE",      "⚡ Squeeze — siap breakout"
    elif breakout_up:
        status, label = "BREAKOUT_UP",  "🚀 Breakout Upper Band!"
    elif lower_touch:
        status, label = "LOWER_TOUCH",  "🔵 Sentuh Lower — rebound?"
    elif pct_b >= 70:
        status, label = "UPPER_ZONE",   "🟡 Zona upper (hati-hati)"
    elif pct_b <= 30:
        status, label = "LOWER_ZONE",   "🟢 Zona lower (murah)"
    else:
        status, label = "MIDDLE",       "⚪ Tengah range"

    return {
        "upper":      round(up_now, 0),
        "middle":     round(mid_now, 0),
        "lower":      round(lo_now, 0),
        "pct_b":      pct_b,
        "bw_pct":     round(bw_now_pct, 2),
        "is_squeeze": is_squeeze,
        "breakout_up":breakout_up,
        "lower_touch":lower_touch,
        "status":     status,
        "label":      label,
    }


def hitung_score(vspike, rsi, chg, macd_data, bb_data, vol_arah, candle, mode="normal"):
    """
    Scoring v5.0 — 7 komponen (total 100 poin)
    ─────────────────────────────────────────────
    VSpike      : 28 poin  (volume anomali)
    RSI         : 18 poin  (momentum)
    Chg%        : 12 poin  (konfirmasi naik)
    MACD        : 17 poin  (tren)
    BB          :  8 poin  (posisi & volatilitas)
    Arah Volume :  7 poin  (akumulasi vs distribusi)
    Candlestick : 10 poin  (konfirmasi pola ← NEW v5.0)
    """
    score = 0

    # --- VSpike (28 poin) ---
    thresh = {"safe":150,"normal":100,"aggressive":50}[mode]
    if   vspike >= thresh:        score += 28
    elif vspike >= thresh * 0.75: score += 18
    elif vspike >= thresh * 0.5:  score += 8
    if   vspike >= 400: score += 5
    elif vspike >= 200: score += 3

    # --- RSI (18 poin) ---
    rsi_max = {"safe":60,"normal":65,"aggressive":70}[mode]
    rsi_min = CONFIG["RSI_MIN"]
    if rsi_min < rsi <= rsi_max:
        score += int(18 * (1 - (rsi - rsi_min) / (rsi_max - rsi_min)))
    elif rsi <= rsi_min:
        score += 3

    # --- Chg% (12 poin) ---
    if chg > 0:
        score += int(min(chg * 1.2, 12))

    # --- MACD (17 poin) ---
    score += {
        "GOLDEN_CROSS":   17,
        "BULLISH_STRONG": 13,
        "BULLISH":         8,
        "BEARISH":         2,
        "BEARISH_STRONG":  0,
        "INSUFFICIENT":    4,
    }.get(macd_data["status"], 4)

    # --- Bollinger Bands (8 poin) ---
    score += {
        "BREAKOUT_UP":   8,
        "SQUEEZE":       7,
        "LOWER_TOUCH":   7,
        "LOWER_ZONE":    5,
        "MIDDLE":        3,
        "UPPER_ZONE":    1,
        "INSUFFICIENT":  2,
    }.get(bb_data["status"], 2)

    # --- Arah Volume (7 poin) ---
    score += {
        "AKUMULASI_KUAT":      7,
        "AKUMULASI":           5,
        "NETRAL":              3,
        "DISTRIBUSI":          0,
        "DISTRIBUSI_KUAT":     0,
        "DISTRIBUSI_HARI_INI": 0,
        "INSUFFICIENT":        2,
    }.get(vol_arah["status"], 2)

    # --- Candlestick (10 poin max) ← NEW v5.0 ---
    # Skor candle 0–40, dinormalisasi ke 0–10
    candle_pts = int(min(candle["skor"] / 4, 10))
    score += candle_pts

    return min(score, 100)


def get_signal(score):
    if score >= 75:   return "KUAT   "
    elif score >= 55: return "MODERAT"
    else:             return "LEMAH  "


def hitung_range_besok(close, atr, vspike, rsi, chg, macd_data, bb_data):
    if atr == 0 or close == 0:
        return {"target_low": close, "target_mid": close,
                "target_high": close, "arah": "SIDEWAYS",
                "confidence": 50, "gap_pct": 0.0}

    mom = 0
    if vspike >= 300:   mom += 35
    elif vspike >= 200: mom += 25
    elif vspike >= 100: mom += 15
    else:               mom += 5

    if rsi < 40:   mom += 25
    elif rsi < 50: mom += 18
    elif rsi < 60: mom += 10

    if chg >= 10:  mom += 20
    elif chg >= 5: mom += 14
    elif chg >= 2: mom += 8

    # Bonus MACD
    if macd_data["status"] == "GOLDEN_CROSS":    mom += 15
    elif macd_data["status"] == "BULLISH_STRONG": mom += 10
    elif macd_data["status"] == "BULLISH":        mom += 5

    # Bonus BB
    if bb_data["status"] == "BREAKOUT_UP":  mom += 10
    elif bb_data["status"] == "SQUEEZE":    mom += 8
    elif bb_data["status"] == "LOWER_TOUCH":mom += 7

    atr_mult    = 0.3 + (mom / 100) * 0.8
    gap_est     = atr * atr_mult
    gap_pct     = round((gap_est / close) * 100, 2)
    target_mid  = round(close + gap_est, 0)
    target_high = round(close + gap_est * 1.6, 0)
    target_low  = round(close - gap_est * 0.25, 0)

    if mom >= 70:
        arah, conf = "NAIK", min(50 + mom // 4, 74)
    elif mom >= 40:
        arah, conf = "NAIK", min(50 + mom // 5, 66)
    else:
        arah, conf = "SIDEWAYS", 50

    return {"target_low": target_low, "target_mid": target_mid,
            "target_high": target_high, "arah": arah,
            "confidence": conf, "gap_pct": gap_pct}


def fmt_vol(v):
    if v >= 1e9:   return f"{v/1e9:.2f}B"
    elif v >= 1e6: return f"{v/1e6:.1f}M"
    elif v >= 1e3: return f"{v/1e3:.0f}K"
    return str(int(v))

def fmt_h(h): return f"{h:,.0f}".replace(",", ".")

# ═══════════════════════════════════════════════════════════════
# AMBIL & ANALISIS DATA
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# SENTIMENT BERITA — Scrape IDX + Analisis AI
# ═══════════════════════════════════════════════════════════════

def scrape_berita_idx(ticker: str, max_berita: int = 5) -> list:
    """
    Scrape berita terbaru saham dari IDX
    Sumber: idx.co.id/id/news, kontan.co.id, bisnis.com
    Return list of {'judul', 'waktu', 'sumber'}
    """
    berita = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "id-ID,id;q=0.9",
    }

    # Sumber 1 — Kontan (lebih mudah di-parse)
    try:
        url = f"https://search.kontan.co.id/search/news?q={ticker}"
        r   = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200 and HAS_BS4:
            soup = BeautifulSoup(r.text, "html.parser")
            for item in soup.select(".list-news li")[:max_berita]:
                judul = item.select_one("h2 a, h3 a, .judul a")
                waktu = item.select_one(".date, time, .waktu")
                if judul:
                    berita.append({
                        "judul":  judul.get_text(strip=True),
                        "waktu":  waktu.get_text(strip=True) if waktu else "Hari ini",
                        "sumber": "Kontan",
                    })
    except Exception:
        pass

    # Sumber 2 — IDX News (RSS/API publik)
    if len(berita) < 3:
        try:
            url = (
                f"https://www.idx.co.id/umbraco/Surface/Helper/GetAllNews"
                f"?indexFrom=0&pageSize=10&keyword={ticker}"
            )
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                data = r.json()
                for item in (data.get("ResultList") or [])[:max_berita]:
                    berita.append({
                        "judul":  item.get("Title", ""),
                        "waktu":  item.get("NewsDate", "")[:10],
                        "sumber": "IDX",
                    })
        except Exception:
            pass

    # Fallback — Google News RSS (tidak butuh BS4)
    if len(berita) < 2:
        try:
            url = (
                f"https://news.google.com/rss/search"
                f"?q={ticker}+saham+IDX&hl=id&gl=ID&ceid=ID:id"
            )
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                # Parse RSS manual tanpa library
                items = re.findall(r"<item>(.*?)</item>", r.text, re.DOTALL)
                for item in items[:max_berita]:
                    judul = re.search(r"<title><!\[CDATA\[(.*?)\]\]>|<title>(.*?)</title>", item)
                    tgl   = re.search(r"<pubDate>(.*?)</pubDate>", item)
                    if judul:
                        j = judul.group(1) or judul.group(2) or ""
                        berita.append({
                            "judul":  j.strip(),
                            "waktu":  tgl.group(1)[:16] if tgl else "Hari ini",
                            "sumber": "Google News",
                        })
        except Exception:
            pass

    return berita[:max_berita]


def analisis_sentimen_berita(ticker: str, berita: list) -> dict:
    """
    Analisis sentimen berita menggunakan aturan kata kunci
    (tanpa API eksternal — pure Python, gratis)

    Kata positif  → skor naik
    Kata negatif  → skor turun
    Return: {'skor', 'label', 'positif', 'negatif', 'ringkasan'}
    """
    if not berita:
        return {
            "skor":      0,
            "label":     "Tidak ada berita",
            "positif":   0,
            "negatif":   0,
            "ringkasan": "Tidak ada berita terbaru ditemukan",
            "aman":      True,
        }

    kata_positif = [
        "naik", "menguat", "bullish", "rebound", "koreksi selesai",
        "akuisisi", "dividen", "laba", "profit", "untung", "tumbuh",
        "ekspansi", "rights issue", "buyback", "tender offer",
        "kontrak baru", "proyek", "pendapatan naik", "kinerja baik",
        "rekomendasi beli", "target harga", "upgrade", "outperform",
        "kenaikan", "positif", "optimis", "prospek cerah",
        "IPO anak", "spin-off", "pelunasan utang",
    ]
    kata_negatif = [
        "turun", "melemah", "bearish", "jual", "rugi", "loss",
        "suspensi", "delisting", "bangkrut", "pailit", "kasus",
        "korupsi", "gagal bayar", "utang", "kredit macet",
        "downgrade", "underperform", "rekomendasi jual",
        "kerugian", "defisit", "pembekuan", "gugatan", "denda",
        "penurunan laba", "pendapatan turun", "resmi ditutup",
        "force majeure", "kebakaran", "bencana",
    ]

    skor_total  = 0
    cnt_positif = 0
    cnt_negatif = 0
    berita_positif = []
    berita_negatif = []

    for b in berita:
        judul_lower = b["judul"].lower()
        skor_item   = 0

        for kp in kata_positif:
            if kp in judul_lower:
                skor_item  += 1
                cnt_positif += 1

        for kn in kata_negatif:
            if kn in judul_lower:
                skor_item  -= 1
                cnt_negatif += 1

        skor_total += skor_item
        if skor_item > 0:
            berita_positif.append(b["judul"][:60])
        elif skor_item < 0:
            berita_negatif.append(b["judul"][:60])

    # Normalisasi ke -100..+100
    max_mungkin = len(berita) * 3
    skor_norm   = int((skor_total / max(max_mungkin, 1)) * 100) if berita else 0

    if skor_norm >= 30:
        label, aman = "Sangat Positif ✅", True
    elif skor_norm >= 10:
        label, aman = "Positif 🟢",        True
    elif skor_norm >= -10:
        label, aman = "Netral ⚪",          True
    elif skor_norm >= -30:
        label, aman = "Negatif 🔴",         False
    else:
        label, aman = "Sangat Negatif 🚨",  False

    ringkasan = (
        f"{len(berita)} berita — "
        f"+{cnt_positif} positif / -{cnt_negatif} negatif"
    )

    return {
        "skor":           skor_norm,
        "label":          label,
        "positif":        cnt_positif,
        "negatif":        cnt_negatif,
        "ringkasan":      ringkasan,
        "berita_positif": berita_positif,
        "berita_negatif": berita_negatif,
        "aman":           aman,
        "total_berita":   len(berita),
    }


def ambil_sentimen(ticker: str) -> dict:
    """Wrapper: scrape + analisis sentimen untuk satu ticker"""
    if not HAS_REQUESTS:
        return {
            "skor": 0, "label": "Tidak bisa cek (install requests)",
            "ringkasan": "-", "aman": True,
            "berita_positif": [], "berita_negatif": [],
            "total_berita": 0,
        }
    berita = scrape_berita_idx(ticker)
    return analisis_sentimen_berita(ticker, berita)


# ═══════════════════════════════════════════════════════════════
# TELEGRAM NOTIFIKASI
# ═══════════════════════════════════════════════════════════════

def telegram_kirim(pesan: str) -> bool:
    """
    Kirim pesan ke Telegram via Bot API
    Return True jika berhasil, False jika gagal
    """
    token   = CONFIG.get("TELEGRAM_TOKEN", "")
    chat_id = CONFIG.get("TELEGRAM_CHAT_ID", "")

    if not HAS_REQUESTS:
        print(f"  {Fore.RED}❌ Library 'requests' tidak ada. Install: pip install requests{Style.RESET_ALL}")
        return False

    if "ISI_" in token or not token:
        print(f"  {Fore.YELLOW}⚠️  Telegram belum dikonfigurasi. Isi TELEGRAM_TOKEN di CONFIG.{Style.RESET_ALL}")
        return False

    try:
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id":    chat_id,
            "text":       pesan,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            return True
        else:
            print(f"  {Fore.RED}❌ Telegram error: {r.status_code} — {r.text[:100]}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"  {Fore.RED}❌ Telegram gagal: {e}{Style.RESET_ALL}")
        return False


def format_pesan_telegram(results: list, mode: str,
                           sentimen_cache: dict = None) -> str:
    """Format hasil screener jadi pesan Telegram yang rapi"""
    top3 = sorted(results, key=lambda x: x["score"], reverse=True)[:3]
    tgl  = datetime.now().strftime("%d %b %Y %H:%M WIB")

    if not results:
        if not CONFIG.get("NOTIF_KOSONG"):
            return ""
        return (
            f"📊 <b>BSJP Screener — {tgl}</b>\n"
            f"Mode: {mode.upper()}\n\n"
            f"⚠️ Tidak ada saham lolos filter hari ini.\n"
            f"Coba jalankan manual dengan mode AGGRESSIVE."
        )

    baris = [
        f"📊 <b>BSJP Screener — {tgl}</b>",
        f"Mode: {mode.upper()} | {len(results)} saham lolos\n",
        f"⭐ <b>TOP 3 PICKS HARI INI:</b>\n",
    ]

    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(top3):
        sentimen = sentimen_cache.get(r["ticker"]) if sentimen_cache else None
        sent_txt = f" | Berita: {sentimen['label']}" if sentimen else ""

        baris.append(
            f"{medals[i]} <b>{r['ticker']}</b> [{r['sektor']}]\n"
            f"   Score: {r['score']} | Close: {fmt_h(r['close'])} "
            f"| Chg: +{r['chg']:.2f}%\n"
            f"   VSpike: {r['vspike']:.0f}% | RSI: {r['rsi']:.1f} "
            f"| {r['macd']['label']}\n"
            f"   Est besok: {fmt_h(r['range']['target_low'])} – "
            f"{fmt_h(r['range']['target_mid'])} – "
            f"{fmt_h(r['range']['target_high'])} "
            f"({r['range']['arah']} ~{r['range']['confidence']}%)"
            f"{sent_txt}\n"
        )
        if r["candle"]["ada_bullish"]:
            baris.append(f"   🕯️ Candle: {r['candle']['label']}\n")

    # Ringkasan sektor dominan
    sektor_count = {}
    for r in results:
        sektor_count[r["sektor"]] = sektor_count.get(r["sektor"], 0) + 1
    dom = max(sektor_count, key=sektor_count.get)
    if sektor_count[dom] >= 3:
        baris.append(f"\n🏦 Sektor dominan: <b>{dom}</b> ({sektor_count[dom]} saham)")

    baris.append(f"\n⚠️ <i>Bukan rekomendasi investasi. Riset mandiri!</i>")
    return "\n".join(baris)


def kirim_notif_telegram(results: list, mode: str,
                          sentimen_cache: dict = None):
    """Kirim hasil screener ke Telegram"""
    pesan = format_pesan_telegram(results, mode, sentimen_cache)
    if not pesan:
        return
    ok = telegram_kirim(pesan)
    if ok:
        print(f"  {Fore.GREEN}✅ Notifikasi terkirim ke Telegram!{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}❌ Notifikasi Telegram gagal dikirim.{Style.RESET_ALL}")


def test_telegram():
    """Test koneksi Telegram — kirim pesan percobaan"""
    print(f"\n  {Fore.YELLOW}Mengirim pesan test ke Telegram...{Style.RESET_ALL}")
    ok = telegram_kirim(
        f"✅ <b>BSJP Screener v6.0</b>\n\n"
        f"Koneksi Telegram berhasil!\n"
        f"Bot siap mengirim sinyal BSJP setiap jam "
        f"{CONFIG['JADWAL_JAM']} WIB.\n\n"
        f"<i>{datetime.now().strftime('%d %b %Y %H:%M WIB')}</i>"
    )
    if ok:
        print(f"  {Fore.GREEN}✅ Test berhasil! Cek Telegram kamu.{Style.RESET_ALL}\n")
    else:
        print(f"  {Fore.RED}❌ Test gagal. Periksa TOKEN dan CHAT_ID di CONFIG.{Style.RESET_ALL}\n")
    return ok


# ═══════════════════════════════════════════════════════════════
# AUTO-SCHEDULER
# ═══════════════════════════════════════════════════════════════

def jalankan_screening_otomatis():
    """
    Fungsi yang dipanggil scheduler setiap hari jam 15.20 WIB
    Scan → analisis sentimen → kirim Telegram
    """
    print(f"\n{Fore.CYAN}{'─'*60}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}{Style.BRIGHT}⏰ AUTO-SCAN dimulai — {datetime.now().strftime('%d %b %Y %H:%M WIB')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─'*60}{Style.RESET_ALL}\n")

    mode = CONFIG.get("AUTO_MODE", "normal")

    # Kirim notif "sedang scanning" ke Telegram dulu
    telegram_kirim(
        f"🔍 <b>BSJP Auto-Scan dimulai</b>\n"
        f"{datetime.now().strftime('%d %b %Y %H:%M WIB')}\n"
        f"Mode: {mode.upper()} | Scanning {len(WATCHLIST)} saham...\n"
        f"<i>Hasil akan dikirim dalam ~3-5 menit</i>"
    )

    # Scan semua saham
    results = []
    for idx, ticker in enumerate(WATCHLIST):
        print_progress(idx+1, len(WATCHLIST), ticker)
        try:
            r = analisis_saham(ticker, mode)
            if r:
                results.append(r)
        except Exception:
            pass
        time.sleep(CONFIG["REQUEST_DELAY"])

    print(f"\r  Scan selesai! {len(results)} lolos dari {len(WATCHLIST)}{' '*30}")

    # Analisis sentimen untuk top 5
    sentimen_cache = {}
    if HAS_REQUESTS and results:
        top5 = sorted(results, key=lambda x: x["score"], reverse=True)[:5]
        print(f"  {Fore.YELLOW}Mengambil sentimen berita top 5...{Style.RESET_ALL}")
        for r in top5:
            sentimen_cache[r["ticker"]] = ambil_sentimen(r["ticker"])
            time.sleep(1.5)

    # Tampilkan di terminal
    print_results(results, mode)
    print_top3(results)
    simpan_csv(results, mode)

    # Kirim ke Telegram
    kirim_notif_telegram(results, mode, sentimen_cache)

    print(f"\n  {Fore.GREEN}✅ Auto-scan selesai. Menunggu jadwal berikutnya...{Style.RESET_ALL}\n")


def mulai_scheduler():
    """
    Jalankan auto-scheduler
    Screener akan berjalan otomatis setiap hari di jam yang dikonfigurasi
    """
    if not HAS_SCHEDULE:
        print(f"  {Fore.RED}❌ Library 'schedule' tidak ada. Install: pip install schedule{Style.RESET_ALL}")
        return

    jadwal = CONFIG.get("JADWAL_JAM", "15:20")

    print(f"\n{Fore.CYAN}{'═'*60}{Style.RESET_ALL}")
    print(f"  {Style.BRIGHT}🤖 BSJP AUTO-SCHEDULER AKTIF{Style.RESET_ALL}")
    print(f"  Screener akan otomatis berjalan setiap hari jam {Fore.GREEN}{jadwal} WIB{Style.RESET_ALL}")
    print(f"  Hasil langsung dikirim ke Telegram kamu")
    print(f"  Tekan Ctrl+C untuk menghentikan")
    print(f"{Fore.CYAN}{'═'*60}{Style.RESET_ALL}\n")

    # Test koneksi Telegram sebelum mulai
    print(f"  Mengecek koneksi Telegram...")
    test_telegram()

    # Jadwalkan screening harian
    schedule.every().day.at(jadwal).do(jalankan_screening_otomatis)

    print(f"  {Fore.GREEN}✅ Scheduler aktif — menunggu jam {jadwal} WIB...{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}  (Hari ini: {datetime.now().strftime('%d %b %Y')}){Style.RESET_ALL}\n")

    # Loop utama scheduler
    try:
        while True:
            schedule.run_pending()
            # Tampilkan countdown setiap 5 menit
            now      = datetime.now()
            jam, mnt = map(int, jadwal.split(":"))
            target   = now.replace(hour=jam, minute=mnt, second=0, microsecond=0)
            if target < now:
                import datetime as dt
                target = target + dt.timedelta(days=1)
            sisa_mnt = int((target - now).total_seconds() / 60)
            print(
                f"\r  ⏳ Jadwal berikutnya: {jadwal} WIB "
                f"(sisa ~{sisa_mnt} menit) — {now.strftime('%H:%M:%S')}",
                end="", flush=True
            )
            time.sleep(60)
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}Scheduler dihentikan.{Style.RESET_ALL}\n")


def ambil_data(ticker):
    try:
        df = yf.Ticker(f"{ticker}.JK").history(period="6mo", auto_adjust=True)
        return df if df is not None and len(df) >= 35 else None
    except Exception:
        return None


def analisis_saham(ticker, mode):
    df = ambil_data(ticker)
    if df is None:
        return None

    closes  = df["Close"]
    volumes = df["Volume"]
    close   = round(float(closes.iloc[-1]), 0)
    vol     = float(volumes.iloc[-1])

    vspike   = hitung_vspike(volumes)
    rsi      = hitung_rsi(closes)
    chg      = hitung_chg(closes)
    atr      = hitung_atr(df)
    sup, res = hitung_sr(df)
    macd     = hitung_macd(closes)
    bb       = hitung_bollinger(closes)
    vol_arah = hitung_arah_volume(df)
    candle   = deteksi_candlestick(df)          # ← NEW v5.0

    # Filter dasar
    if vol < CONFIG["MIN_VOLUME"]:  return None
    if chg < CONFIG["CHG_MIN"]:     return None

    rsi_max = {"safe":60,"normal":65,"aggressive":70}[mode]
    vs_min  = {"safe":150,"normal":100,"aggressive":50}[mode]

    if rsi > rsi_max or rsi < CONFIG["RSI_MIN"]: return None
    if vspike < vs_min * 0.5:                    return None
    if mode == "safe" and chg > CONFIG["SAFE_CHG_MAX"]: return None

    # ── Filter MACD ────────────────────────────────────────────
    # SAFE   : tolak semua bearish (kuat maupun biasa)
    # NORMAL : tolak bearish kuat saja — FIX kasus BUMI!
    # AGGR   : tidak ada filter MACD (semua boleh masuk)
    if mode == "safe"   and macd["status"] in ("BEARISH", "BEARISH_STRONG"): return None
    if mode == "normal" and macd["status"] == "BEARISH_STRONG":              return None

    if mode in ("safe", "normal") and vol_arah["distribusi_hari_ini"]: return None
    if mode == "safe" and not vol_arah["aman"]: return None

    score  = hitung_score(vspike, rsi, chg, macd, bb, vol_arah, candle, mode)
    signal = get_signal(score)

    # Hint — prioritas dari sinyal terkuat
    hint = "-"
    if vol_arah["distribusi_hari_ini"]:        hint = "DISTRIB🚨"
    elif candle["ada_bullish"] and macd["status"] == "GOLDEN_CROSS":
                                               hint = "GOLDEN+CANDLE💎"
    elif macd["status"] == "GOLDEN_CROSS":     hint = "GOLDEN✨"
    elif candle["pola"] and "Morning Star ⭐" in candle["pola"]:
                                               hint = "MORNING STAR⭐"
    elif candle["pola"] and "3 White Soldiers 🪖" in candle["pola"]:
                                               hint = "3 SOLDIERS🪖"
    elif candle["pola"] and "Bull.Engulfing 🟢" in candle["pola"]:
                                               hint = "ENGULFING🟢"
    elif bb["status"] == "BREAKOUT_UP":        hint = "BREAKOUT🚀"
    elif bb["status"] == "SQUEEZE":            hint = "SQUEEZE⚡"
    elif candle["ada_bullish"] and vol_arah["status"] == "AKUMULASI_KUAT":
                                               hint = "AKUM+CANDLE💎"
    elif vspike >= 200 and chg >= 10:          hint = "MOMO🔥"
    elif candle["ada_bullish"]:                hint = candle["pola"][0] if candle["pola"] else "-"
    elif rsi < 40 and chg > 3:                 hint = "AKUMULASI"

    sektor = SEKTOR.get(ticker, "Lainnya")
    rng    = hitung_range_besok(close, atr, vspike, rsi, chg, macd, bb)

    return {
        "ticker":   ticker,   "sektor":  sektor,
        "close":    close,    "chg":     chg,
        "volume":   vol,      "vspike":  vspike,
        "rsi":      rsi,      "atr":     atr,
        "support":  sup,      "resistance": res,
        "macd":     macd,     "bb":      bb,
        "vol_arah": vol_arah, "candle":  candle,   # ← NEW v5.0
        "score":    score,    "signal":  signal,
        "hint":     hint,     "range":   rng,
    }

# ═══════════════════════════════════════════════════════════════
# TAMPILAN
# ═══════════════════════════════════════════════════════════════

def print_header():
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*74}")
    print(f"  BSJP SCREENER v4.0 — IHSG  |  MACD + BB + Sektor + Arah Volume")
    print(f"  {datetime.now().strftime('%d %B %Y, %H:%M WIB')}  |  Watchlist: {len(WATCHLIST)} saham")
    print(f"{'═'*74}{Style.RESET_ALL}")
    wt = cek_waktu_scan()
    if wt["warna"] == "GREEN":
        print(f"\n  {Fore.GREEN}{Style.BRIGHT}✅ {wt['label']}{Style.RESET_ALL}\n")
    elif wt["warna"] == "YELLOW":
        print(f"\n  {Fore.YELLOW}{Style.BRIGHT}⚠️  {wt['label']}{Style.RESET_ALL}\n")
    else:
        print(f"\n  {Fore.RED}{Style.BRIGHT}{'─'*70}")
        print(f"  🚨 PERINGATAN WAKTU SCAN!")
        print(f"  {wt['label']}")
        print(f"  Data yang kamu lihat BUKAN harga final hari ini!")
        print(f"  Kasus PTPP bisa terulang — VSpike tinggi tapi harga balik turun.")
        print(f"  Tunggu jam 15.15 WIB untuk hasil yang akurat.")
        print(f"  {'─'*70}{Style.RESET_ALL}\n")


def print_progress(cur, total, ticker):
    pct = int(cur / total * 42)
    bar = "█" * pct + "░" * (42 - pct)
    print(f"\r  [{bar}] {cur}/{total} {ticker:<8}", end="", flush=True)


def print_results(results, mode):
    if not results:
        print(f"\n{Fore.RED}  Tidak ada saham lolos filter. Coba mode aggressive.{Style.RESET_ALL}\n")
        return
    top = sorted(results, key=lambda x: x["score"], reverse=True)[:CONFIG["TOP_N"]]
    print(f"\n{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
    print(f"  {Style.BRIGHT}HASIL SCREENER — MODE {mode.upper()}{Style.RESET_ALL}")
    print(f"  {len(results)} lolos → top {len(top)} ditampilkan")
    print(f"{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
    print(f"\n  {'#':<3} {'TICKER':<7} {'CLOSE':>7} {'CHG%':>7} {'VSPIKE':>7} "
          f"{'RSI':>5} {'MACD':<14} {'BB':<22} {'SCORE':>5} HINT")
    print(f"  {'─'*3} {'─'*7} {'─'*7} {'─'*7} {'─'*7} {'─'*5} {'─'*14} {'─'*22} {'─'*5} {'─'*12}")

    for i, r in enumerate(top, 1):
        c = Fore.GREEN+Style.BRIGHT if r["score"]>=75 else (Fore.YELLOW if r["score"]>=55 else Style.DIM)
        cc= Fore.GREEN if r["chg"]>0 else Fore.RED
        hc= Fore.MAGENTA if any(x in r["hint"] for x in ["GOLDEN","BREAKOUT","MOMO","SPIKE"]) else Fore.CYAN
        macd_short = r["macd"]["label"][:13]
        bb_short   = r["bb"]["label"][:21]
        print(
            f"  {c}{i:<3}{Style.RESET_ALL} {c}{r['ticker']:<7}{Style.RESET_ALL} "
            f"{fmt_h(r['close']):>7} {cc}{r['chg']:>+6.2f}%{Style.RESET_ALL} "
            f"{r['vspike']:>6.0f}% {r['rsi']:>5.1f} "
            f"{macd_short:<14} {bb_short:<22} "
            f"{c}{r['score']:>5}{Style.RESET_ALL} {hc}{r['hint']}{Style.RESET_ALL}"
        )


def print_sektor_summary(results):
    """Ringkasan sinyal per sektor"""
    if not results:
        return

    # Hitung per sektor
    sektor_data = {}
    for r in results:
        s = r["sektor"]
        if s not in sektor_data:
            sektor_data[s] = {"count": 0, "scores": [], "tickers": []}
        sektor_data[s]["count"]   += 1
        sektor_data[s]["scores"].append(r["score"])
        sektor_data[s]["tickers"].append(r["ticker"])

    # Sort by count desc
    sorted_s = sorted(sektor_data.items(), key=lambda x: x[1]["count"], reverse=True)

    print(f"\n{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
    print(f"  {Style.BRIGHT}🏦 RINGKASAN PER SEKTOR{Style.RESET_ALL}")
    print(f"  Sektor dengan banyak sinyal = kemungkinan ada sentimen/tema hari ini")
    print(f"{Fore.CYAN}{'═'*74}{Style.RESET_ALL}\n")

    print(f"  {'SEKTOR':<16} {'SINYAL':>7} {'AVG SCORE':>10} {'TOP SAHAM'}")
    print(f"  {'─'*16} {'─'*7} {'─'*10} {'─'*30}")

    for sektor, data in sorted_s[:8]:
        avg_score  = sum(data["scores"]) / len(data["scores"])
        top_tickers= ", ".join(data["tickers"][:4])
        bar_len    = min(data["count"] * 3, 15)
        bar        = "▓" * bar_len

        if data["count"] >= 3:
            color = Fore.GREEN + Style.BRIGHT
            note  = " ← DOMINAN"
        elif data["count"] >= 2:
            color = Fore.YELLOW
            note  = ""
        else:
            color = ""
            note  = ""

        print(
            f"  {color}{sektor:<16}{Style.RESET_ALL} "
            f"{color}{data['count']:>4} saham{Style.RESET_ALL} "
            f"  {avg_score:>6.0f} poin  "
            f"{Fore.CYAN}{top_tickers}{Style.RESET_ALL}"
            f"{Fore.GREEN}{note}{Style.RESET_ALL}"
        )

    # Interpretasi
    if sorted_s:
        dom_sektor = sorted_s[0][0]
        dom_count  = sorted_s[0][1]["count"]
        if dom_count >= 3:
            print(f"\n  {Fore.YELLOW}💡 Sektor {dom_sektor} dominan ({dom_count} saham) "
                  f"— ada potensi sentimen/rotasi sektor hari ini!{Style.RESET_ALL}")


def print_macd_bb_detail(results):
    """Detail MACD, BB, Arah Volume & Candlestick untuk top 5"""
    if not results:
        return
    top5 = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    print(f"\n{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
    print(f"  {Style.BRIGHT}📊 DETAIL INDIKATOR — Top 5{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═'*74}{Style.RESET_ALL}\n")

    for r in top5:
        m   = r["macd"]
        bb  = r["bb"]
        va  = r["vol_arah"]
        cd  = r["candle"]
        mc  = Fore.GREEN if "BULL" in m["status"] or "GOLDEN" in m["status"] else Fore.RED
        bc  = Fore.GREEN if bb["status"] in ["BREAKOUT_UP","SQUEEZE","LOWER_TOUCH","LOWER_ZONE"] else Fore.YELLOW
        vac = Fore.GREEN if va["aman"] else Fore.RED
        cdc = Fore.GREEN + Style.BRIGHT if cd["ada_bullish"] else Fore.WHITE

        print(f"  {Fore.WHITE}{Style.BRIGHT}{r['ticker']}{Style.RESET_ALL}  "
              f"Score:{r['score']}  Close:{fmt_h(r['close'])}  [{r['sektor']}]")
        print(f"    MACD     : {mc}{m['label']}{Style.RESET_ALL}  "
              f"(MACD:{m['macd']:+.3f}  Signal:{m['signal']:+.3f}  Hist:{m['hist']:+.3f})")
        print(f"    BB       : {bc}{bb['label']}{Style.RESET_ALL}  "
              f"(%B:{bb['pct_b']:.0f}  Upper:{fmt_h(bb['upper'])}  "
              f"Mid:{fmt_h(bb['middle'])}  Lower:{fmt_h(bb['lower'])})")
        print(f"    Vol Arah : {vac}{va['label']}{Style.RESET_ALL}  "
              f"(Beli:{va['rasio_beli']:.0f}%  Candle:{va['candle_hari_ini']})")
        if cd["ada_bullish"]:
            print(f"    Candle   : {cdc}{cd['label']}{Style.RESET_ALL}  "
                  f"(Skor candle: +{cd['skor']})")
        else:
            print(f"    Candle   : {Fore.WHITE}Tidak ada pola bullish khusus{Style.RESET_ALL}")
        print(f"    Range    : {Fore.RED}{fmt_h(r['range']['target_low'])}{Style.RESET_ALL} – "
              f"{Fore.YELLOW}{fmt_h(r['range']['target_mid'])}{Style.RESET_ALL} – "
              f"{Fore.GREEN}{fmt_h(r['range']['target_high'])}{Style.RESET_ALL}  "
              f"({r['range']['arah']} ~{r['range']['confidence']}%)\n")


def print_top3(results):
    if not results:
        return
    top3   = sorted(results, key=lambda x: x["score"], reverse=True)[:3]
    medals = ["🥇","🥈","🥉"]

    print(f"\n{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
    print(f"  {Style.BRIGHT}⭐ TOP 3 BSJP PICKS HARI INI{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═'*74}{Style.RESET_ALL}\n")

    for i, r in enumerate(top3):
        rng     = r["range"]
        reasons = []
        if r["vspike"] >= 200:                    reasons.append(f"VSpike {r['vspike']:.0f}%")
        if r["rsi"] < 50:                         reasons.append(f"RSI {r['rsi']:.1f}")
        if r["chg"] >= 5:                         reasons.append(f"Naik +{r['chg']:.2f}%")
        if r["macd"]["status"] == "GOLDEN_CROSS": reasons.append("MACD Golden Cross✨")
        elif "BULL" in r["macd"]["status"]:       reasons.append("MACD Bullish")
        if r["bb"]["status"] == "BREAKOUT_UP":    reasons.append("BB Breakout🚀")
        elif r["bb"]["status"] == "SQUEEZE":      reasons.append("BB Squeeze⚡")
        elif r["bb"]["status"] == "LOWER_TOUCH":  reasons.append("BB Lower Touch")

        print(f"  {medals[i]} {Fore.GREEN}{Style.BRIGHT}{r['ticker']}{Style.RESET_ALL} "
              f"[{r['sektor']}]  Score:{r['score']}  "
              f"Close:{fmt_h(r['close'])}  Chg:{r['chg']:+.2f}%")
        print(f"     Alasan  : {Fore.YELLOW}{' | '.join(reasons) or 'Lolos semua filter'}{Style.RESET_ALL}")
        print(f"     Est besok: {Fore.RED}{fmt_h(rng['target_low'])}{Style.RESET_ALL} – "
              f"{Fore.YELLOW}{fmt_h(rng['target_mid'])}{Style.RESET_ALL} – "
              f"{Fore.GREEN}{fmt_h(rng['target_high'])}{Style.RESET_ALL} "
              f"({rng['arah']} ~{rng['confidence']}%)")
        print(f"     Support  : {fmt_h(r['support'])}  "
              f"Resistance: {fmt_h(r['resistance'])}\n")


def print_top3_dengan_sentimen(results, sentimen_cache=None):
    """Top 3 picks lengkap dengan info sentimen berita"""
    if not results:
        return
    top3   = sorted(results, key=lambda x: x["score"], reverse=True)[:3]
    medals = ["🥇","🥈","🥉"]

    print(f"\n{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
    print(f"  {Style.BRIGHT}⭐ TOP 3 BSJP PICKS HARI INI{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═'*74}{Style.RESET_ALL}\n")

    for i, r in enumerate(top3):
        rng     = r["range"]
        reasons = []
        if r["vspike"] >= 200:                    reasons.append(f"VSpike {r['vspike']:.0f}%")
        if r["rsi"] < 50:                         reasons.append(f"RSI {r['rsi']:.1f}")
        if r["chg"] >= 5:                         reasons.append(f"Naik +{r['chg']:.2f}%")
        if r["macd"]["status"] == "GOLDEN_CROSS": reasons.append("MACD Golden Cross✨")
        elif "BULL" in r["macd"]["status"]:       reasons.append("MACD Bullish")
        if r["bb"]["status"] == "BREAKOUT_UP":    reasons.append("BB Breakout🚀")
        elif r["bb"]["status"] == "SQUEEZE":      reasons.append("BB Squeeze⚡")
        if r["candle"]["ada_bullish"]:            reasons.append(r["candle"]["pola"][0])

        sentimen = sentimen_cache.get(r["ticker"]) if sentimen_cache else None

        print(f"  {medals[i]} {Fore.GREEN}{Style.BRIGHT}{r['ticker']}{Style.RESET_ALL} "
              f"[{r['sektor']}]  Score:{r['score']}  "
              f"Close:{fmt_h(r['close'])}  Chg:{r['chg']:+.2f}%")
        print(f"     Alasan   : {Fore.YELLOW}{' | '.join(reasons) or 'Lolos semua filter'}{Style.RESET_ALL}")
        print(f"     Est besok: {Fore.RED}{fmt_h(rng['target_low'])}{Style.RESET_ALL} – "
              f"{Fore.YELLOW}{fmt_h(rng['target_mid'])}{Style.RESET_ALL} – "
              f"{Fore.GREEN}{fmt_h(rng['target_high'])}{Style.RESET_ALL} "
              f"({rng['arah']} ~{rng['confidence']}%)")
        print(f"     Support  : {fmt_h(r['support'])}  "
              f"Resistance: {fmt_h(r['resistance'])}")

        # Tampilkan sentimen jika ada
        if sentimen:
            sc = Fore.GREEN if sentimen["aman"] else Fore.RED
            print(f"     Berita   : {sc}{sentimen['label']}{Style.RESET_ALL}  "
                  f"({sentimen['ringkasan']})")
            if sentimen["berita_positif"]:
                print(f"     {Fore.GREEN}+ {sentimen['berita_positif'][0][:65]}{Style.RESET_ALL}")
            if sentimen["berita_negatif"]:
                print(f"     {Fore.RED}- {sentimen['berita_negatif'][0][:65]}{Style.RESET_ALL}")
        print()


    print(f"\n{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}{Style.BRIGHT}⚠  DISCLAIMER{Style.RESET_ALL}")
    print(f"  Alat bantu analisis teknikal — BUKAN rekomendasi investasi.")
    print(f"  Estimasi range akurasi ~60-65% untuk arah. Riset mandiri selalu.")
    print(f"  Trading saham mengandung risiko kehilangan modal.")
    print(f"{Fore.CYAN}{'═'*74}{Style.RESET_ALL}\n")


def simpan_csv(results, mode):
    if not results: return
    fn  = f"bsjp_hasil_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    top = sorted(results, key=lambda x: x["score"], reverse=True)[:CONFIG["TOP_N"]]
    rows = [{
        "tanggal": datetime.now().strftime("%Y-%m-%d"),
        "jam": datetime.now().strftime("%H:%M"),
        "mode": mode, "ticker": r["ticker"], "sektor": r["sektor"],
        "close": r["close"], "chg_pct": r["chg"],
        "volume": r["volume"], "vspike_pct": r["vspike"],
        "rsi": r["rsi"], "atr": r["atr"],
        "candle_pola":       " + ".join(r["candle"]["pola"]) if r["candle"]["pola"] else "-",
        "candle_skor":       r["candle"]["skor"],
        "vol_arah_status":   r["vol_arah"]["status"],
        "vol_rasio_beli":    r["vol_arah"]["rasio_beli"],
        "vol_candle":        r["vol_arah"]["candle_hari_ini"],
        "macd_signal": r["macd"]["signal"], "macd_hist": r["macd"]["hist"],
        "bb_status": r["bb"]["status"], "bb_pct_b": r["bb"]["pct_b"],
        "bb_upper": r["bb"]["upper"], "bb_lower": r["bb"]["lower"],
        "support": r["support"], "resistance": r["resistance"],
        "score": r["score"], "signal": r["signal"].strip(), "hint": r["hint"],
        "est_low": r["range"]["target_low"],
        "est_mid": r["range"]["target_mid"],
        "est_high": r["range"]["target_high"],
        "est_gap_pct": r["range"]["gap_pct"],
        "est_arah": r["range"]["arah"],
        "est_confidence": r["range"]["confidence"],
        "actual_open_besok": "", "actual_high_besok": "",
        "actual_close_besok": "", "profit_loss_pct": "",
    } for r in top]
    pd.DataFrame(rows).to_csv(fn, index=False)
    print(f"  {Fore.GREEN}✅ Hasil disimpan: {fn}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}   Isi kolom actual_* besok untuk tracking akurasi{Style.RESET_ALL}\n")


# ═══════════════════════════════════════════════════════════════
# RUN ALL MODES
# ═══════════════════════════════════════════════════════════════

def run_all_modes():
    all_res = {}
    ticker_count = {}
    for mode in ["safe","normal","aggressive"]:
        print(f"\n  {Fore.YELLOW}━━━ Mode: {mode.upper()} ━━━{Style.RESET_ALL}")
        results = []
        for idx, ticker in enumerate(WATCHLIST):
            print_progress(idx+1, len(WATCHLIST), ticker)
            r = analisis_saham(ticker, mode)
            if r:
                results.append(r)
                ticker_count[ticker] = ticker_count.get(ticker, 0) + 1
            time.sleep(CONFIG["REQUEST_DELAY"])
        print(f"\r  Selesai — {len(results)} lolos{' '*40}")
        all_res[mode] = results
        print_results(results, mode)

    # Global picks
    gp = [t for t, c in ticker_count.items() if c >= 3]
    if gp:
        print(f"\n{Fore.CYAN}{'═'*74}{Style.RESET_ALL}")
        print(f"  {Style.BRIGHT}🌟 GLOBAL PICKS — Muncul di semua 3 mode{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'═'*74}{Style.RESET_ALL}\n")
        norm = {r["ticker"]: r for r in all_res.get("normal",[])}
        for t in gp:
            r = norm.get(t)
            if r:
                print(f"  {Fore.GREEN}{Style.BRIGHT}★ {t}{Style.RESET_ALL} [{r['sektor']}]"
                      f"  Score:{r['score']}  MACD:{r['macd']['label']}"
                      f"  BB:{r['bb']['label']}")

    norm = sorted(all_res.get("normal",[]), key=lambda x: x["score"], reverse=True)
    print_sektor_summary(norm)
    print_macd_bb_detail(norm)
    print_top3(norm)
    print_disclaimer()
    simpan_csv(norm, "all_modes")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print_header()

    # Cek waktu — konfirmasi wajib jika jam berbahaya
    wt = cek_waktu_scan()
    if not wt["aman"]:
        print(f"  {Fore.RED}{Style.BRIGHT}⚠  Data belum final! Lanjutkan screening?{Style.RESET_ALL}")
        print(f"  Hasil bisa menyesatkan seperti kasus PTPP\n")
        try:
            jawab = input("  Ketik 'lanjut' untuk tetap scan, atau Enter untuk batal: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            jawab = ""
        if jawab != "lanjut":
            print(f"\n  {Fore.GREEN}✅ Jalankan lagi jam 15.15 WIB untuk hasil akurat.{Style.RESET_ALL}\n")
            sys.exit(0)
        print(f"\n  {Fore.YELLOW}Melanjutkan...{Style.RESET_ALL}\n")

    print(f"  {Style.BRIGHT}Pilih mode:{Style.RESET_ALL}")
    print(f"  1. {Fore.GREEN}SAFE{Style.RESET_ALL}       (VSpike>150%, RSI<60, filter ketat)")
    print(f"  2. {Fore.YELLOW}NORMAL{Style.RESET_ALL}     (VSpike>100%, RSI<65) ← Recommended")
    print(f"  3. {Fore.RED}AGGRESSIVE{Style.RESET_ALL} (VSpike>50%,  RSI<70)")
    print(f"  4. {Fore.CYAN}ALL MODES{Style.RESET_ALL}  (Semua + Global Picks)")
    print(f"  5. {Fore.MAGENTA}AUTO{Style.RESET_ALL}       (Scheduler otomatis + Telegram) ← NEW v6.0")
    print(f"  6. {Fore.WHITE}TEST{Style.RESET_ALL}       (Test koneksi Telegram saja)\n")

    try:
        pilihan = input("  Pilihan [1-6, default=2]: ").strip()
    except (EOFError, KeyboardInterrupt):
        pilihan = "2"

    # Mode 5 — Auto scheduler
    if pilihan == "5":
        mulai_scheduler()
        return

    # Mode 6 — Test Telegram
    if pilihan == "6":
        test_telegram()
        return

    # Mode 4 — All modes
    if pilihan == "4":
        run_all_modes()
        return

    mode  = {"1":"safe","3":"aggressive"}.get(pilihan,"normal")
    color = {"safe":Fore.GREEN,"normal":Fore.YELLOW,"aggressive":Fore.RED}[mode]
    vs    = {"safe":150,"normal":100,"aggressive":50}[mode]
    rm    = {"safe":60,"normal":65,"aggressive":70}[mode]

    # Tanya apakah mau analisis sentimen
    print(f"\n  Mode: {color}{Style.BRIGHT}{mode.upper()}{Style.RESET_ALL}"
          f"  VSpike>={vs}%  RSI:{CONFIG['RSI_MIN']}–{rm}\n")
    try:
        cek_sent = input("  Analisis sentimen berita top 5? (y/n, default=y): ").strip().lower()
        with_sentiment = cek_sent != "n"
    except (EOFError, KeyboardInterrupt):
        with_sentiment = True

    print(f"\n  {Fore.YELLOW}Scanning {len(WATCHLIST)} saham...{Style.RESET_ALL}\n")

    results, errors = [], 0
    for idx, ticker in enumerate(WATCHLIST):
        print_progress(idx+1, len(WATCHLIST), ticker)
        try:
            r = analisis_saham(ticker, mode)
            if r: results.append(r)
        except Exception:
            errors += 1
        time.sleep(CONFIG["REQUEST_DELAY"])

    print(f"\r  Scan selesai! {len(results)} lolos dari {len(WATCHLIST)} ({errors} error){' '*20}")

    # Analisis sentimen untuk top 5
    sentimen_cache = {}
    if with_sentiment and HAS_REQUESTS and results:
        top5 = sorted(results, key=lambda x: x["score"], reverse=True)[:5]
        print(f"\n  {Fore.YELLOW}Mengambil sentimen berita untuk top 5 saham...{Style.RESET_ALL}")
        for r in top5:
            print(f"    Cek berita {r['ticker']}...", end="", flush=True)
            sentimen_cache[r["ticker"]] = ambil_sentimen(r["ticker"])
            sent = sentimen_cache[r["ticker"]]
            print(f" {sent['label']} ({sent['ringkasan']})")
            time.sleep(1.5)

    # Tampilkan hasil
    print_results(results, mode)
    print_sektor_summary(results)
    print_macd_bb_detail(results)
    print_top3_dengan_sentimen(results, sentimen_cache)
    print_disclaimer()
    simpan_csv(results, mode)

    # Tanya kirim Telegram
    if results:
        try:
            kirim = input("\n  Kirim hasil ke Telegram? (y/n, default=y): ").strip().lower()
            if kirim != "n":
                kirim_notif_telegram(results, mode, sentimen_cache)
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}Screener dihentikan.{Style.RESET_ALL}\n")
        sys.exit(0)
