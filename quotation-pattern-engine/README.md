# Quotation Pattern Engine

A reusable deterministic analysis pipeline for historical fuel quotation datasets.

It takes a quotation table as input and produces:

1. `daily_analysis.csv` — one row per canonical quotation with movements and regimes.
2. `pattern_summary.csv` — aggregate metrics by supplier/product.
3. `pattern_events.csv` — streaks, spikes, reversals and stable periods.
4. `llm_payload.json` — structured facts suitable for an LLM.
5. `interpretation_prompt.txt` — a controlled prompt that prevents the LLM from inventing calculations.
6. `deterministic_interpretation.md` — a readable interpretation produced without an LLM.
7. `canonical_quotations.csv` — cleaned input after duplicate resolution.

The pattern detector does not depend on a particular supplier, date range, product list, or price level.

## Scope

This package starts from the **Historical Quotation Dataset**.

It does not parse quotation emails. Email extraction and validation should remain a separate upstream component:

```text
Quotation emails
      ↓
Extraction and validation
      ↓
Historical quotation dataset
      ↓
This pattern engine
```

## Minimum input schema

A CSV file must contain:

| Field | Required | Description |
|---|---:|---|
| `date` | yes | Quotation date |
| `product` | yes | Product or fuel name |
| `price` | yes | Numeric quotation price |
| `supplier` | no | Supplier name |
| `valid_from` | no | Start of quotation validity |
| `valid_to` | no | End of quotation validity |
| `event_type` | no | Normal, regulatory update, revision, etc. |
| `source` | no | Source filename or source identifier |
| `priority` | no | Numeric precedence for duplicate resolution |

Column names are configurable, so the input does not need to use these exact headers.

## Installation

Python 3.10+ is recommended.

```bash
cd quotation-pattern-engine
pip install -e .
```

The engine itself uses only the Python standard library.

## Run

```bash
quotation-patterns analyze \
  --input examples/sample_quotations.csv \
  --config examples/config.json \
  --output output
```

Or:

```bash
python run_analysis.py \
  --input examples/sample_quotations.csv \
  --config examples/config.json \
  --output output
```

## Apply it to another quotation dataset

1. Put the new quotations in a CSV.
2. Map its headers in `config.json`.
3. Run the same command.
4. Read the generated tables and LLM payload.

No product-specific code changes are required.

## Canonical quotation selection

Multiple rows may exist for the same date, supplier and product.

The engine selects one canonical row using:

1. Highest numeric `priority`.
2. If priorities tie, the last input row wins.

For example, a revised quotation caused by an excise-duty update can be assigned a higher priority than the original quotation.

## Pattern library

### P01 — Market regime

Uses a configurable lookback. The current quotation is compared with the quotation `regime_lookback` observations earlier.

- Rising: change > `regime_threshold`
- Falling: change < `-regime_threshold`
- Stable: otherwise

### P02 — Consecutive movements

Detects streaks of consecutive increases or decreases.

### P03 — Price spikes

A movement is a spike when its absolute magnitude is at least:

```text
max(
  absolute_spike_floor,
  mean_absolute_change + spike_std_multiplier × standard_deviation
)
```

### P04 — Trend reversals

Detects a change from increasing to decreasing or vice versa. Stable observations do not create a reversal.

### P05 — Stable periods

Detects consecutive observations where absolute price changes remain within the stability threshold.

## LLM architecture

The LLM should never calculate the patterns from raw prices.

```text
Historical dataset
      ↓
Deterministic pattern engine
      ↓
Structured JSON facts
      ↓
LLM interpretation
```

The generated payload contains only computed evidence. The included prompt explicitly tells the LLM not to recalculate values, invent causes or make forecasts.

## Tests

```bash
python -m unittest discover -s tests
```
