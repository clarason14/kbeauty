# ✨ K-Beauty Virality to Sales ✨

This project explores how **TikTok virality** influences visibility and sales in the **Korean beauty (K-Beauty)** market.  
We collect TikTok data, clean it into a structured dataset, and analyze engagement trends, brand visibility, and predictive models of virality.

---

## 📂 Repository Structure


```bash
kbeauty-virality-to-sales/
├── analysis/        # Scripts for descriptive stats, brand-level and model analysis
├── scraping/        # TikTok scraping scripts
├── data/
│   └── final/       # Final cleaned dataset used for analysis
├── results/         # Model outputs and figures
├── utils/           # Helper functions
├── requirements.txt # Dependencies
└── .gitignore
```

---

## 🔎 Analysis Modules

### 1. **Descriptive Analysis**
- File: `analysis/tiktok_descriptive_analysis.py`
- Purpose: Exploratory Data Analysis (EDA) on TikTok metrics
- Outputs: Engagement distributions, hashtag patterns, brand-level statistics

### 2. **Brand Analysis**
- File: `analysis/brand_analysis.py`
- Purpose: Quantify mentions and engagement per brand
- Outputs:  
  - `brand_stats.csv`  
  - `brand_video_counts.csv`  
  - `hashtag_stats.csv`  
  - `product_stats.csv`

### 3. **Model Comparison**
- File: `analysis/tiktok_model_comparison.py`
- Purpose: Compare predictive performance across ML models (Logistic Regression, Random Forest, SVM, XGBoost, Neural Networks)
- Outputs:  
  - `results/model_comparison_cv.csv`  
  - Feature importance files for interpretability

---

## 📊 Key Results

### 1. **Brand Mentions vs. Engagement**
- Challenger brands like **TIRTIR** and **Rom&nd** show disproportionately high engagement compared to dominant brands like COSRX.  
- Virality is driven by **community resonance** more than brand size.

### 2. **Feature Importances**
- Top predictors of virality:  
  - Engagement ratio (likes/comments per view)  
  - Co-hashtag diversity  
  - Follower count of video authors  

### 3. **Model Performance**
- **XGBoost** achieved the best trade-off between accuracy and AUC.  
- **Logistic Regression** offered interpretability but lower predictive power.  
- Random Forest lagged behind in generalization.

---

## 🗂 Data

- **Final dataset**:  
  - `data/final/tiktok_with_followers_with_counts.csv`  
  - Cleaned TikTok dataset with video stats, author followers, and hashtag features  

- **Intermediate CSVs** are excluded via `.gitignore` to keep the repo lightweight.

---

## 🚀 Getting Started

Clone the repository:
```bash
git clone https://github.com/clarason14/kbeauty.git
cd kbeauty-virality-to-sales
Install dependencies:

pip install -r requirements.txt
```

Run scraping:
```
python scraping/tiktok_discovery_main.py
```

Run analysis:
```
python analysis/brand_analysis.py
```


📌 Next Steps

Add Amazon reviews & sales data to link virality with actual purchases.

Incorporate Google Trends to track search demand.

Build Streamlit or Power BI dashboards for interactive exploration.
