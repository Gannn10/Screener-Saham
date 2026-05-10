"""Test IDX broker summary API"""
from curl_cffi import requests as cf_requests
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-broker/",
    "Accept": "application/json",
}

# Try different dates
dates = ["20260509", "20260508", "20260507", "20260506", "20260505"]
for d in dates:
    url = "https://www.idx.co.id/primary/TradingSummary/GetBrokerSummary"
    params = {"date": d, "start": "0", "length": "3"}
    try:
        r = cf_requests.get(url, headers=headers, params=params, timeout=15, impersonate="chrome")
        data = r.json()
        total = data.get("recordsTotal", 0)
        items = data.get("data", [])
        print(f"Date {d}: total={total} items={len(items)}")
        if items:
            print(json.dumps(items[0], indent=2))
            break
    except Exception as e:
        print(f"Date {d}: Error {e}")

# Also try stock-specific broker summary
print("\n--- Stock-specific broker (BBCA) ---")
url2 = "https://www.idx.co.id/primary/TradingSummary/GetBrokerTradingSummary"
params2 = {"code": "BBCA", "date": "20260509", "start": "0", "length": "5"}
try:
    r2 = cf_requests.get(url2, headers=headers, params=params2, timeout=15, impersonate="chrome")
    print(f"Status: {r2.status_code}")
    print(r2.text[:500])
except Exception as e:
    print(f"Error: {e}")

# Try alternative endpoint
print("\n--- Alternative endpoint ---")
url3 = "https://www.idx.co.id/primary/StockData/GetBrokerSummary"
params3 = {"code": "BBCA", "date": "20260509", "start": "0", "length": "5"}
try:
    r3 = cf_requests.get(url3, headers=headers, params=params3, timeout=15, impersonate="chrome")
    print(f"Status: {r3.status_code}")
    print(r3.text[:500])
except Exception as e:
    print(f"Error: {e}")
