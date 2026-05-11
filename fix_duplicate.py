"""Fix: remove duplicate old whale classification from bsjp_bot.py"""
import os

filepath = os.path.join("d:", os.sep, "web saham", "bsjp_bot.py")

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the line with "def fmt_net_foreign"
fmt_line = None
for i, line in enumerate(lines):
    if "def fmt_net_foreign(val):" in line:
        fmt_line = i
        break

# Find the end of the new return block ("}") before the duplicate
# The new return ends around line 1174 with "    }"
new_return_end = None
for i in range(1170, 1180):
    if i < len(lines) and lines[i].strip() == "}":
        new_return_end = i
        break

if fmt_line and new_return_end:
    print(f"New return ends at line {new_return_end + 1}")
    print(f"fmt_net_foreign starts at line {fmt_line + 1}")
    
    # Keep lines 0..new_return_end (inclusive), then skip to fmt_line
    new_lines = lines[:new_return_end + 1]
    new_lines.append("\n")
    new_lines.append("\n")
    new_lines.extend(lines[fmt_line:])
    
    removed = len(lines) - len(new_lines)
    print(f"Removed {removed} duplicate lines")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print("Done!")
else:
    print(f"Could not find markers: new_return_end={new_return_end}, fmt_line={fmt_line}")
    # Show context
    for i in range(1170, 1240):
        if i < len(lines):
            print(f"  {i+1}: {lines[i].rstrip()[:80]}")
