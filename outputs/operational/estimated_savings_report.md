# AS IS vs WIDGET — estimated operational impact

> This is a simulation, not a reconstruction of realised purchases. Savings are estimated from a transparent reference policy and the widget policy using the same demand and quotation data.

## Portfolio result

- Estimated reduction in cost of litres sold: **€4,987.23**
- Estimated gross-margin uplift: **€4,987.23**
- Lost sales under AS IS: **0 L**
- Lost sales under WIDGET: **0 L**

## Result by distributor and product

| Distributor | Product | AS IS COGS | WIDGET COGS | Estimated saving | AS IS closing implicit cost | WIDGET closing implicit cost |
|---|---|---:|---:|---:|---:|---:|
| 368318 | Diesel | €70,940.69 | €70,525.04 | €415.65 | €1.4828/L | €1.4725/L |
| 368318 | Verde | €39,411.33 | €39,113.27 | €298.06 | €1.4341/L | €1.3897/L |
| 368319 | Diesel | €13,633.54 | €13,401.93 | €231.61 | €1.5300/L | €1.4941/L |
| 368319 | Verde | €16,253.71 | €15,831.17 | €422.54 | €1.4205/L | €1.4346/L |
| 368320 | Diesel | €45,385.02 | €44,863.67 | €521.35 | €1.5207/L | €1.4960/L |
| 368320 | Verde | €27,496.76 | €26,289.32 | €1,207.45 | €1.4245/L | €1.4005/L |
| 368321 | Diesel | €16,656.41 | €16,371.43 | €284.98 | €1.5070/L | €1.4910/L |
| 368321 | Verde | €12,926.84 | €12,379.94 | €546.90 | €1.5700/L | €1.4581/L |
| 368322 | Diesel | €20,178.96 | €19,818.43 | €360.53 | €1.5503/L | €1.4938/L |
| 368322 | Verde | €16,088.93 | €15,390.76 | €698.17 | €1.4529/L | €1.4389/L |

## Inputs grounded in client files

- Daily demand uses the January–March 2025 Verde/Diesel profile for each distributor and weekday.
- Demand is scaled using each distributor's January–June 2026 versus January–June 2025 sales ratio.
- Current tank inventory, physical capacity, selling price and opening implicit cost come from Serbatoi.xlsx.
- Quotation prices and regimes come from daily_analysis.csv and are converted from €/m³ to €/L.
- Performance is excluded because its quotation mapping has not been confirmed.

## Temporary simulation policy

- AS IS buys when inventory cannot cover expected demand for today and the next day, then replenishes to the opening inventory level.
- WIDGET waits during falling quotations when stock cover is sufficient.
- WIDGET uses physical available capacity during rising quotations or regulatory events.
- No minimum order size, order rounding, 95% fill rule, supplier lead time or confirmed safety-stock rule is assumed.
- The policies must be calibrated when the customer's real purchasing rules and delivery history become available.

## How to interpret the saving

The headline uses the difference in cost of goods sold for the same simulated demand. It is an estimated model benefit under the stated policy, not verified historical savings.