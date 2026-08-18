from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import xlsxwriter


def _obj_dict(obj: Any) -> dict[str, Any]:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return dict(obj)
    return vars(obj)


def _decision_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    date_value = row.get("date")
    date_key = date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value)
    return (
        date_key,
        str(row.get("strategy", "")),
        str(row.get("distributor_id", "")),
        str(row.get("product", "")),
    )


def write_simulation_audit_workbook(
    path: str | Path,
    *,
    ledgers: list[Any],
    decisions: list[Any],
    comparison_rows: list[dict[str, Any]],
    config: Any,
    title: str,
) -> Path:
    """Human-readable audit workbook linking every headline euro to daily rows."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    decision_lookup: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for decision in decisions:
        d = _obj_dict(decision)
        decision_lookup[_decision_key(d)] = d

    wb = xlsxwriter.Workbook(output)
    wb.set_properties({"title": title, "subject": "CUEBIT simulation audit and reconciliation"})

    fmt_title = wb.add_format({"bold": True, "font_size": 16})
    fmt_header = wb.add_format({"bold": True, "bg_color": "#E7E6E6", "border": 1, "text_wrap": True})
    fmt_subheader = wb.add_format({"bold": True, "bg_color": "#D9EAF7", "border": 1})
    fmt_text = wb.add_format({"border": 1})
    fmt_int = wb.add_format({"border": 1, "num_format": "#,##0"})
    fmt_litre = wb.add_format({"border": 1, "num_format": '#,##0 "L"'})
    fmt_price = wb.add_format({"border": 1, "num_format": '€0.00000'})
    fmt_eur = wb.add_format({"border": 1, "num_format": '€#,##0.00;[Red]-€#,##0.00'})
    fmt_pct = wb.add_format({"border": 1, "num_format": '0.00%'})
    fmt_date = wb.add_format({"border": 1, "num_format": "dd/mm/yyyy"})
    fmt_note = wb.add_format({"italic": True, "font_color": "#666666", "text_wrap": True})

    # ------------------------------------------------------------------
    # DAILY AUDIT
    # ------------------------------------------------------------------
    ws = wb.add_worksheet("Daily Audit")
    ws.freeze_panes(2, 0)
    ws.write(0, 0, title, fmt_title)
    ws.write(0, 5, "Purchase € is formula-driven: Purchase L × quotation price", fmt_note)
    headers = [
        "Date", "Distributor", "Product", "Strategy",
        "Opening stock", "Opening implicit cost", "Sales",
        "Purchase L", "Purchase price", "Purchase €",
        "Closing stock", "Closing implicit cost",
        "Decision / reason", "Operational required L", "Strategic extra L",
        "Signal score", "Confidence", "Price percentile",
        "External drivers", "External themes",
    ]
    for c, h in enumerate(headers):
        ws.write(1, c, h, fmt_header)

    sorted_ledgers = sorted(
        ledgers,
        key=lambda x: (
            str(getattr(x, "distributor_id", "")),
            str(getattr(x, "product", "")),
            getattr(x, "date", ""),
            str(getattr(x, "strategy", "")),
        ),
    )

    for r0, ledger in enumerate(sorted_ledgers, start=2):
        l = _obj_dict(ledger)
        date_value = l.get("date")
        date_key = date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value)
        key = (date_key, str(l.get("strategy", "")), str(l.get("distributor_id", "")), str(l.get("product", "")))
        d = decision_lookup.get(key, {})
        ws.write_datetime(r0, 0, date_value, fmt_date) if hasattr(date_value, "year") else ws.write(r0, 0, str(date_value), fmt_text)
        ws.write(r0, 1, l.get("distributor_id", ""), fmt_text)
        ws.write(r0, 2, l.get("product", ""), fmt_text)
        ws.write(r0, 3, l.get("strategy", ""), fmt_text)
        ws.write_number(r0, 4, float(l.get("opening_inventory_litres", 0.0)), fmt_litre)
        ws.write_number(r0, 5, float(l.get("opening_implicit_cost_per_litre", 0.0)), fmt_price)
        ws.write_number(r0, 6, float(l.get("sales_litres", 0.0)), fmt_litre)
        ws.write_number(r0, 7, float(l.get("purchase_litres", 0.0)), fmt_litre)
        ws.write_number(r0, 8, float(l.get("purchase_price_eur_per_litre", 0.0)), fmt_price)
        excel_row = r0 + 1
        ws.write_formula(r0, 9, f"=H{excel_row}*I{excel_row}", fmt_eur, float(l.get("purchase_total_eur", 0.0)))
        ws.write_number(r0, 10, float(l.get("closing_inventory_litres", 0.0)), fmt_litre)
        ws.write_number(r0, 11, float(l.get("closing_implicit_cost_per_litre", 0.0)), fmt_price)
        ws.write(r0, 12, d.get("reason", "HOLD / no quotation purchase"), fmt_text)
        ws.write_number(r0, 13, float(d.get("operational_required_litres", 0.0) or 0.0), fmt_litre)
        ws.write_number(r0, 14, float(d.get("discretionary_litres", 0.0) or 0.0), fmt_litre)
        score = d.get("combined_signal_score", d.get("signal_score", 0.0)) or 0.0
        conf = d.get("combined_signal_confidence", d.get("signal_confidence", 0.0)) or 0.0
        percentile = d.get("observed_price_percentile", d.get("price_percentile", 0.0)) or 0.0
        ws.write_number(r0, 15, float(score), fmt_text)
        ws.write_number(r0, 16, float(conf), fmt_pct)
        ws.write_number(r0, 17, float(percentile), fmt_pct)
        ws.write(r0, 18, d.get("external_drivers", ""), fmt_text)
        ws.write(r0, 19, d.get("external_themes", ""), fmt_text)

    widths = [12, 12, 10, 18, 15, 18, 13, 13, 14, 14, 15, 18, 42, 18, 18, 12, 12, 14, 28, 28]
    for i, width in enumerate(widths):
        ws.set_column(i, i, width)
    ws.autofilter(1, 0, max(1, len(sorted_ledgers) + 1), len(headers) - 1)

    # ------------------------------------------------------------------
    # ECONOMIC RECONCILIATION
    # ------------------------------------------------------------------
    rec = wb.add_worksheet("Economic Reconciliation")
    rec.write(0, 0, "Economic Reconciliation", fmt_title)
    rec.write(1, 0, "Economic saving = (AS IS cash spend − ending inventory value) − (CUEBIT cash spend − ending inventory value)", fmt_note)

    rec_headers = [
        "Distributor", "Product",
        "AS IS cash spend", "CUEBIT cash spend", "Cash difference",
        "AS IS ending stock", "CUEBIT ending stock", "Terminal price",
        "AS IS ending inventory value", "CUEBIT ending inventory value",
        "AS IS economic cost", "CUEBIT economic cost", "Economic saving",
    ]
    for c, h in enumerate(rec_headers):
        rec.write(3, c, h, fmt_header)

    def getv(row: dict[str, Any], *names: str, default: float = 0.0) -> float:
        for name in names:
            if name in row:
                return float(row[name] or 0.0)
        return default

    distributor_totals: dict[str, list[float]] = defaultdict(lambda: [0.0] * 10)
    for idx, row in enumerate(comparison_rows, start=4):
        dist = str(row.get("distributor_id", "")); prod = str(row.get("product", ""))
        as_cash = getv(row, "as_is_cash_spend_eur", "as_is_supplier_spend_eur")
        cue_cash = getv(row, "combined_cash_spend_eur", "cuebit_supplier_spend_eur", "operational_cash_spend_eur", "combined_supplier_spend_eur")
        as_stock = getv(row, "as_is_closing_inventory_litres")
        cue_stock = getv(row, "combined_closing_inventory_litres", "cuebit_closing_inventory_litres", "operational_closing_inventory_litres")
        term = getv(row, "terminal_valuation_price_eur_per_litre")
        as_inv = getv(row, "as_is_ending_inventory_value_eur", default=as_stock * term)
        cue_inv = getv(row, "combined_ending_inventory_value_eur", "cuebit_ending_inventory_value_eur", "operational_ending_inventory_value_eur", default=cue_stock * term)
        as_cost = getv(row, "as_is_inventory_adjusted_economic_cost_eur", default=as_cash - as_inv)
        cue_cost = getv(row, "combined_inventory_adjusted_economic_cost_eur", "cuebit_inventory_adjusted_economic_cost_eur", "operational_inventory_adjusted_economic_cost_eur", default=cue_cash - cue_inv)
        saving = getv(row, "combined_saving_vs_as_is_eur", "estimated_saving_eur", "operational_saving_vs_as_is_eur", default=as_cost - cue_cost)
        values = [dist, prod, as_cash, cue_cash, as_cash-cue_cash, as_stock, cue_stock, term, as_inv, cue_inv, as_cost, cue_cost, saving]
        rec.write(idx, 0, dist, fmt_text); rec.write(idx, 1, prod, fmt_text)
        for c, val in enumerate(values[2:], start=2):
            fmt = fmt_litre if c in (5,6) else (fmt_price if c == 7 else fmt_eur)
            rec.write_number(idx, c, float(val), fmt)

        dt = distributor_totals[dist]
        for j, val in enumerate([as_cash,cue_cash,as_cash-cue_cash,as_stock,cue_stock,as_inv,cue_inv,as_cost,cue_cost,saving]):
            dt[j] += val

    start_tot = 6 + len(comparison_rows)
    rec.write(start_tot, 0, "Distributor totals", fmt_subheader)
    total_headers = ["Distributor","AS IS cash","CUEBIT cash","Cash Δ","AS IS end stock","CUEBIT end stock","AS IS inv value","CUEBIT inv value","AS IS econ cost","CUEBIT econ cost","Economic saving"]
    for c,h in enumerate(total_headers): rec.write(start_tot+1,c,h,fmt_header)
    portfolio = [0.0]*10
    rr=start_tot+2
    for dist in sorted(distributor_totals):
        vals=distributor_totals[dist]
        rec.write(rr,0,dist,fmt_text)
        for c,val in enumerate(vals, start=1):
            fmt=fmt_litre if c in (4,5) else fmt_eur
            rec.write_number(rr,c,val,fmt)
        for j,val in enumerate(vals): portfolio[j]+=val
        rr+=1
    rec.write(rr,0,"TOTAL",fmt_subheader)
    for c,val in enumerate(portfolio,start=1):
        fmt=fmt_litre if c in (4,5) else fmt_eur
        rec.write_number(rr,c,val,fmt)
    rec.set_column(0, 1, 14); rec.set_column(2, 12, 19)

    # ------------------------------------------------------------------
    # ASSUMPTIONS / LINEAGE
    # ------------------------------------------------------------------
    ass = wb.add_worksheet("Assumptions")
    ass.write(0, 0, "Simulation assumptions & source lineage", fmt_title)
    ass.write_row(2, 0, ["Parameter", "Value", "Status / source"], fmt_header)
    cfg = _obj_dict(config)
    rows = [
        ("Opening stock", "Serbatoi.Giacenza Attuale", "Simulation assumption: treated as opening stock"),
        ("Tank capacity", "Serbatoi.Capacità Max", "Client source"),
        ("Daily demand shape", "Litres", "Client source"),
        ("Monthly demand scale", "Litri Venduti", "Client source"),
        ("Quotation price", "Supplier quotations", "Client source"),
        ("Hard minimum stock", cfg.get("hard_min_stock_litres", 700), "Confirmed operational rule"),
        ("Delivery lead time (days)", cfg.get("delivery_lead_time_days", 1), "Simulation assumption"),
        ("Minimum order (L)", cfg.get("minimum_order_litres", 5000), "Simulation assumption"),
        ("Order rounding (L)", cfg.get("order_rounding_litres", 1000), "Simulation assumption"),
        ("Usable capacity", cfg.get("max_fill_ratio", .95), "Simulation assumption"),
        ("Ending inventory valuation", "Last observed quotation by product", "Economic comparison rule"),
    ]
    for r,(a,b,c) in enumerate(rows,start=3):
        ass.write(r,0,a,fmt_text); ass.write(r,1,b,fmt_text); ass.write(r,2,c,fmt_text)
    ass.set_column(0,0,28); ass.set_column(1,1,34); ass.set_column(2,2,45)

    wb.close()
    return output
