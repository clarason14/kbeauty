import csv

file = "/Users/clarason/Desktop/kbeauty-virality-to-sales/data/raw/tiktok_discovery.csv"
fixed_file = file  # overwrite same file

rows = []
with open(file, "r", encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f)
    for row in reader:
        rows.append(row)

print(f"Read {len(rows)} rows (may include messy captions).")

# Re-save with strict quoting
with open(fixed_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_ALL)
    writer.writerows(rows)

print(f"Re-saved file with quoting enforced: {fixed_file}")
