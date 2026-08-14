# CUEBIT purchasing simulation — decision audit

> Same demand, same purchased litres and same closing inventory. The difference is when the fuel is purchased, how much is purchased on each quotation date and which quotation is paid.

## Executive result

| Metric | Operational baseline | CUEBIT | Difference |
|---|---:|---:|---:|
| **Supplier spend** | **€276,396.58** | **€273,940.49** | **€2,456.09 (0.89%)** |
| Litres purchased | 184,786 L | 184,786 L | -0 L |
| Purchase orders | 38 | 29 | 9 |

## How CUEBIT decides

On every quotation date, CUEBIT first calculates the minimum volume required to remain operational. It then generates feasible purchase volumes between that minimum and the usable tank capacity.

Each candidate is evaluated as:

```text
Immediate purchase cost
+ expected future procurement cost
+ holding cost
+ working-capital cost
+ order cost
+ risk adjustment for downside scenarios
= robust objective
```

The feasible candidate with the lowest robust objective is selected. The candidate tables below show the complete comparison used by the optimiser.

## Result by distributor and product

| Distributor | Product | Baseline spend | CUEBIT spend | Saving | Saving % | Baseline orders | CUEBIT orders |
|---|---|---:|---:|---:|---:|---:|---:|
| 368318 | Diesel | €72,284.41 | €71,134.94 | €1,149.47 | 1.59% | 10 | 5 |
| 368318 | Verde | €38,617.43 | €38,023.00 | €594.43 | 1.54% | 11 | 5 |
| 368319 | Diesel | €13,828.33 | €13,828.33 | €0.00 | 0.00% | 1 | 1 |
| 368319 | Verde | €15,396.89 | €15,194.49 | €202.39 | 1.31% | 4 | 4 |
| 368320 | Diesel | €46,314.98 | €46,314.98 | €0.00 | 0.00% | 1 | 1 |
| 368320 | Verde | €26,080.17 | €25,762.23 | €317.94 | 1.22% | 4 | 4 |
| 368321 | Diesel | €16,796.42 | €16,659.11 | €137.31 | 0.82% | 3 | 4 |
| 368321 | Verde | €11,902.08 | €11,902.08 | €0.00 | 0.00% | 1 | 1 |
| 368322 | Diesel | €20,214.33 | €20,214.33 | €0.00 | 0.00% | 1 | 1 |
| 368322 | Verde | €14,961.53 | €14,906.98 | €54.55 | 0.36% | 2 | 3 |

## Decision audit by distributor and product

# 368318 — Diesel

**Economic result:** €1,149.47 saved (1.59%).

**Average purchase price:** €1.51601/L → €1.49190/L.

**Order count:** 10 → 5.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-06-25 | 1,747 L | 608 L | **608 L** | €1.44000/L |
| 2026-06-26 | 0 L | 2,248 L | **2,248 L** | €1.44700/L |
| 2026-06-27 | 0 L | 5,971 L | **5,971 L** | €1.46000/L |
| 2026-06-30 | 0 L | 1,933 L | **1,933 L** | €1.47000/L |
| 2026-07-01 | 0 L | 2,057 L | **2,057 L** | €1.48000/L |
| 2026-07-02 | 0 L | 2,354 L | **2,354 L** | €1.49000/L |
| 2026-07-03 | 0 L | 2,248 L | **2,248 L** | €1.49800/L |
| 2026-07-04 | 0 L | 5,971 L | **5,971 L** | €1.50581/L |
| 2026-07-07 | 0 L | 1,933 L | **1,933 L** | €1.54700/L |
| 2026-07-08 | 0 L | 2,057 L | **22,357 L** | €1.55186/L |

### CUEBIT decision stories

### Decision — 2026-06-17

