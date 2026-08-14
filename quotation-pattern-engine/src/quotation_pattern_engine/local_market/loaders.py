from __future__ import annotations
from datetime import datetime
from pathlib import Path
import csv
from .models import LocalDailySignal, CompetitorPrice


def _float(value: str) -> float:
    return float(str(value).replace(',', '.'))


def load_market_signals(path: str | Path) -> list[LocalDailySignal]:
    rows=[]
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            fuel=str(r.get('fuel','')).strip()
            if fuel not in {'Benzina','Gasolio'}:
                continue
            rows.append(LocalDailySignal(
                date=datetime.strptime(r['date'], '%Y-%m-%d').date(),
                fuel=fuel,
                avg_price=_float(r['avg_price']),
                min_price=_float(r['min_price']),
                max_price=_float(r['max_price']),
                competitors=int(float(r.get('competitors') or 0)),
            ))
    return rows


def load_competitor_history(path: str | Path) -> list[CompetitorPrice]:
    rows=[]
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            fuel=str(r.get('fuel','')).strip()
            if fuel not in {'Benzina','Gasolio'}:
                continue
            raw=str(r.get('dtComu','')).strip()
            communicated=None
            if raw:
                try: communicated=datetime.strptime(raw, '%d/%m/%Y %H:%M:%S')
                except ValueError: pass
            rows.append(CompetitorPrice(
                snapshot_date=datetime.strptime(r['snapshot_date'], '%Y-%m-%d').date(),
                station_id=str(r['station_id']).strip(),
                fuel=fuel,
                price=_float(r['price']),
                is_self=str(r.get('isSelf','')).strip() in {'1','true','True'},
                communicated_at=communicated,
            ))
    return rows
