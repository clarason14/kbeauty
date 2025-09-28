# fix_missing.py
import pandas as pd
import re

def extract_hashtags(text):
    if pd.isna(text):
        return None
    hashtags = re.findall(r"#(\w+)", str(text))
    return ",".join([h.lower() for h in hashtags]) if hashtags else None

def clean_tiktok_data(input_file, output_file):
    # Try utf-8-sig first, fallback to latin1
    try:
        df = pd.read_csv(input_file, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(input_file, encoding="latin1")

    # Fix Share_Count: replace "share" with 0
    df['Share_Count'] = (
        df['Share_Count']
        .astype(str)
        .str.replace(',', '', regex=False)
        .replace('share', '0')
    )
    df['Share_Count'] = pd.to_numeric(df['Share_Count'], errors='coerce')

    # Rebuild Hashtags from Caption if missing
    missing_hashtags = df['Hashtags'].isna()
    df.loc[missing_hashtags, 'Hashtags'] = df.loc[missing_hashtags, 'Caption'].apply(extract_hashtags)

    # Final fill rules
    df['Hashtags'] = df['Hashtags'].fillna("none")
    df['Like_Count'] = df['Like_Count'].fillna(0)
    df['Comment_Count'] = df['Comment_Count'].fillna(0)
    df['Share_Count'] = df['Share_Count'].fillna(0)
    df['Upload_Date'] = df['Upload_Date'].fillna(0)
    df['Author'] = df['Author'].fillna("Unknown")
    df['Caption'] = df['Caption'].fillna("Unknown")

    # Save cleaned dataset
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    # Show confirmation
    print(f"Saved cleaned dataset to {output_file} with {len(df)} rows.")
    print("\nRemaining missing values (should all be 0):")
    print(df.isna().sum())

if __name__ == "__main__":
    clean_tiktok_data(
        "tiktok_discovery_dedup.csv",
        "tiktok_discovery_clean.csv"
    )
