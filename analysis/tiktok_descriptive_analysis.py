import pandas as pd
import re
from pathlib import Path

# --------------------------
# File Paths
# --------------------------
DATA_PATH = Path("../data/raw/tiktok_discovery_final.csv")
CLEANED_PATH = Path("../data/interim/tiktok_cleaned.csv")
BRAND_STATS_PATH = Path("brand_stats.csv")
PRODUCT_STATS_PATH = Path("product_stats.csv")
HASHTAG_STATS_PATH = Path("hashtag_stats.csv")

# --------------------------
# Brand Aliases (broad)
# --------------------------
BRAND_ALIASES = {
    "COSRX": ["cosrx", "코스알엑스", "snail", "pimple", "galactomyces", "peptide", "toner", "serum"],
    "Beauty of Joseon": ["joseon", "뷰티오브조선", "조선", "boj", "reliefsun", "serum", "sunscreen"],
    "Laneige": ["laneige", "라네즈", "lip", "cushion", "cream skin", "sleeping mask"],
    "Innisfree": ["innisfree", "이니스프리", "retinol", "cica", "green tea", "serum", "toner"],
    "TIRTIR": ["tirtir", "티르티르", "maskfit", "cushion"],
    "Banila Co": ["banila", "banilaco", "바닐라코", "cleanitzero", "cleansing"],
    "Anua": ["anua", "아누아", "heartleaf", "toner", "serum"],
    "Skin1004": ["skin1004", "스킨1004", "centella", "toner"],
    "Medicube": ["medicube", "메디큐브", "zeropore", "glassskin", "pad", "mask"],
    "VT Cosmetics": ["vt cosmetics", "브이티", "reedleshot"],
    "Fwee": ["fwee", "퓌", "puddingpot", "palette", "lip"],
    "Rom&nd": ["romand", "롬앤", "tint", "balm", "pencil", "lip combo"],
    "Peripera": ["peripera", "페리페라", "inkvelvet"],
    "Dasique": ["dasique", "데이지크"],
    "Clio": ["clio", "클리오"],
    "Colorgram": ["colorgram", "컬러그램"],
    "Amuse": ["amuse", "어뮤즈", "tint", "cheek"],
    "Numbuzin": ["numbuzin", "넘버즈인", "no1", "no3", "no5", "no9", "sunscreen", "serum"],
    "Mixsoon": ["mixsoon", "믹순", "bean", "cleansing", "foam", "serum"],
    "Arencia": ["arencia", "아렌시아", "smoothie", "mochi", "cleanser"],
    "Torriden": ["torriden", "토리든", "divein", "serum"],
    "Mediheal": ["mediheal", "메디힐", "tonerpad", "peeling", "mask"],
    "Ma:nyo": ["manyo", "마녀공장", "cleansing", "ampoule"]
}