| Input | Value |
|---|---:|
| Current quotation | €1.47800/L |
| Inventory before purchase | 18,367 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 10,760 L |
| Total purchase selected | **10,760 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P02 streak 1; P07 price percentile 0.00.
- Signal score: +0.031.
- Confidence: 0.600.
- Adjusted signal: +0.019.
- Expected daily quotation change: +0.00028 €/L.
- Observed price percentile: 0%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 8 days | €0.00 | €15,924.17 | €0.00 | €0.00 | €0.00 | €0.00 | **€15,924.17** | Rejected |
| 608 L | 9 days | €898.18 | €15,024.80 | €0.00 | €0.00 | €0.00 | €0.00 | **€15,922.99** | Rejected |
| 2,856 L | 10 days | €4,220.89 | €11,697.73 | €0.00 | €0.00 | €0.00 | €0.00 | **€15,918.62** | Rejected |
| 4,992 L | 11 days | €7,378.78 | €8,535.68 | €0.00 | €0.00 | €0.00 | €0.00 | **€15,914.47** | Rejected |
| 6,793 L | 12 days | €10,040.51 | €5,870.46 | €0.00 | €0.00 | €0.00 | €0.00 | **€15,910.97** | Rejected |
| 8,827 L | 13 days | €13,046.75 | €2,860.27 | €0.00 | €0.00 | €0.00 | €0.00 | **€15,907.02** | Rejected |
| 10,760 L | 14 days | €15,903.26 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€15,903.26** | ✅ Selected |
| 16,633 L | 14 days | €24,583.11 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€24,583.11** | Rejected |

#### Why this candidate won

The optimiser selected **10,760 L** because its robust objective of **€15,903.26** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **8,827 L** with a robust objective of **€15,907.02**, which was **€3.75** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-25 | €1.44000/L | 608 L |
| 2026-06-26 | €1.44700/L | 2,248 L |
| 2026-06-27 | €1.46000/L | 5,971 L |
| 2026-06-30 | €1.47000/L | 1,933 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€20.90**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €15,903.26.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-23

| Input | Value |
|---|---:|
| Current quotation | €1.42500/L |
| Inventory before purchase | 16,496 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 12,631 L |
| Total purchase selected | **12,631 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 falling; P02 streak 1; P07 price percentile 0.13.
- Signal score: +0.222.
- Confidence: 0.600.
- Adjusted signal: +0.133.
- Expected daily quotation change: +0.00200 €/L.
- Observed price percentile: 13%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 8 days | €0.00 | €18,165.09 | €0.00 | €0.00 | €0.00 | €1,407.59 | **€18,165.09** | Rejected |
| 2,057 L | 9 days | €2,931.33 | €15,206.73 | €0.00 | €0.00 | €0.00 | €1,178.35 | **€18,138.06** | Rejected |
| 4,411 L | 10 days | €6,286.19 | €11,820.94 | €0.00 | €0.00 | €0.00 | €915.99 | **€18,107.13** | Rejected |
| 6,659 L | 11 days | €9,489.75 | €8,587.84 | €0.00 | €0.00 | €0.00 | €665.46 | **€18,077.59** | Rejected |
| 8,796 L | 12 days | €12,534.41 | €5,515.11 | €0.00 | €0.00 | €0.00 | €427.36 | **€18,049.51** | Rejected |
| 10,597 L | 13 days | €15,100.69 | €2,925.16 | €0.00 | €0.00 | €0.00 | €226.67 | **€18,025.85** | Rejected |
| 12,631 L | 14 days | €17,999.12 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€17,999.12** | ✅ Selected |
| 18,504 L | 14 days | €26,367.72 | €0.00 | €0.00 | €0.00 | €0.00 | €-0.00 | **€26,367.72** | Rejected |

#### Why this candidate won

The optimiser selected **12,631 L** because its robust objective of **€17,999.12** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **10,597 L** with a robust objective of **€18,025.85**, which was **€26.73** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-25 | €1.44000/L | 608 L |
| 2026-06-26 | €1.44700/L | 2,248 L |
| 2026-06-27 | €1.46000/L | 5,971 L |
| 2026-06-30 | €1.47000/L | 1,933 L |
| 2026-07-01 | €1.48000/L | 1,871 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€165.97**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €17,999.12.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-24

| Input | Value |
|---|---:|
| Current quotation | €1.43200/L |
| Inventory before purchase | 27,195 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 1,933 L |
| Total purchase selected | **1,933 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 2; P07 price percentile 0.22.
- Signal score: +0.861.
- Confidence: 0.633.
- Adjusted signal: +0.545.
- Expected daily quotation change: +0.00763 €/L.
- Observed price percentile: 22%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €2,916.89 | €0.00 | €0.00 | €0.00 | €258.40 | **€2,916.89** | Rejected |
| 1,933 L | 14 days | €2,767.61 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€2,767.61** | ✅ Selected |
| 7,805 L | 14 days | €11,177.31 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€11,177.31** | Rejected |

#### Why this candidate won

