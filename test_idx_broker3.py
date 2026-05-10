"""Test IDX - find per-stock broker detail endpoint"""
from curl_cffi import requests as cf_requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-broker/",
    "Accept": "application/json",
}

date = "20260508"

# The stock summary already has ForeignBuy / ForeignSell!
# Let's get specific stocks we care about
print("=== Stock Summary for key stocks ===")
url = "https://www.idx.co.id/primary/TradingSummary/GetStockSummary"
params = {"date": date, "start": "0", "length": "1000"}
r = cf_requests.get(url, headers=headers, params=params, timeout=15, impersonate="chrome")
data = r.json()
stocks = data.get("data", [])

# Filter for our watchlist
targets = ["BBCA", "BBRI", "BMRI", "TLKM", "ASII", "ADRO", "ANTM", "INCO"]
for stock in stocks:
    code = stock.get("StockCode", "")
    if code in targets:
        fb = stock.get("ForeignBuy", 0)
        fs = stock.get("ForeignSell", 0)
        net = fb - fs
        vol = stock.get("Volume", 0)
        foreign_pct = (fb + fs) / vol * 100 if vol > 0 else 0
        print(f"\n{code} ({stock['StockName'][:30]})")
        print(f"  Close: {stock['Close']}  Chg: {stock['Change']}")
        print(f"  Volume: {vol:,.0f}")
        print(f"  Foreign Buy:  {fb:,.0f}")
        print(f"  Foreign Sell: {fs:,.0f}")
        print(f"  Net Foreign:  {net:,.0f} ({'INFLOW' if net > 0 else 'OUTFLOW'})")
        print(f"  Foreign %vol: {foreign_pct:.1f}%")

print(f"\n\nTotal stocks in summary: {len(stocks)}")
