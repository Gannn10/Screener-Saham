"""Fix emoji encoding in whale flow labels for Windows cp1252 compatibility"""
import re

with open(r'd:\web saham\bsjp_bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Map of emoji labels -> ASCII safe labels + telegram labels
replacements = {
    # In analisis_whale_flow function - replace labels  
    '        label   = "\u26a0\ufe0f Retail driven"': 
        '        label   = "[!] Retail driven"\n        label_tg = "\u26a0\ufe0f Retail driven"',
    '        label   = "\U0001f40b\U0001f525 Whale Strong Inflow!"':
        '        label   = "[W++] Whale Strong!"\n        label_tg = "\U0001f40b\U0001f525 Whale Strong Inflow!"',
    '        label   = "\U0001f40b Whale Inflow"':
        '        label   = "[W+] Whale Inflow"\n        label_tg = "\U0001f40b Whale Inflow"',
    '        label   = "\U0001f7e2 Foreign inflow kecil"':
        '        label   = "[+] Inflow kecil"\n        label_tg = "\U0001f7e2 Foreign inflow kecil"',
    '        label   = "\U0001f6a8 Foreign Dump!"':
        '        label   = "[!!] Foreign Dump!"\n        label_tg = "\U0001f6a8 Foreign Dump!"',
    '        label   = "\U0001f534 Foreign Outflow"':
        '        label   = "[-] Foreign Outflow"\n        label_tg = "\U0001f534 Foreign Outflow"',
    '        label   = "\U0001f7e1 Outflow kecil"':
        '        label   = "[-] Outflow kecil"\n        label_tg = "\U0001f7e1 Outflow kecil"',
    '        label   = "\u26aa Netral"':
        '        label   = "[=] Netral"\n        label_tg = "\u26aa Netral"',
}

count = 0
for old, new in replacements.items():
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f"  Replaced: {old[:40]}...")
    else:
        print(f"  NOT FOUND: {old[:40]}...")

# Also add label_tg to the return dict
old_return = '        "label":           label,'
new_return = '        "label":           label,\n        "label_tg":        label_tg,'
if old_return in content:
    content = content.replace(old_return, new_return, 1)
    count += 1
    print("  Added label_tg to return dict")

# Also fix the NO_DATA label
old_nodata = '            "label":        "Data IDX tidak tersedia",'
new_nodata = '            "label":        "Data IDX tidak tersedia",\n            "label_tg":     "Data IDX tidak tersedia",'
if old_nodata in content:
    content = content.replace(old_nodata, new_nodata, 1)
    count += 1
    print("  Fixed NO_DATA label_tg")

# Fix comment with em-dash
old_comment = "        # Foreign terlalu kecil \u2014 retail driven"
new_comment = "        # Foreign terlalu kecil - retail driven"
if old_comment in content:
    content = content.replace(old_comment, new_comment)
    count += 1
    print("  Fixed em-dash in comment")

with open(r'd:\web saham\bsjp_bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone! {count} replacements made.")