The optimiser selected **1,933 L** because its robust objective of **€2,767.61** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€2,916.89**, which was **€149.28** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-25 | €1.44000/L | 608 L |
| 2026-06-26 | €1.44700/L | 1,325 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€149.28**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €2,767.61.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-25

| Input | Value |
|---|---:|
| Current quotation | €1.44000/L |
| Inventory before purchase | 27,070 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 2,057 L |
| Total purchase selected | **2,057 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 3; P07 price percentile 0.32.
- Signal score: +0.806.
- Confidence: 0.667.
- Adjusted signal: +0.537.
- Expected daily quotation change: +0.00699 €/L.
- Observed price percentile: 32%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €3,124.43 | €0.00 | €0.00 | €0.00 | €252.28 | **€3,124.43** | Rejected |
| 2,057 L | 14 days | €2,962.19 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€2,962.19** | ✅ Selected |
| 7,930 L | 14 days | €11,418.88 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€11,418.88** | Rejected |

#### Why this candidate won

The optimiser selected **2,057 L** because its robust objective of **€2,962.19** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€3,124.43**, which was **€162.24** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-26 | €1.44700/L | 2,057 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€162.24**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €2,962.19.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 20,300 L at €1.55186/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368318 — Verde

**Economic result:** €594.43 saved (1.54%).

**Average purchase price:** €1.42052/L → €1.39865/L.

**Order count:** 11 → 5.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-06-24 | 603 L | 541 L | **541 L** | €1.36800/L |
| 2026-06-25 | 0 L | 1,308 L | **1,308 L** | €1.37400/L |
| 2026-06-26 | 0 L | 1,325 L | **1,325 L** | €1.36900/L |
| 2026-06-27 | 0 L | 3,470 L | **3,470 L** | €1.38000/L |
| 2026-06-30 | 0 L | 1,074 L | **1,074 L** | €1.38900/L |
| 2026-07-01 | 0 L | 1,144 L | **1,144 L** | €1.39900/L |
| 2026-07-02 | 0 L | 1,308 L | **1,308 L** | €1.40800/L |
| 2026-07-03 | 0 L | 1,325 L | **1,325 L** | €1.41000/L |
| 2026-07-04 | 0 L | 3,470 L | **3,470 L** | €1.44470/L |
| 2026-07-07 | 0 L | 1,074 L | **1,074 L** | €1.44300/L |
| 2026-07-08 | 0 L | 1,144 L | **11,144 L** | €1.44554/L |

### CUEBIT decision stories

### Decision — 2026-06-17

| Input | Value |
|---|---:|
| Current quotation | €1.38400/L |
| Inventory before purchase | 8,926 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 7,719 L |
| Total purchase selected | **7,719 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P02 streak 1; P07 price percentile 0.00.
- Signal score: +0.031.
- Confidence: 0.600.
- Adjusted signal: +0.019.
- Expected daily quotation change: +0.00026 €/L.
- Observed price percentile: 0%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 7 days | €0.00 | €10,696.81 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,696.81** | Rejected |
| 541 L | 8 days | €748.69 | €9,947.14 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,695.83** | Rejected |
| 1,849 L | 9 days | €2,558.88 | €8,134.58 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,693.46** | Rejected |
| 3,174 L | 10 days | €4,392.97 | €6,298.09 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,691.06** | Rejected |
| 4,427 L | 11 days | €6,126.38 | €4,562.41 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,688.78** | Rejected |
| 5,502 L | 12 days | €7,615.37 | €3,071.46 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,686.83** | Rejected |
| 6,644 L | 13 days | €9,195.99 | €1,488.78 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,684.76** | Rejected |
| 7,719 L | 14 days | €10,682.82 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,682.82** | ✅ Selected |
| 21,074 L | 14 days | €29,166.83 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€29,166.83** | Rejected |

#### Why this candidate won

The optimiser selected **7,719 L** because its robust objective of **€10,682.82** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **6,644 L** with a robust objective of **€10,684.76**, which was **€1.95** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-24 | €1.36800/L | 541 L |
| 2026-06-25 | €1.37400/L | 1,308 L |
| 2026-06-26 | €1.36900/L | 1,325 L |
| 2026-06-27 | €1.38000/L | 3,470 L |
| 2026-06-30 | €1.38900/L | 1,074 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€14.00**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €10,682.82.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-23

