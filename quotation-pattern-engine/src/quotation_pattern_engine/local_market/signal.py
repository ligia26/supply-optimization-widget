from __future__ import annotations
from datetime import date
import math, statistics
from quotation_pattern_engine.external.models import ExternalSignal, ExternalSignalComponent
from .config import LocalMarketConfig
from .models import LocalDailySignal, CompetitorPrice


def _clip(x, lo, hi): return max(lo, min(hi, x))

def _fuel(product: str) -> str:
    return 'Gasolio' if product in {'Diesel','Gasolio Synergy'} else 'Benzina'


def build_local_market_signal(
    daily: list[LocalDailySignal],
    history: list[CompetitorPrice],
    product: str,
    decision_date: date,
    config: LocalMarketConfig,
) -> ExternalSignal:
    fuel=_fuel(product)
    series=sorted([x for x in daily if x.fuel==fuel and x.date<=decision_date and (decision_date-x.date).days<=config.lookback_days], key=lambda x:x.date)
    if len(series)<2:
        return ExternalSignal(0,0,0,0,(),(),('Insufficient local competitor history before decision date',))
    latest=series[-1]
    one_day=latest.avg_price-series[-2].avg_price
    anchor=series[max(0,len(series)-4)]
    three_day=(latest.avg_price-anchor.avg_price)/max(1,(latest.date-anchor.date).days)
    moves=[series[i].avg_price-series[i-1].avg_price for i in range(1,len(series))]
    scale=max(statistics.pstdev(moves) if len(moves)>1 else abs(one_day), 0.002)
    direction=_clip((0.6*one_day+0.4*three_day)/(2*scale),-1,1)
    dispersion=max(0,latest.max_price-latest.min_price)
    reporting=_clip(latest.competitors/4.0,0,1)
    freshness=math.exp(-math.log(2)*max(0,(decision_date-latest.date).days)/2)

    # Change breadth from self-service station prices, available up to the decision date.
    rows=[x for x in history if x.fuel==fuel and x.is_self and x.snapshot_date<=decision_date]
    by_station={}
    for r in sorted(rows,key=lambda x:(x.station_id,x.snapshot_date)):
        by_station.setdefault(r.station_id,[]).append(r)
    up=down=changed=0
    for station, vals in by_station.items():
        vals=[v for v in vals if (decision_date-v.snapshot_date).days<=config.lookback_days]
        if len(vals)>=2:
            delta=vals[-1].price-vals[-2].price
            if abs(delta)>1e-9:
                changed+=1
                up += delta>0
                down += delta<0
    breadth=(up-down)/changed if changed else 0.0
    score=_clip(0.75*direction+0.25*breadth,-1,1)
    confidence=_clip(reporting*freshness*(0.65+0.35*min(1,len(series)/4)),0,1)
    expected=_clip(
        score*config.max_expected_change_eur_per_litre_day*config.retail_to_supplier_pass_through*confidence,
        -config.max_expected_change_eur_per_litre_day,
        config.max_expected_change_eur_per_litre_day,
    )
    uncertainty=(scale+0.15*dispersion)*config.retail_to_supplier_pass_through
    component=ExternalSignalComponent(
        component_id=f'LOCAL_{fuel}_{latest.date.isoformat()}',
        theme_id='LOCAL_COMPETITOR_MARKET',
        component_type='LOCAL_MARKET',
        driver='LOCAL_COMPETITOR_PRICING',
        direction_score=score,
        confidence=confidence,
        expected_change_eur_per_litre_day=expected,
        uncertainty_eur_per_litre_day=uncertainty,
        explanation=(f'{fuel} local market: avg={latest.avg_price:.3f}, 1d={one_day:+.4f}, '
                     f'3d/day={three_day:+.4f}, breadth={breadth:+.2f}, competitors={latest.competitors}'),
    )
    return ExternalSignal(score,confidence,expected,uncertainty,(component,),(),())


def merge_macro_and_local(macro: ExternalSignal, local: ExternalSignal, config: LocalMarketConfig) -> ExternalSignal:
    wm=config.macro_external_weight*macro.confidence
    wl=config.local_market_weight*local.confidence
    total=wm+wl
    if total<=1e-12:
        return ExternalSignal(0,0,0,0,macro.components+local.components,macro.themes_used,macro.caveats+local.caveats)
    score=(wm*macro.score+wl*local.score)/total
    expected=(wm*macro.expected_change_eur_per_litre_day+wl*local.expected_change_eur_per_litre_day)/total
    uncertainty=math.sqrt(macro.uncertainty_eur_per_litre_day**2+local.uncertainty_eur_per_litre_day**2)
    confidence=(config.macro_external_weight*macro.confidence+config.local_market_weight*local.confidence)/(config.macro_external_weight+config.local_market_weight)
    caveats=macro.caveats+local.caveats
    if macro.score*local.score<0:
        confidence=max(0,confidence-config.disagreement_penalty*min(abs(macro.score),abs(local.score)))
        caveats += ('Macro external and local competitor signals disagree.',)
    return ExternalSignal(_clip(score,-1,1),_clip(confidence,0,1),expected,uncertainty,macro.components+local.components,macro.themes_used,caveats)