# --------------------------
# Product Aliases (specific only)
# --------------------------
PRODUCT_ALIASES = {
    "COSRX": {
        "Snail Mucin Essence": ["cosrxsnailessence", "snailmucinserum", "snail96"],
        "Pimple Patch": ["cosrxpimplepatch"],
        "Galactomyces Essence": ["cosrxgalactomyces", "galactomycesserum", "essence"],
        "6 Peptide Booster": ["6peptideskinbooster", "cosrx6peptide"],
        "Retinol/Retinal Serums": ["retinolserum", "retinalserum", "serumviral", "overnightserum"],
        "Vitamin C Serum": ["vitamincserum"]
    },
    "Beauty of Joseon": {
        "Relief Sun": [
            "bojsunscreen", "beautyofjoseonsunsunsunscreen", "bojreliefsun",
            "koreansunscreen", "sunscreenviral", "spf", "koreanspf"
        ],
        "Glow Serum": ["bojglowserum"],
        "Calming Serum": ["bojcalmingserum"]
    },
    "Laneige": {
        "Lip Sleeping Mask": ["laneigelipmask", "laneigeglazecraze", "laneigedonutglaze"],
        "Neo Cushion": ["laneigeneocushion", "cushionfoundation"],
        "Cream Skin": ["laneigecreamskin"],
        "Water Sleeping Mask": ["watersleepingmask"],
        "Lip Products": ["lipgloss", "lipcombo", "liptint", "koreanliptint", "lipcare"],
        "Gel Creams": ["gelcream"]
    },
    "Innisfree": {
        "Retinol Cica Serum": ["innisfreeretinolcica", "retinolcicaserum", "retinol"],
        "Green Tea Serum": ["greenteaserum"],
        "Serums": ["koreanserum", "serums"]
    },
    "TIRTIR": {
        "Mask Fit Cushion": ["tirtircushionfoundation", "maskfitcushion"]
    },
    "Banila Co": {
        "Clean It Zero": ["cleanitzero", "banilacleanitzero"],
        "Double Cleansing": ["doublecleansing", "cleansingoil", "cleanser", "cleansers", "oilcleanser"]
    },
    "Anua": {
        "Heartleaf Toner": ["anuaheartleaf77", "anuatoner77", "anuatoner", "koreantoner", "toners"],
        "Dark Spot Serum": ["anuadarkspotcorrectingserum", "anuadarkspotserum"],
        "Cleansing Oil": ["anuacleansingoil"],
        "Azelaic Acid Serum": ["anuaazelaicacidserum"],
        "TxA Serum": ["txaserum"]
    },
    "Skin1004": {
        "Centella Toner": ["skin1004centella", "centellaskin1004"],
        "Centella Ampoule": ["skin1004centellaampoule", "centellaampoule"]
    },
    "Medicube": {
        "Zero Pore Pad": ["zeroporepad", "medicubetonerpad", "tonerpad", "tonerpads"],
        "Exosome Shot": ["exosomeshot"],
        "Night Collagen Mask": [
            "nightcollagenmask", "collagenmask", "sheetmask", "facemask", "koreanfacemask", "ricemask", "claymask"
        ],
        "Glass Skin Line": ["glassskin", "medicube"]
    },
    "VT Cosmetics": {
        "Reedle Shot": ["reedleshot100", "reedleshot1000"]
    },
    "Fwee": {
        "Pudding Pot": ["blurrypuddingpot"],
        "Pocket Cheek Palette": ["pocketcheekpalette"]
    },
    "Rom&nd": {
        "Juicy Lasting Tint": ["juicylastingtint"],
        "Glasting Melting Balm": ["glastingmeltingbalm", "glastingcolorgloss"],
        "Lipmate Pencil": ["lipmatepencil"],
        "Lip Combo": ["romandlipcombo", "lipcombo"]
    },
    "Peripera": {
        "Ink Velvet": ["inkvelvet"]
    },
    "Amuse": {
        "Jelly Fit Tint": ["amusejelfittint"],
        "Cheek Toktok": ["cheektoktok"]
    },
    "Numbuzin": {
        "No.3 Serum": ["numbuzinno3"],
        "No.5 Serum": ["numbuzinno5"],
        "No.9 Sunscreen": ["numbuzinno9", "spf"]
    },
    "Mixsoon": {
        "Bean Essence": ["beanessence", "mixsoonbeanessence"],
        "Hyaluronic Acid Serum": ["hyaluronicacidserum"],
        "Soybean Milk Serum": ["soybeanmilkserum"]
    },
    "Arencia": {
        "Red Smoothie Serum": ["redsmoothieserum"],
        "Rice Mochi Cleanser": ["ricemochicleanser", "mochicleanser"]
    },
    "Torriden": {
        "Dive In Serum": ["diveinserum"]
    },
    "Mediheal": {
        "Madecassoside Pad": ["madecassosidepad"],
        "Retinol Lifting Pad": ["retinolliftingpad"],
        "Other Masks": ["sheetmask", "facemask", "koreanfacemask", "ricemask", "claymask"]
    },
    "Ma:nyo": {
        "Bifida Ampoule": ["bifidaampoule", "ampoule"],
        "Cleansing Oil/Water": [
            "cleansingoil", "oilcleanser", "ricewaterbright", "ricewater",
            "cleansers", "cleanser", "cleansingwater"
        ]
    },
    "Dr. Althea": {
        "345 Cream": ["345cream", "dralthea345cream", "pdrncream"]
    },
    "Round Lab": {
        "Dokdo Cleanser": ["roundlabdokdo", "dokdocleanser", "roundlabdokdocleanser"],
        "Birch Juice Sunscreen": ["roundlabbirchjuice", "roundlabsunscreen", "roundlabspf", "koreanspf"],
        "Round Lab Skincare": ["roundlab", "roundlabskincare"]
    }
}