| Input | Value |
|---|---:|
| Current quotation | €1.35800/L |
| Inventory before purchase | 9,397 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 7,248 L |
| Total purchase selected | **7,248 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P02 streak 1; P07 price percentile 0.11.
- Signal score: +0.885.
- Confidence: 0.600.
- Adjusted signal: +0.531.
- Expected daily quotation change: +0.00478 €/L.
- Observed price percentile: 11%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 8 days | €0.00 | €10,073.13 | €0.00 | €0.00 | €0.00 | €478.94 | **€10,073.13** | Rejected |
| 1,144 L | 9 days | €1,554.12 | €8,482.63 | €0.00 | €0.00 | €0.00 | €403.32 | **€10,036.75** | Rejected |
| 2,452 L | 10 days | €3,330.30 | €6,664.87 | €0.00 | €0.00 | €0.00 | €316.89 | **€9,995.17** | Rejected |
| 3,778 L | 11 days | €5,129.93 | €4,823.11 | €0.00 | €0.00 | €0.00 | €229.32 | **€9,953.04** | Rejected |
| 5,030 L | 12 days | €6,830.78 | €3,082.45 | €0.00 | €0.00 | €0.00 | €146.56 | **€9,913.23** | Rejected |
| 6,106 L | 13 days | €8,291.80 | €1,587.23 | €0.00 | €0.00 | €0.00 | €75.47 | **€9,879.02** | Rejected |
| 7,248 L | 14 days | €9,842.72 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€9,842.72** | ✅ Selected |
| 20,603 L | 14 days | €27,979.49 | €0.00 | €0.00 | €0.00 | €0.00 | €-0.00 | **€27,979.49** | Rejected |

#### Why this candidate won

The optimiser selected **7,248 L** because its robust objective of **€9,842.72** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **6,106 L** with a robust objective of **€9,879.02**, which was **€36.31** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-24 | €1.36800/L | 541 L |
| 2026-06-25 | €1.37400/L | 1,308 L |
| 2026-06-26 | €1.36900/L | 1,325 L |
| 2026-06-27 | €1.38000/L | 3,470 L |
| 2026-06-30 | €1.38900/L | 603 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€230.42**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €9,842.72.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-24

| Input | Value |
|---|---:|
| Current quotation | €1.36800/L |
| Inventory before purchase | 15,570 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 1,074 L |
| Total purchase selected | **1,074 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 2; P07 price percentile 0.33.
- Signal score: +0.787.
- Confidence: 0.633.
- Adjusted signal: +0.499.
- Expected daily quotation change: +0.00474 €/L.
- Observed price percentile: 33%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €1,519.93 | €0.00 | €0.00 | €0.00 | €101.90 | **€1,519.93** | Rejected |
| 1,074 L | 14 days | €1,469.64 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€1,469.64** | ✅ Selected |
| 14,430 L | 14 days | €19,739.97 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€19,739.97** | Rejected |

#### Why this candidate won

The optimiser selected **1,074 L** because its robust objective of **€1,469.64** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€1,519.93**, which was **€50.29** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-25 | €1.37400/L | 1,074 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€50.29**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €1,469.64.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-25

| Input | Value |
|---|---:|
| Current quotation | €1.37400/L |
| Inventory before purchase | 15,500 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 1,144 L |
| Total purchase selected | **1,144 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 3; P07 price percentile 0.47.
- Signal score: +0.718.
- Confidence: 0.667.
- Adjusted signal: +0.479.
- Expected daily quotation change: +0.00431 €/L.
- Observed price percentile: 47%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €1,625.52 | €0.00 | €0.00 | €0.00 | €98.37 | **€1,625.52** | Rejected |
| 1,144 L | 14 days | €1,572.43 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€1,572.43** | ✅ Selected |
| 14,500 L | 14 days | €19,922.89 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€19,922.89** | Rejected |

#### Why this candidate won

The optimiser selected **1,144 L** because its robust objective of **€1,572.43** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€1,625.52**, which was **€53.09** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-06-26 | €1.36900/L | 1,144 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€53.09**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €1,572.43.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 10,000 L at €1.44554/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368319 — Diesel

**Economic result:** €0.00 saved (0.00%).

**Average purchase price:** €1.55186/L → €1.55186/L.

**Order count:** 1 → 1.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-08 | 1,087 L | 0 L | **8,911 L** | €1.55186/L |

### CUEBIT decision stories

