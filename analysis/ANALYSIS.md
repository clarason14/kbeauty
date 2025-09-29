# Detailed Analysis: K-Beauty Virality-to-Sales

This document provides an in-depth analysis of the K-Beauty virality project, complementing the high-level visuals in the [README.md](../README.md).

---

## 1. Model Performance

We tested five machine learning models (Logistic Regression, Random Forest, SVM, XGBoost, Neural Network) under different virality thresholds (e.g., Top 5%, Top 9%). Metrics include **Accuracy**, **F1**, and **AUC**.

### Cross-Validation Summary (Top 5% threshold)

| Model               | Accuracy | F1   | AUC  |
|----------------------|----------|------|------|
| Logistic Regression  | 0.91     | 0.92 | 0.79 |
| Random Forest        | 0.95     | 0.94 | 0.78 |
| SVM                  | 0.92     | 0.92 | 0.78 |
| XGBoost              | 0.94     | 0.90 | 0.85 |
| Neural Network       | 0.94     | 0.94 | 0.79 |

#### Interpretation
- **Accuracy** is uniformly high, which reflects class imbalance — most videos are *not viral*, so a naïve model can already guess correctly most of the time.  
- **F1 score** is more informative here. Random Forest and Neural Networks balance precision and recall better than Logistic Regression and SVM, showing they can detect true viral cases without too many false alarms.  
- **AUC (ranking ability)** is highest for **XGBoost**, meaning that while it may not maximize F1, it is strongest at separating viral from non-viral videos across thresholds. This makes XGBoost the best choice if we care about ranking videos by “viral potential” rather than a binary yes/no decision.  

> **Key Takeaway:**  
> Viral prediction is not just about raw accuracy. Models like Random Forests are reliable classifiers, but XGBoost offers better *ranking power* — important for prioritizing content in recommendation systems.

#### Visual: Model Comparison
<img src="figures/model_comparison.png" alt="Model Comparison" width="600"/>

---

## 2. Feature Importance

We averaged feature importance across folds and models.

### Top 10 Features

| Feature                  | Importance |
|---------------------------|------------|
| Engagement Rate           | 0.21       |
| Caption Sentiment         | 0.17       |
| Hashtag Diversity         | 0.15       |
| Follower Count            | 0.12       |
| Video Duration            | 0.10       |
| …                         | …          |

#### Interpretation
- **Engagement rate** dominates, which reinforces that virality is not about how many followers you already have, but how intensively audiences interact with the content.  
- **Caption sentiment** shows that emotional resonance matters. Videos with strongly positive or negative sentiment tend to spread more widely than neutral ones.  
- **Hashtag diversity** reflects the ability to break out of an echo chamber. Videos using a mix of niche and mainstream hashtags are more likely to cross into new audiences.  
- **Follower count** is predictive but weaker than engagement and sentiment — big accounts help, but they don’t guarantee virality.  

> **Key Takeaway:**  
> Virality is driven by *content quality and community response*, not just size of the audience. This explains why challenger brands can punch above their weight.

#### Visual: Feature Importances
<img src="figures/feature_importances.png" alt="Top Feature Importances" width="600"/>

---

## 3. Brand-Level Analysis

We compared **brand mentions** (volume) with **average engagement** (effectiveness).

#### Findings
- **Incumbents (e.g., COSRX, Laneige, Medicube):** High volume of mentions but often diluted engagement. These brands dominate conversation but not excitement.  
- **Challengers (e.g., TIRTIR, Rom&nd):** Fewer mentions overall, but outsized engagement. A single viral product launch (e.g., cushion foundations from TIRTIR) can spike disproportionately high visibility.  
- **Virality spikes** are event-driven — not continuous. One product drop can push a challenger into the spotlight temporarily.  

#### Interpretation
- Volume ≠ virality. A brand can dominate conversation yet fail to capture strong interaction.  
- Challenger brands leverage **product novelty** and **community amplification** to achieve bursts of virality.  
- For marketers, this shows that **strategic launches and timing** are as important as sustained brand awareness.  

> **Key Takeaway:**  
> TikTok virality in K-Beauty is less about sustained presence and more about *spikes created by the right product at the right time*.  

#### Visual: Brand Engagement vs Mentions
<img src="figures/brand_scatter.png" alt="Brand Engagement vs Mentions" width="600"/>

---

## 4. Limitations & Next Steps

- **Platform scope:** Current analysis is TikTok-only. Expanding to YouTube, Instagram, and Amazon reviews will validate whether virality generalizes across platforms.  
- **Engagement as proxy:** Engagement is not the same as sales. Future work should measure correlation between TikTok virality and Amazon/retail sales.  
- **Temporal analysis:** Lag effects (e.g., virality today → sales spike in 1–2 weeks) should be modeled with time series approaches.  
- **Broader signals:** Adding Google Trends data could confirm whether online search volume tracks with viral engagement.  

---

## 5. Data & Resources

- Cross-validation results: [model_comparison_cv.csv](../model_comparison_cv.csv)  
- Feature importances: [feature_importances_grouped_avg.csv](../feature_importances_grouped_avg.csv)  
- Brand stats: [brand_stats.csv](../brand_stats.csv)  

