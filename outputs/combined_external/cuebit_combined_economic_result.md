# CUEBIT External Intelligence Validation

## Result

Adding external market intelligence improved the operational purchasing engine.

| Metric | Result |
|---|---:|
| Operational-only saving | **€2,456.09** |
| Combined engine saving | **€3,227.06** |
| Additional saving from external intelligence | **€770.97** |
| Improvement over the operational engine | **31.39%** |

The improvement was achieved while purchasing the same total litres, ending with the same physical inventory and creating no additional lost sales.

## Decisions changed by external intelligence

| Date | Station | Product | Recommendation | Why |
|---|---|---|---|---|
| 2026-06-17 | 368318 | Diesel | **Do not buy 10,760 L yet** | Buying immediately did not provide sufficient economic advantage. Drivers: Crude, Currency, Geopolitics. |
| 2026-06-17 | 368318 | Verde | **Do not buy 7,719 L yet** | Buying immediately did not provide sufficient economic advantage. Drivers: Crude, Currency, Geopolitics. |
| 2026-06-23 | 368318 | Diesel | **Buy 23,391 L (+10,760 L)** | Internal quotation patterns and external market conditions supported advancing future volume. Drivers: Crude, Currency. |
| 2026-06-23 | 368318 | Verde | **Buy 14,967 L (+7,719 L)** | Internal quotation patterns and external market conditions supported advancing future volume. Drivers: Crude, Currency. |

## Most important decision

On **2026-06-23**, for station **368318** and product **Verde**, the combined engine recommended **14,967 L** instead of **7,248 L**.

The modelled expected advantage for this decision was **€253.01**.

## Validation

| Check | Result |
|---|---|
| Same total litres purchased | PASS |
| Same closing inventory | PASS |
| No additional lost sales | PASS |

## Conclusion

The external layer does not replace the operational engine. It selectively changes purchase timing and volume when external evidence indicates that waiting or advancing a purchase is economically preferable.

This is a historical simulation against a modelled reference policy, not yet verified realised client savings.