No non-terminal optimisation purchase was made for this distributor/product. The only purchase was the final stock-equalisation adjustment, so the simulation does not demonstrate a timing advantage for this case.

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 8,911 L at €1.55186/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368319 — Verde

**Economic result:** €202.39 saved (1.31%).

**Average purchase price:** €1.44366/L → €1.42468/L.

**Order count:** 4 → 4.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-03 | 133 L | 506 L | **506 L** | €1.41000/L |
| 2026-07-04 | 0 L | 1,338 L | **1,338 L** | €1.44470/L |
| 2026-07-07 | 0 L | 381 L | **381 L** | €1.44300/L |
| 2026-07-08 | 0 L | 440 L | **8,440 L** | €1.44554/L |

### CUEBIT decision stories

### Decision — 2026-06-23

| Input | Value |
|---|---:|
| Current quotation | €1.35800/L |
| Inventory before purchase | 4,719 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 1,844 L |
| Total purchase selected | **1,844 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P02 streak 1; P07 price percentile 0.11.
- Signal score: +0.885.
- Confidence: 0.600.
- Adjusted signal: +0.531.
- Expected daily quotation change: +0.00478 €/L.
- Observed price percentile: 11%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 10 days | €0.00 | €2,562.59 | €0.00 | €0.00 | €0.00 | €121.84 | **€2,562.59** | Rejected |
| 506 L | 11 days | €686.75 | €1,859.76 | €0.00 | €0.00 | €0.00 | €88.43 | **€2,546.51** | Rejected |
| 960 L | 12 days | €1,303.97 | €1,228.09 | €0.00 | €0.00 | €0.00 | €58.39 | **€2,532.06** | Rejected |
| 1,456 L | 13 days | €1,977.90 | €538.39 | €0.00 | €0.00 | €0.00 | €25.60 | **€2,516.28** | Rejected |
| 1,844 L | 14 days | €2,503.97 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€2,503.97** | ✅ Selected |
| 5,281 L | 14 days | €7,171.99 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€7,171.99** | Rejected |

#### Why this candidate won

The optimiser selected **1,844 L** because its robust objective of **€2,503.97** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **1,456 L** with a robust objective of **€2,516.28**, which was **€12.32** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-03 | €1.41000/L | 506 L |
| 2026-07-04 | €1.44470/L | 1,338 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€58.62**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €2,503.97.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-24

| Input | Value |
|---|---:|
| Current quotation | €1.36800/L |
| Inventory before purchase | 6,181 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 381 L |
| Total purchase selected | **381 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 2; P07 price percentile 0.33.
- Signal score: +0.787.
- Confidence: 0.633.
- Adjusted signal: +0.499.
- Expected daily quotation change: +0.00474 €/L.
- Observed price percentile: 33%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €539.30 | €0.00 | €0.00 | €0.00 | €36.16 | **€539.30** | Rejected |
| 381 L | 14 days | €521.46 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€521.46** | ✅ Selected |
| 3,819 L | 14 days | €5,223.85 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€5,223.85** | Rejected |

#### Why this candidate won

The optimiser selected **381 L** because its robust objective of **€521.46** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€539.30**, which was **€17.85** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-03 | €1.41000/L | 381 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€17.85**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €521.46.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-25

| Input | Value |
|---|---:|
| Current quotation | €1.37400/L |
| Inventory before purchase | 6,122 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 440 L |
| Total purchase selected | **440 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 3; P07 price percentile 0.47.
- Signal score: +0.718.
- Confidence: 0.667.
- Adjusted signal: +0.479.
- Expected daily quotation change: +0.00431 €/L.
- Observed price percentile: 47%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €625.16 | €0.00 | €0.00 | €0.00 | €37.83 | **€625.16** | Rejected |
| 440 L | 14 days | €604.75 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€604.75** | ✅ Selected |
| 3,878 L | 14 days | €5,327.77 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€5,327.77** | Rejected |

#### Why this candidate won

The optimiser selected **440 L** because its robust objective of **€604.75** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€625.16**, which was **€20.42** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-03 | €1.41000/L | 440 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€20.42**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €604.75.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 8,000 L at €1.44554/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368320 — Diesel

**Economic result:** €0.00 saved (0.00%).

**Average purchase price:** €1.55186/L → €1.55186/L.

**Order count:** 1 → 1.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-08 | 19,182 L | 0 L | **29,845 L** | €1.55186/L |

### CUEBIT decision stories

