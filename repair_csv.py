import pandas as pd

df = pd.read_csv("data/raw/tiktok_discovery_fixed.csv", encoding="utf-8-sig")

# Drop extra unnamed columns
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

# Save cleaned version
df.to_csv("data/raw/tiktok_discovery_clean.csv", index=False, encoding="utf-8-sig")

print(df.shape)
print(df.columns)