# --------------------------
# Helpers
# --------------------------
def normalize_text(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def find_brand(row):
    for brand, aliases in BRAND_ALIASES.items():
        for alias in aliases:
            if alias in row["Caption_norm"] or alias in row["Hashtags_norm"]:
                return brand
    return None

def find_product(row, brand):
    if not brand:
        return None

    caption = row["Caption_clean"]
    hashtags = row["Hashtags_clean"]

    # Check specific product aliases
    for product_name, aliases in PRODUCT_ALIASES.get(brand, {}).items():
        for alias in aliases:
            if alias in caption or alias in hashtags:
                return product_name

    # Fallback to generic product bucket
    if "toner" in caption or "toner" in hashtags:
        return f"{brand} – Toner"
    if "serum" in caption or "serum" in hashtags:
        return f"{brand} – Serum"
    if "mask" in caption or "mask" in hashtags:
        return f"{brand} – Mask"
    if "sunscreen" in caption or "sunscreen" in hashtags or "spf" in hashtags:
        return f"{brand} – Sunscreen"
    if "cushion" in caption or "cushion" in hashtags or "foundation" in hashtags:
        return f"{brand} – Cushion"

    return f"{brand} – Other"

def inspect_other_hashtags(df, brand_aliases, top_n=30):
    """
    Look inside 'Other' product rows and suggest brand mapping for frequent hashtags.
    """
    other_rows = df[df["Product"].str.contains("Other", na=False)]

    other_hashtags = []
    for row in other_rows["Hashtags_norm"].dropna():
        for tag in str(row).split(","):
            tag = tag.strip().lower()
            if tag:
                other_hashtags.append(tag)

    counts = pd.Series(other_hashtags).value_counts().reset_index()
    counts.columns = ["Hashtag", "Count"]

    # Try to suggest brands
    suggestions = []
    for hashtag in counts["Hashtag"]:
        matched_brand = None
        for brand, aliases in brand_aliases.items():
            for alias in aliases:
                if alias in hashtag:
                    matched_brand = brand
                    break
            if matched_brand:
                break
        suggestions.append(matched_brand if matched_brand else "Unknown")

    counts["Suggested_Brand"] = suggestions
    return counts.head(top_n)


# --------------------------
# Load + Prep
# --------------------------
df = pd.read_csv(DATA_PATH)

df["Caption_norm"] = df["Caption"].fillna("").str.lower()
df["Hashtags_norm"] = df["Hashtags"].fillna("").str.lower()
df["Caption_clean"] = df["Caption"].fillna("").apply(normalize_text)
df["Hashtags_clean"] = df["Hashtags"].fillna("").apply(normalize_text)

df["Engagement"] = df["Like_Count"] + df["Comment_Count"].fillna(0) + df["Share_Count"].fillna(0)
df["Share_Like_Ratio"] = df["Share_Count"] / df["Like_Count"].replace(0, pd.NA)
df["Comment_Like_Ratio"] = df["Comment_Count"] / df["Like_Count"].replace(0, pd.NA)

df["Brand"] = df.apply(find_brand, axis=1)
df["Product"] = df.apply(lambda row: find_product(row, row["Brand"]), axis=1)

df.to_csv(CLEANED_PATH, index=False)

# --------------------------
# Brand-level stats
# --------------------------
brand_stats = df.groupby("Brand").agg(
    Videos=("Video_ID", "count"),
    Avg_Likes=("Like_Count", "mean"),
    Avg_Comments=("Comment_Count", "mean"),
    Avg_Shares=("Share_Count", "mean"),
    Avg_Engagement=("Engagement", "mean"),
    Share_Like_Ratio=("Share_Like_Ratio", "mean"),
    Comment_Like_Ratio=("Comment_Like_Ratio", "mean"),
).reset_index()
brand_stats.to_csv(BRAND_STATS_PATH, index=False)

# --------------------------
# Product-level stats
# --------------------------
product_stats = df.groupby(["Brand", "Product"]).agg(
    Mentions=("Video_ID", "count"),
    Total_Engagement=("Engagement", "sum"),
    Median_Engagement=("Engagement", "median"),
    Engagement_per_Video=("Engagement", "mean")
).reset_index()

product_stats = product_stats.sort_values("Total_Engagement", ascending=False).reset_index(drop=True)
product_stats.to_csv(PRODUCT_STATS_PATH, index=False)

# --------------------------
# Hashtag-level stats
# --------------------------
hashtag_records = []
for row in df["Hashtags_norm"].dropna():
    for tag in str(row).split(","):
        tag = tag.strip()
        if tag:
            hashtag_records.append(tag)

hashtag_counts = pd.Series(hashtag_records).value_counts().reset_index()
hashtag_counts.columns = ["Hashtag", "Count"]
hashtag_counts.to_csv(HASHTAG_STATS_PATH, index=False)

print("Analysis complete. Files saved:")
print(f"- Cleaned dataset: {CLEANED_PATH}")
print(f"- Brand stats: {BRAND_STATS_PATH}")
print(f"- Product stats: {PRODUCT_STATS_PATH}")
print(f"- Hashtag stats: {HASHTAG_STATS_PATH}")