No non-terminal optimisation purchase was made for this distributor/product. The only purchase was the final stock-equalisation adjustment, so the simulation does not demonstrate a timing advantage for this case.

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 29,845 L at €1.55186/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368320 — Verde

**Economic result:** €317.94 saved (1.22%).

**Average purchase price:** €1.44461/L → €1.42700/L.

**Order count:** 4 → 4.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-03 | 585 L | 372 L | **372 L** | €1.41000/L |
| 2026-07-04 | 0 L | 2,165 L | **2,165 L** | €1.44470/L |
| 2026-07-07 | 0 L | 697 L | **697 L** | €1.44300/L |
| 2026-07-08 | 0 L | 820 L | **14,820 L** | €1.44554/L |

### CUEBIT decision stories

### Decision — 2026-06-23

| Input | Value |
|---|---:|
| Current quotation | €1.35800/L |
| Inventory before purchase | 8,488 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 2,537 L |
| Total purchase selected | **2,537 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P02 streak 1; P07 price percentile 0.11.
- Signal score: +0.885.
- Confidence: 0.600.
- Adjusted signal: +0.531.
- Expected daily quotation change: +0.00478 €/L.
- Observed price percentile: 11%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 10 days | €0.00 | €3,525.69 | €0.00 | €0.00 | €0.00 | €167.64 | **€3,525.69** | Rejected |
| 372 L | 11 days | €505.30 | €3,008.57 | €0.00 | €0.00 | €0.00 | €143.05 | **€3,513.87** | Rejected |
| 1,226 L | 12 days | €1,665.02 | €1,821.70 | €0.00 | €0.00 | €0.00 | €86.62 | **€3,486.72** | Rejected |
| 1,770 L | 13 days | €2,403.82 | €1,065.60 | €0.00 | €0.00 | €0.00 | €50.67 | **€3,469.42** | Rejected |
| 2,537 L | 14 days | €3,445.05 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€3,445.05** | ✅ Selected |
| 41,512 L | 14 days | €56,373.68 | €0.00 | €0.00 | €0.00 | €0.00 | €-0.00 | **€56,373.68** | Rejected |

#### Why this candidate won

The optimiser selected **2,537 L** because its robust objective of **€3,445.05** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **1,770 L** with a robust objective of **€3,469.42**, which was **€24.37** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-03 | €1.41000/L | 372 L |
| 2026-07-04 | €1.44470/L | 2,165 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€80.65**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €3,445.05.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-24

| Input | Value |
|---|---:|
| Current quotation | €1.36800/L |
| Inventory before purchase | 10,328 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 697 L |
| Total purchase selected | **697 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 2; P07 price percentile 0.33.
- Signal score: +0.787.
- Confidence: 0.633.
- Adjusted signal: +0.499.
- Expected daily quotation change: +0.00474 €/L.
- Observed price percentile: 33%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €985.63 | €0.00 | €0.00 | €0.00 | €66.08 | **€985.63** | Rejected |
| 697 L | 14 days | €953.01 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€953.01** | ✅ Selected |
| 39,672 L | 14 days | €54,271.40 | €0.00 | €0.00 | €0.00 | €0.00 | €-0.00 | **€54,271.40** | Rejected |

#### Why this candidate won

The optimiser selected **697 L** because its robust objective of **€953.01** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€985.63**, which was **€32.61** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-03 | €1.41000/L | 372 L |
| 2026-07-04 | €1.44470/L | 325 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€32.61**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €953.01.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-25

| Input | Value |
|---|---:|
| Current quotation | €1.37400/L |
| Inventory before purchase | 10,205 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 820 L |
| Total purchase selected | **820 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 3; P07 price percentile 0.47.
- Signal score: +0.718.
- Confidence: 0.667.
- Adjusted signal: +0.479.
- Expected daily quotation change: +0.00431 €/L.
- Observed price percentile: 47%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €1,164.65 | €0.00 | €0.00 | €0.00 | €70.48 | **€1,164.65** | Rejected |
| 820 L | 14 days | €1,126.61 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€1,126.61** | ✅ Selected |
| 39,795 L | 14 days | €54,678.85 | €0.00 | €0.00 | €0.00 | €0.00 | €-0.00 | **€54,678.85** | Rejected |

#### Why this candidate won

The optimiser selected **820 L** because its robust objective of **€1,126.61** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€1,164.65**, which was **€38.04** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-03 | €1.41000/L | 372 L |
| 2026-07-04 | €1.44470/L | 448 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€38.04**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €1,126.61.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 14,000 L at €1.44554/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368321 — Diesel

