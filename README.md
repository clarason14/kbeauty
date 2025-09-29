K-Beauty Virality to Sales

This project analyzes the relationship between TikTok virality and sales signals in the Korean beauty (K-beauty) market. By collecting TikTok data (hashtags, video stats, captions) and combining it with downstream analysis, the goal is to understand how online engagement translates into brand visibility and product performance.

📂 Repository Structure
kbeauty-virality-to-sales/
├── analysis/                  # Scripts for descriptive stats, modeling, brand analysis
├── scraping/                  # TikTok scraping scripts
├── data/final/                # Final dataset used in analysis
├── results/                   # Processed outputs & model evaluation
│   ├── feature_importances_grouped_avg.csv
│   ├── feature_importances_grouped_summary.csv
│   ├── feature_importances_xgboost.csv
│   ├── model_comparison_cv.csv
│   └── figures/               # Visualizations for README + analysis
│       ├── brand_mentions.png
│       ├── engagement_vs_mentions.png
│       └── model_performance.png
├── utils/                     # Helper functions
├── requirements.txt
├── .gitignore
└── README.md

⚙️ Workflow

Data Collection – TikTok scraping for hashtags, captions, stats.

Data Cleaning – Deduplication + enrichment → data/final/tiktok_with_followers_with_counts.csv.

Analysis – Descriptive analysis, brand-level trends, model comparison.

Results – Feature importances, virality predictors, model benchmarks.

🔑 Key Insights

Virality is not just volume of mentions — smaller brands like TIRTIR and Rom&nd punch above their weight compared to giants like COSRX.

Engagement ratios and co-hashtags outperform raw mention counts for predicting virality.

XGBoost and Neural Networks showed stronger performance than baseline models, but Logistic Regression offered more interpretability.

📊 Results & Visuals

1. Brand Mentions vs. Engagement


Smaller challenger brands achieve higher engagement per mention, while dominant brands often show diminishing returns.

2. Feature Importances (XGBoost)


Follower count, co-hashtag diversity, and engagement ratios were the top predictors of virality.

3. Model Comparison


XGBoost achieved the best balance between accuracy and AUC, while Random Forests lagged in generalization.

🚀 Getting Started
git clone https://github.com/clarason14/kbeauty.git
cd kbeauty-virality-to-sales
pip install -r requirements.txt


Run scraping:

python scraping/tiktok_discovery_main.py


Run analysis:

python analysis/brand_analysis.py

📌 Next Steps

Add Amazon reviews & sales data for virality-to-sales linkage.

Incorporate Google Trends for search demand signals.

Deploy Power BI / Streamlit dashboards for interactive exploration.
