"""Test IDX broker summary - per stock endpoints"""
from curl_cffi import requests as cf_requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-broker/",
    "Accept": "application/json",
}

date = "20260508"

# 1. Get full broker summary with more data 
print("=== Full Broker Summary (first 5) ===")
url = "https://www.idx.co.id/primary/TradingSummary/GetBrokerSummary"
params = {"date": date, "start": "0", "length": "5"}
r = cf_requests.get(url, headers=headers, params=params, timeout=15, impersonate="chrome")
data = r.json()
print(f"Total brokers: {data['recordsTotal']}")
for item in data["data"]:
    print(json.dumps(item, indent=2))

# 2. Try getting broker detail per stock - different URL patterns
print("\n=== Test per-stock endpoints ===")
endpoints = [
    "/primary/TradingSummary/GetBrokerSummary?code=BBCA&date={date}",
    "/primary/TradingSummary/GetBrokerSummary?stockCode=BBCA&date={date}",
    "/primary/TradingSummary/GetBrokerSummary?type=stock&code=BBCA&date={date}",
    "/primary/TradingSummary/GetStockSummary?date={date}&start=0&length=5",
]

for ep in endpoints:
    try:
        full_url = "https://www.idx.co.id" + ep.format(date=date)
        r = cf_requests.get(full_url, headers=headers, timeout=15, impersonate="chrome")
        data = r.json()
        total = data.get("recordsTotal", "N/A")
        items = data.get("data", [])
        print(f"\n{ep[:70]}")
        print(f"  status={r.status_code} total={total} items={len(items)}")
        if items:
            print(f"  Keys: {list(items[0].keys())}")
            print(f"  Sample: {json.dumps(items[0], indent=4)}")
    except Exception as e:
        print(f"\n{ep[:70]}")
        print(f"  Error: {e}")