**Economic result:** €137.31 saved (0.82%).

**Average purchase price:** €1.55012/L → €1.53745/L.

**Order count:** 3 → 4.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-04 | 898 L | 358 L | **358 L** | €1.50581/L |
| 2026-07-07 | 0 L | 478 L | **478 L** | €1.54700/L |
| 2026-07-08 | 0 L | 478 L | **10,000 L** | €1.55186/L |

### CUEBIT decision stories

### Decision — 2026-06-23

| Input | Value |
|---|---:|
| Current quotation | €1.42500/L |
| Inventory before purchase | 6,281 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 358 L |
| Total purchase selected | **358 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 falling; P02 streak 1; P07 price percentile 0.13.
- Signal score: +0.222.
- Confidence: 0.600.
- Adjusted signal: +0.133.
- Expected daily quotation change: +0.00200 €/L.
- Observed price percentile: 13%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €514.76 | €0.00 | €0.00 | €0.00 | €39.89 | **€514.76** | Rejected |
| 358 L | 14 days | €510.06 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€510.06** | ✅ Selected |
| 3,719 L | 14 days | €5,300.02 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€5,300.02** | Rejected |

#### Why this candidate won

The optimiser selected **358 L** because its robust objective of **€510.06** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€514.76**, which was **€4.70** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-04 | €1.50581/L | 358 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€4.70**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €510.06.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-24

| Input | Value |
|---|---:|
| Current quotation | €1.43200/L |
| Inventory before purchase | 6,161 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 478 L |
| Total purchase selected | **478 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 2; P07 price percentile 0.22.
- Signal score: +0.861.
- Confidence: 0.633.
- Adjusted signal: +0.545.
- Expected daily quotation change: +0.00763 €/L.
- Observed price percentile: 22%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €720.81 | €0.00 | €0.00 | €0.00 | €63.85 | **€720.81** | Rejected |
| 478 L | 14 days | €683.92 | €0.00 | €0.00 | €0.00 | €0.00 | €-0.00 | **€683.92** | ✅ Selected |
| 3,839 L | 14 days | €5,497.41 | €0.00 | €0.00 | €0.00 | €0.00 | €-0.00 | **€5,497.41** | Rejected |

#### Why this candidate won

The optimiser selected **478 L** because its robust objective of **€683.92** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€720.81**, which was **€36.89** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-04 | €1.50581/L | 358 L |
| 2026-07-07 | €1.54700/L | 120 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€36.89**.
- Selected downside cost: €-0.00.
- Immediate supplier spend on this order: €683.92.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-25

| Input | Value |
|---|---:|
| Current quotation | €1.44000/L |
| Inventory before purchase | 6,161 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 478 L |
| Total purchase selected | **478 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 3; P07 price percentile 0.32.
- Signal score: +0.806.
- Confidence: 0.667.
- Adjusted signal: +0.537.
- Expected daily quotation change: +0.00699 €/L.
- Observed price percentile: 32%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €725.93 | €0.00 | €0.00 | €0.00 | €58.61 | **€725.93** | Rejected |
| 478 L | 14 days | €688.24 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€688.24** | ✅ Selected |
| 3,839 L | 14 days | €5,528.62 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€5,528.62** | Rejected |

#### Why this candidate won

The optimiser selected **478 L** because its robust objective of **€688.24** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€725.93**, which was **€37.70** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-04 | €1.50581/L | 358 L |
| 2026-07-07 | €1.54700/L | 120 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€37.70**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €688.24.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 9,522 L at €1.55186/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368321 — Verde

**Economic result:** €0.00 saved (0.00%).

**Average purchase price:** €1.44554/L → €1.44554/L.

**Order count:** 1 → 1.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-08 | 924 L | 0 L | **8,234 L** | €1.44554/L |

### CUEBIT decision stories

No non-terminal optimisation purchase was made for this distributor/product. The only purchase was the final stock-equalisation adjustment, so the simulation does not demonstrate a timing advantage for this case.

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 8,234 L at €1.44554/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368322 — Diesel

**Economic result:** €0.00 saved (0.00%).

**Average purchase price:** €1.55186/L → €1.55186/L.

**Order count:** 1 → 1.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-08 | 974 L | 0 L | **13,026 L** | €1.55186/L |

