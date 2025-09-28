# deduplicate_tiktok.py
import pandas as pd

def deduplicate_tiktok(input_file, output_file):
    # Load dataset
    df = pd.read_csv(input_file)

    # Drop duplicates based on TikTok_Video_ID, keep first occurrence
    df_nodup = df.drop_duplicates(subset='TikTok_Video_ID', keep='first').copy()

    # Reset Video_ID sequentially (TT0001, TT0002, ...)
    df_nodup = df_nodup.reset_index(drop=True)
    df_nodup['Video_ID'] = [
        f"TT{str(i+1).zfill(4)}" for i in range(len(df_nodup))
    ]

    # Save cleaned dataset
    df_nodup.to_csv(output_file, index=False)
    print(f"Saved deduplicated dataset to {output_file} with {len(df_nodup)} rows.")

if __name__ == "__main__":
    # Example usage
    deduplicate_tiktok(
        "tiktok_discovery_with_dates.csv", 
        "tiktok_discovery_dedup.csv"
    )
