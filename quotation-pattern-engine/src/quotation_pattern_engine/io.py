from __future__ import annotations

import csv
from datetime import datetime, date
from pathlib import Path
from typing import Iterable, Any

from .config import EngineConfig
from .models import Quotation


def _parse_date(raw: str | None, formats: list[str], required: bool) -> date | None:
    if raw is None or not str(raw).strip():
        if required:
            raise ValueError("Required date value is empty.")
        return None

    value = str(raw).strip()
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(
        f"Could not parse date {value!r}. Accepted formats: {', '.join(formats)}"
    )


def _optional(row: dict[str, str], column: str | None, default: str = "") -> str:
    if not column:
        return default
    value = row.get(column)
    return default if value is None or not str(value).strip() else str(value).strip()


def read_quotations(path: str | Path, config: EngineConfig) -> list[Quotation]:
    input_path = Path(path)
    if input_path.suffix.lower() != ".csv":
        raise ValueError(
            "V1 accepts CSV input. Export the Historical Quotation Dataset as CSV "
            "or add a separate XLSX input adapter."
        )

    quotations: list[Quotation] = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Input CSV has no header row.")

        required = {
            config.columns.date,
            config.columns.product,
            config.columns.price,
        }
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        for index, row in enumerate(reader):
            raw_price = str(row[config.columns.price]).strip().replace(",", ".")
            try:
                price = float(raw_price)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid price at input row {index + 2}: {raw_price!r}"
                ) from exc

            priority_raw = _optional(row, config.columns.priority, "0")
            try:
                priority = float(priority_raw.replace(",", "."))
            except ValueError as exc:
                raise ValueError(
                    f"Invalid priority at input row {index + 2}: {priority_raw!r}"
                ) from exc

            quotations.append(
                Quotation(
                    date=_parse_date(
                        row.get(config.columns.date),
                        config.date_formats,
                        required=True,
                    ),
                    product=str(row[config.columns.product]).strip(),
                    price=price,
                    supplier=_optional(row, config.columns.supplier, "Unknown"),
                    valid_from=_parse_date(
                        row.get(config.columns.valid_from)
                        if config.columns.valid_from else None,
                        config.date_formats,
                        required=False,
                    ),
                    valid_to=_parse_date(
                        row.get(config.columns.valid_to)
                        if config.columns.valid_to else None,
                        config.date_formats,
                        required=False,
                    ),
                    event_type=_optional(
                        row, config.columns.event_type, "Normal quotation"
                    ),
                    source=_optional(row, config.columns.source, ""),
                    priority=priority,
                    input_order=index,
                )
            )

    if not quotations:
        raise ValueError("Input dataset contains no quotation rows.")

    return quotations


def canonicalize(quotations: Iterable[Quotation]) -> list[Quotation]:
    selected: dict[tuple[Any, ...], Quotation] = {}
    for quotation in quotations:
        key = quotation.canonical_key
        current = selected.get(key)
        if current is None or (
            quotation.priority,
            quotation.input_order,
        ) >= (
            current.priority,
            current.input_order,
        ):
            selected[key] = quotation

    return sorted(
        selected.values(),
        key=lambda q: (q.supplier, q.product, q.date, q.input_order),
    )


def _serialize(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if value is None:
        return ""
    return value


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _serialize(value) for key, value in row.items()})
