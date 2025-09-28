import pandas as pd
from pathlib import Path

# --------------------------
# Paths
# --------------------------
DATA_PATH = Path("../data/raw/tiktok_discovery_final.csv")
OUTPUT_PATH = Path("brand_video_counts.csv")  # saved in analysis/

# --------------------------
# Brand Aliases
# --------------------------
BRAND_ALIASES = {
    "COSRX": [
        "cosrx", "cos rx", "코스알엑스","cosrxsnailessence", "snailmucin",
        "6peptideskinbooster", "galactomyces", "cosrxpimplepatch"
    ],
    "Beauty of Joseon": [
        "joseon", "뷰티오브조선", "조선","joseonsunsunscreen", "reliefsun",
        "beautyofjoseonsunsunscreen", "bojsunscreen"
    ],
    "Laneige": [
        "laneige", "라네즈","laneigeglazecraze", "laneigedonutglaze", "laneigelip",
        "laneigeneocushion","laniegecreamskin", "laneigematcha", "laneigetaro"
    ],
    "Innisfree": [
        "innisfree", "이니스프리","innisfreeretinolcica", "wy_rca_challenge",
        "innisfreeindonesia", "retinolcica","innisfreeserum"
    ],
    "TIRTIR": [
        "tirtir", "티르티르","tirtircushion", "tirtircushionfoundation",
        "tirtirmaskfitcushion", "tirtirmaskfitaifilter",
        "tirtirpinkcushion", "tirtirredcushion", "tirtirorangecushion",
        "tirtirsilvercushion","tirtirbeauty"
    ],
    "Banila Co": [
        "banila", "banilaco", "바닐라코", "clean it zero","banila co usa",
        "banilacousa","cleanitzero", "livewithbanila"
    ],
    "Anua": [
        "anua", "아누아","anuaskincare", "anuaskincareset",
        "anuatoner", "anuaheartleaf77","anuaserums", "anuadarkspotcorrectingserum"
    ],
    "Skin1004": [
        "skin1004", "스킨1004","skin1004centella", "centellaskin1004", "skin1004skincare"
    ],
    "Medicube": [
        "medicube", "메디큐브","medicubetonerpad", "medicubetonerpads",
        "medicubetonerpadresults", "medicubebundle", "medicubeskincare",
        "medicubetiktokshop","medicubenightcollagenmask", "medicubezeroporepad",
        "medicubeexosomeshot", "medicubezerofoamcleanser",
        "medicubeglassskin", "medicubeglassskinset"
    ],
    "VT Cosmetics": [
        "vt cosmetics", "브이티","reedleshot", "vtreedleshot",
        "vtcosmeticsreedleshot","reedleshot100", "reedleshot1000"
    ],
    "Fwee": [
        "fwee", "퓌","fweepocketcheekpalette", "fweepuddingpot",
        "fweekeyring", "lippot", "lipandcheek","fweeblurrypuddingpot"
    ],
    "Rom&nd": [
        "romand", "롬앤", "juicylastingtint","volumehacktrio",
        "romandvolumehacktrio", "lineitglossitplumpit","romandlipcombo",
        "romnd", "romndlipgloss","romndglastingmeltingbalm",
        "romndglastingcolorgloss","romndlipmatepencil", "glastingmeltingbalm"
    ],
    "Peripera": ["peripera", "페리페라", "inkvelvet"],
    "Dasique": ["dasique", "데이지크"],
    "Clio": ["clio", "클리오"],
    "Colorgram": ["colorgram", "컬러그램"],
    "Amuse": [
        "amuse", "어뮤즈","amusemakeup", "amuseliptint", "amusejelfittint", "jelfittint",
        "amuseseoulgirl", "wonyoungliptint", "cheektoktok"
    ],
    "Numbuzin": [
        "numbuzin", "넘버즈인","numbuzin no.1", "numbuzin no.3",
        "numbuzin no.5", "numbuzin no.9","numbuzinserum", "numbuzinessence",
        "numbuzinbundle","numbuzinsunscreen", "no.9 essence", "no.9 sunscreen"
    ],
    "Mixsoon": [
        "mixsoon", "믹순", "mixsoonpartner", "centella cleansing foam", "glacier water hyaluronic acid serum"
    ],
    "Arencia": [
        "arencia", "아렌시아", "arenciaskincare", "arenciaredsmoothieserum30",
        "mochicleanser", "ricemochicleanser", "rice mochi cleanser","arenciapartner"
    ],
    "Torriden": ["torriden", "토리든", "torridendiveinserum"],
    "Mediheal": [
        "mediheal", "메디힐","medihealtonerpad", "medihealtonerpads",
        "medihealtonerpadresults","phytoenzymepeeling", "phytoenzymepeelingpads",
        "retinolliftingpad", "vitamidebrighteningpad","madecassosidepad"
    ],
    "Ma:nyo": [
        "manyo", "마녀공장","manyocleansingoil", "manyocleansingwater",
        "manyocleansingfoam", "bifidaampoule"
    ],
}

# --------------------------
# Load dataset
# --------------------------
df = pd.read_csv(DATA_PATH)

df["Caption_norm"] = df["Caption"].fillna("").str.lower()
df["Hashtags_norm"] = df["Hashtags"].fillna("").str.lower()

# --------------------------
# Count unique videos per brand
# --------------------------
brand_counts = {}
for brand, aliases in BRAND_ALIASES.items():
    mask = df.apply(
        lambda row: any(alias.lower() in row["Caption_norm"] or alias.lower() in row["Hashtags_norm"]
                        for alias in aliases),
        axis=1
    )
    brand_counts[brand] = mask.sum()

# Filter out low counts (<5) and sort
result = pd.DataFrame(list(brand_counts.items()), columns=["Brand", "Video_Count"])
result = result[result["Video_Count"] >= 5].sort_values(by="Video_Count", ascending=False)

# --------------------------
# Save results
# --------------------------
print(result)
result.to_csv(OUTPUT_PATH, index=False)
print(f"\nSaved results to {OUTPUT_PATH}")
