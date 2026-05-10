"""Quick test - scan 3 saham untuk verifikasi whale flow"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Import screener
from bsjp_bot import (
    ambil_idx_stock_summary, analisis_whale_flow, analisis_saham,
    fmt_net_foreign, fmt_h, fmt_vol
)

print("=== Test 1: Fetch IDX Data ===")
idx_cache = ambil_idx_stock_summary()
print(f"Cache size: {len(idx_cache)} saham\n")

print("=== Test 2: Whale Flow Analysis ===")
test_tickers = ["BBCA", "BBRI", "TLKM", "ADRO", "ANTM"]
for t in test_tickers:
    wh = analisis_whale_flow(t, idx_cache)
    net_str = fmt_net_foreign(wh["net_foreign_val"])
    print(f"  {t}: {wh['label']}  Net: {net_str}  F%: {wh['foreign_pct']:.0f}%  Skor: {wh['skor']:+d}")
print()

print("=== Test 3: Full Scan (3 saham) ===")
for t in ["BBRI", "TLKM", "ADRO"]:
    print(f"\n  Scanning {t}...")
    r = analisis_saham(t, "aggressive", idx_cache)
    if r:
        wh = r.get("whale", {})
        print(f"  {t}: Score={r['score']}/135  Signal={r['signal'].strip()}")
        print(f"    Chg={r['chg']:+.2f}%  VSpike={r['vspike']:.0f}%  RSI={r['rsi']:.1f}")
        print(f"    Whale: {wh.get('label','-')}  Hint: {r['hint']}")
    else:
        print(f"  {t}: Tidak lolos filter")

print("\n✅ Test selesai!")
