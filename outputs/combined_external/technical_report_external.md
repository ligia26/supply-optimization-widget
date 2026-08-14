# CUEBIT External Intelligence — Technical Appendix

This file contains the detailed explanation of only the decisions where the external layer changed the operational recommendation.

## 2026-06-17 · 368318 · Diesel

**Action:** POSTPONE PURCHASE

| Metric | Operational | Combined |
|---|---:|---:|
| Purchase volume | 10,760 L | 0 L |
| Purchase spend | €15,903.26 | €0.00 |
| Cover days | 14.0 | 8.0 |

Postpone the operational purchase of 10,760 L because buying now did not produce sufficient expected economic advantage. Main external drivers: Crude, Currency, Geopolitics.

- Expected advantage: **€0.00**
- Internal signal: **0.03**
- External signal: **-0.69**
- Combined signal: **-0.30**
- Confidence: **0.60**
- Internal patterns: **P02 streak 1, P07 price percentile 0.00**
- External drivers: **Crude, Currency, Geopolitics**
- News themes: **HORMUZ_RECOVERY**
- Caveats: **Pattern confidence is detection confidence, not validated predictive probability., Internal and external evidence disagree; discretionary volume is penalised.**

## 2026-06-17 · 368318 · Verde

**Action:** POSTPONE PURCHASE

| Metric | Operational | Combined |
|---|---:|---:|
| Purchase volume | 7,719 L | 0 L |
| Purchase spend | €10,682.82 | €0.00 |
| Cover days | 14.0 | 7.0 |

Postpone the operational purchase of 7,719 L because buying now did not produce sufficient expected economic advantage. Main external drivers: Crude, Currency, Geopolitics.

- Expected advantage: **€0.00**
- Internal signal: **0.03**
- External signal: **-0.70**
- Combined signal: **-0.32**
- Confidence: **0.63**
- Internal patterns: **P02 streak 1, P07 price percentile 0.00**
- External drivers: **Crude, Currency, Geopolitics**
- News themes: **HORMUZ_RECOVERY**
- Caveats: **Pattern confidence is detection confidence, not validated predictive probability., Internal and external evidence disagree; discretionary volume is penalised.**

## 2026-06-23 · 368318 · Diesel

**Action:** BUY MORE

| Metric | Operational | Combined |
|---|---:|---:|
| Purchase volume | 12,631 L | 23,391 L |
| Purchase spend | €17,999.12 | €33,332.11 |
| Cover days | 14.0 | 14.0 |

Buy 10,760 L more because the combined internal and external scenario favoured advancing a future purchase. Modelled expected advantage: €205.55. Main external drivers: Crude, Currency.

- Expected advantage: **€205.55**
- Internal signal: **0.22**
- External signal: **-0.28**
- Combined signal: **0.07**
- Confidence: **0.43**
- Internal patterns: **P01 falling, P02 streak 1, P07 price percentile 0.13**
- External drivers: **Crude, Currency**
- Caveats: **Pattern confidence is detection confidence, not validated predictive probability., Internal and external evidence disagree; discretionary volume is penalised.**

## 2026-06-23 · 368318 · Verde

**Action:** BUY MORE

| Metric | Operational | Combined |
|---|---:|---:|
| Purchase volume | 7,248 L | 14,967 L |
| Purchase spend | €9,842.72 | €20,324.84 |
| Cover days | 14.0 | 14.0 |

Buy 7,719 L more because the combined internal and external scenario favoured advancing a future purchase. Modelled expected advantage: €253.01. Main external drivers: Crude, Currency.

- Expected advantage: **€253.01**
- Internal signal: **0.89**
- External signal: **-0.22**
- Combined signal: **0.49**
- Confidence: **0.47**
- Internal patterns: **P02 streak 1, P07 price percentile 0.11**
- External drivers: **Crude, Currency**
- Caveats: **Pattern confidence is detection confidence, not validated predictive probability., Internal and external evidence disagree; discretionary volume is penalised.**

## Interpretation boundary

Historical simulated supplier-spend saving is calculated from prices paid in the replayed strategies.

Modelled expected advantage is used to choose between candidate purchase volumes. It is not added to the historical saving.