### CUEBIT decision stories

No non-terminal optimisation purchase was made for this distributor/product. The only purchase was the final stock-equalisation adjustment, so the simulation does not demonstrate a timing advantage for this case.

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 13,026 L at €1.55186/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

# 368322 — Verde

**Economic result:** €54.55 saved (0.36%).

**Average purchase price:** €1.44548/L → €1.44021/L.

**Order count:** 2 → 3.

### Operational baseline

The baseline buys only the volume needed to remain feasible until the next observed quotation.

| Date | Inventory before | Demand cover required | Purchase | Quotation |
|---|---:|---:|---:|---:|
| 2026-07-07 | 171 L | 247 L | **247 L** | €1.44300/L |
| 2026-07-08 | 0 L | 503 L | **10,103 L** | €1.44554/L |

### CUEBIT decision stories

### Decision — 2026-06-24

| Input | Value |
|---|---:|
| Current quotation | €1.36800/L |
| Inventory before purchase | 6,039 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 247 L |
| Total purchase selected | **247 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 2; P07 price percentile 0.33.
- Signal score: +0.787.
- Confidence: 0.633.
- Adjusted signal: +0.499.
- Expected daily quotation change: +0.00474 €/L.
- Observed price percentile: 33%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €349.70 | €0.00 | €0.00 | €0.00 | €23.44 | **€349.70** | Rejected |
| 247 L | 14 days | €338.13 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€338.13** | ✅ Selected |
| 7,961 L | 14 days | €10,890.82 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€10,890.82** | Rejected |

#### Why this candidate won

The optimiser selected **247 L** because its robust objective of **€338.13** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€349.70**, which was **€11.57** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-07 | €1.44300/L | 247 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€11.57**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €338.13.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

### Decision — 2026-06-25

| Input | Value |
|---|---:|
| Current quotation | €1.37400/L |
| Inventory before purchase | 5,783 L |
| Operational minimum | 0 L |
| Available discretionary purchase selected | 503 L |
| Total purchase selected | **503 L** |
| Selected cover | 14 days |

#### Market evidence

- Patterns: P01 rising; P02 streak 3; P07 price percentile 0.47.
- Signal score: +0.718.
- Confidence: 0.667.
- Adjusted signal: +0.479.
- Expected daily quotation change: +0.00431 €/L.
- Observed price percentile: 47%.

#### Candidates evaluated

| Buy today | Cover | Purchase cost | Expected future cost | Holding | Capital | Orders | Downside | Robust objective | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0 L | 13 days | €0.00 | €715.02 | €0.00 | €0.00 | €0.00 | €43.27 | **€715.02** | Rejected |
| 503 L | 14 days | €691.67 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€691.67** | ✅ Selected |
| 8,217 L | 14 days | €11,290.63 | €0.00 | €0.00 | €0.00 | €0.00 | €0.00 | **€11,290.63** | Rejected |

#### Why this candidate won

The optimiser selected **503 L** because its robust objective of **€691.67** was the lowest among the feasible candidates after expected procurement, holding, working-capital, ordering and downside costs were included.

The next-best rejected candidate was **0 L** with a robust objective of **€715.02**, which was **€23.35** higher.

#### Baseline purchases approximately brought forward

The following FIFO allocation explains which later baseline litres the discretionary purchase can be interpreted as replacing. It is an audit explanation, not an additional optimiser calculation.

| Later baseline date | Baseline quotation | Litres allocated |
|---|---:|---:|
| 2026-07-07 | €1.44300/L | 247 L |

#### Decision-level economic result

- Expected advantage versus the operational-minimum candidate: **€23.35**.
- Selected downside cost: €0.00.
- Immediate supplier spend on this order: €691.67.

#### Caveats

Pattern confidence is detection confidence, not validated predictive probability..

<details>
<summary>Final stock-equalisation adjustment</summary>

- 2026-07-08: 9,600 L at €1.44554/L. This technical adjustment makes both strategies finish with the same inventory and is not treated as a normal optimisation decision.

</details>

## Validation boundary

This is a historical simulation against a modelled operational baseline. Actual historical purchase orders, realised demand, delivery fees, lead times, minimum order rules, payment terms and other client-specific constraints are required before the estimated savings can be treated as realised client savings.

The FIFO 'brought forward' mapping is explanatory only. The authoritative optimiser evidence is the candidate table and its robust-objective ranking.