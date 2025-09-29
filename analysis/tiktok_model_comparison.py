import os
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
from textblob import TextBlob
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

# -----------------------------
# 1. Load data
# -----------------------------
df = pd.read_csv("../data/raw/tiktok_with_followers_with_counts.csv")

# -----------------------------
# 2. Feature engineering (pre-upload only)
# -----------------------------
df["Hashtag_Count"] = df["Hashtags"].fillna("").apply(lambda x: len(str(x).split(",")))
df["Text_All"] = df["Caption"].fillna("") + " " + df["Hashtags"].fillna("").str.replace(",", " ")
df["Sentiment"] = df["Caption"].fillna("").apply(lambda x: TextBlob(str(x)).sentiment.polarity)

df["Upload_Date"] = pd.to_datetime(df["Upload_Date"], errors="coerce", dayfirst=True)
df["DayOfWeek"] = df["Upload_Date"].dt.dayofweek
df["Hour"] = df["Upload_Date"].dt.hour
df["Weekend"] = df["DayOfWeek"].apply(lambda x: 1 if x >= 5 else 0)

# Engagement (for labeling only, not as features)
df["total_engagement"] = df["Like_Count"] + df["Comment_Count"] + df["Share_Count"]

# -----------------------------
# 3. Features (no leakage!)
# -----------------------------
numeric_features = ["Hashtag_Count", "Sentiment", "Author_Followers"]
categorical_features = ["DayOfWeek", "Weekend"]
text_feature = "Text_All"

numeric_transformer = StandardScaler()
categorical_transformer = OneHotEncoder(handle_unknown="ignore")
text_transformer = TfidfVectorizer(
    max_features=1000,
    ngram_range=(1,2),
    stop_words="english"  # remove filler words like "with", "to"
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features),
        ("text", text_transformer, text_feature)
    ]
)

# -----------------------------
# 4. Models
# -----------------------------
def build_models(y):
    scale_pos_weight = (len(y) - y.sum()) / y.sum() if y.sum() > 0 else 1
    return {
        "Logistic Regression": LogisticRegression(max_iter=2000, class_weight="balanced", C=0.8, penalty="l2"),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=20, min_samples_split=10,
            class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "SVM": SVC(probability=True, kernel="linear", class_weight="balanced", C=0.8, random_state=42),
        "XGBoost": xgb.XGBClassifier(
            eval_metric="logloss", scale_pos_weight=scale_pos_weight,
            max_depth=6, min_child_weight=3, subsample=0.8, colsample_bytree=0.8,
            learning_rate=0.1, n_estimators=150, random_state=42, n_jobs=-1
        ),
        "Neural Network": MLPClassifier(
            hidden_layer_sizes=(128, 64), alpha=0.001, learning_rate_init=0.001,
            max_iter=500, early_stopping=True, random_state=42
        )
    }

# -----------------------------
# 5. Evaluation with CV
# -----------------------------
viral_thresholds = [0.95, 0.90, 0.80]  # Top 5%, 10%, 20%
scoring = {"accuracy": "accuracy", "f1": "f1", "roc_auc": "roc_auc"}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

all_results = []

for vt in viral_thresholds:
    viral_cut = df["total_engagement"].quantile(vt)
    df["viral"] = (df["total_engagement"] >= viral_cut).astype(int)

    X = df[numeric_features + categorical_features + [text_feature]]
    y = df["viral"]

    models = build_models(y)

    for name, model in models.items():
        clf = ImbPipeline(steps=[
            ("preprocessor", preprocessor),
            ("smote", SMOTE(random_state=42)),
            ("model", model)
        ])

        cv_results = cross_validate(clf, X, y, cv=cv, scoring=scoring, return_train_score=False)

        result_row = {
            "Threshold": f"Top {int((1-vt)*100)}%",
            "Model": name,
            "Accuracy_mean": round(cv_results["test_accuracy"].mean(), 4),
            "Accuracy_std": round(cv_results["test_accuracy"].std(), 4),
            "F1_mean": round(cv_results["test_f1"].mean(), 4),
            "F1_std": round(cv_results["test_f1"].std(), 4),
            "AUC_mean": round(cv_results["test_roc_auc"].mean(), 4),
            "AUC_std": round(cv_results["test_roc_auc"].std(), 4)
        }
        all_results.append(result_row)

        # Print to terminal
        print("\n" + "="*70)
        print(f"Threshold: {result_row['Threshold']} | Model: {name}")
        print(f"Accuracy: {result_row['Accuracy_mean']} ± {result_row['Accuracy_std']}")
        print(f"F1: {result_row['F1_mean']} ± {result_row['F1_std']}")
        print(f"AUC: {result_row['AUC_mean']} ± {result_row['AUC_std']}")

# Save CV results
results_df = pd.DataFrame(all_results)
print("\nCross-Validation Summary:\n", results_df)
os.makedirs("../results", exist_ok=True)
results_df.to_csv("../results/model_comparison_preupload.csv", index=False)

# -----------------------------
# 6. Grouped Feature Importance (XGBoost, Top 10%)
# -----------------------------
from sklearn.model_selection import train_test_split

# Define viral label (Top 10%)
viral_cut = df["total_engagement"].quantile(0.90)
df["viral"] = (df["total_engagement"] >= viral_cut).astype(int)

X = df[numeric_features + categorical_features + [text_feature]]
y = df["viral"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

xgb_model = xgb.XGBClassifier(
    eval_metric="logloss",
    max_depth=6, min_child_weight=3, subsample=0.8, colsample_bytree=0.8,
    learning_rate=0.1, n_estimators=150, random_state=42, n_jobs=-1
)

clf = ImbPipeline(steps=[
    ("preprocessor", preprocessor),
    ("smote", SMOTE(random_state=42)),
    ("model", xgb_model)
])

clf.fit(X_train, y_train)

# Extract feature importances
xgb_model_fitted = clf.named_steps["model"]
feature_names = clf.named_steps["preprocessor"].get_feature_names_out()
importances = xgb_model_fitted.feature_importances_

feat_imp = pd.DataFrame({"feature": feature_names, "importance": importances})
# -----------------------------
# Grouped Feature Importance (average per feature)
# -----------------------------

# Map features to groups
def map_group(f):
    if "Author_Followers" in f:
        return "Followers"
    elif "Hashtag_Count" in f or f.startswith("text__"):
        return "Hashtags/Text"
    elif "DayOfWeek" in f or "Hour" in f or "Weekend" in f:
        return "Timing"
    elif "Sentiment" in f:
        return "Sentiment"
    else:
        return "Other"

feat_imp["group"] = feat_imp["feature"].apply(map_group)

# Average importance per feature within each group
grouped_imp = (
    feat_imp.groupby("group")["importance"]
    .mean()
    .reset_index()
    .sort_values("importance", ascending=False)
)

# Normalize to percentages
grouped_imp["importance_pct"] = 100 * grouped_imp["importance"] / grouped_imp["importance"].sum()

# Save both detailed + grouped outputs
os.makedirs("../results", exist_ok=True)
feat_imp.to_csv("../results/feature_importances_detailed.csv", index=False)
grouped_imp.to_csv("../results/feature_importances_grouped_avg.csv", index=False)

print("\nGrouped Feature Importance (average per feature, % of total):\n", grouped_imp)
