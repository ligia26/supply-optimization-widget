from __future__ import annotations
import math
import statistics
from datetime import date
from .config import OperationalConfig
from .models import PatternEvent, QuotationPoint, SignalAssessment

def _sgn(v:float|None,text:str="")->int:
    if v is not None and not math.isclose(v,0.0,abs_tol=1e-12): return 1 if v>0 else -1
    t=text.lower()
    if any(x in t for x in ("increase","rising","upward","positive")): return 1
    if any(x in t for x in ("decrease","falling","downward","negative")): return -1
    return 0

def _latest(events:list[PatternEvent], code:str, product:str, day:date, max_age:int)->PatternEvent|None:
    def classify(e:PatternEvent)->str|None:
        text=f"{e.pattern_name} {e.event_type} {e.pattern_id}".lower()
        if "consecutive" in text: return "P02"
        if "reversal" in text or "revision" in text: return "P05"
        if "spike" in text or "extreme" in text: return "P07"
        return None
    eligible=[e for e in events if e.product==product and e.end_date<=day and (day-e.end_date).days<=max_age and classify(e)==code]
    return max(eligible,key=lambda e:e.end_date) if eligible else None

def build_signal(history:list[QuotationPoint], events:list[PatternEvent], day:date, config:OperationalConfig)->SignalAssessment:
    if not history:
        raise ValueError("history cannot be empty")
    cur=history[-1]; prices=[x.price_per_litre for x in history]
    lo,hi=min(prices),max(prices); pct=.5 if math.isclose(lo,hi) else (prices[-1]-lo)/(hi-lo)
    family:dict[str,tuple[float,float,str]]={}
    caveats=["Pattern confidence is detection confidence, not validated predictive probability."]

    regime=cur.regime.lower()
    if regime in ("rising","falling"):
        family["P01"]=(1.0 if regime=="rising" else -1.0,.60,f"P01 {regime}")

    # Current causal streak, based only on observed quotation changes.
    streak_dir=0; streak_len=0
    for p in reversed(history[1:]):
        d=_sgn(p.change_per_litre)
        if d==0: break
        if streak_dir==0: streak_dir=d
        if d!=streak_dir: break
        streak_len+=1
    latest_p02=_latest(events,"P02",cur.product,day,config.max_pattern_age_days)
    p02_conf=min(.90,.45+.10*streak_len) if streak_len else 0.0
    if latest_p02 is not None:
        p02_conf=max(p02_conf,latest_p02.confidence or config.missing_pattern_confidence)
    if streak_dir:
        family["P02"]=(float(streak_dir),p02_conf,f"P02 streak {streak_len}")

    med=statistics.median(prices)
    if regime=="stable" and prices[-1]>med:
        family["P03"]=(-1.0,.55,"P03 stable premium")

    # P04 is non-directional; it increases evidence quality but never creates a price direction.
    if "multi-day" in cur.event_type.lower():
        family["P04"]=(0.0,.80,"P04 multi-day quotation")

    latest_p05=_latest(events,"P05",cur.product,day,config.max_pattern_age_days)
    if latest_p05 is not None:
        age=(day-latest_p05.end_date).days
        decay=max(0.0,1-age/(config.max_pattern_age_days+1))
        family["P05"]=(float(_sgn(latest_p05.magnitude_per_litre,latest_p05.direction)),(latest_p05.confidence or config.missing_pattern_confidence)*decay,f"P05 {latest_p05.pattern_name}")

    if any(x in cur.event_type.lower() for x in ("regulatory","accise")):
        family["P06"]=(float(_sgn(cur.change_per_litre,cur.event_type)),.95,"P06 regulatory update")

    latest_p07=_latest(events,"P07",cur.product,day,config.max_pattern_age_days)
    position=(0.5-pct)*2
    p07_dir=position; p07_conf=.65
    p07_label=f"P07 price percentile {pct:.2f}"
    if latest_p07 is not None:
        age=(day-latest_p07.end_date).days
        decay=max(0.0,1-age/(config.max_pattern_age_days+1))
        spike_dir=_sgn(latest_p07.magnitude_per_litre,latest_p07.direction)
        # A high upward spike at a high percentile is treated as expensive, not as an invitation to chase.
        if spike_dir>0 and pct>.75: spike_dir=-1
        p07_dir=max(-1.0,min(1.0,(position+spike_dir)/2))
        p07_conf=max(p07_conf,(latest_p07.confidence or config.missing_pattern_confidence)*decay)
        p07_label=f"P07 {latest_p07.pattern_name}; percentile {pct:.2f}"
    family["P07"]=(p07_dir,p07_conf,p07_label)

    weighted=[]
    for code,(direction,confidence,label) in family.items():
        weight=config.pattern_weights.get(code,1.0)
        weighted.append((direction*weight,confidence,label,weight))
    numerator=sum(v*c for v,c,_,_ in weighted)
    denominator=sum(abs(w)*c for _,c,_,w in weighted if c>0) or 1.0
    score=max(-1.0,min(1.0,numerator/denominator))
    directional=[c for v,c,_,_ in weighted if abs(v)>1e-12]
    confidence=sum(directional)/len(directional) if directional else 0.0

    changes=[abs(x.change_per_litre) for x in history if x.change_per_litre is not None and abs(x.change_per_litre)>1e-12]
    scale=statistics.median(changes[-7:]) if changes else 0.0
    expected=scale*score*confidence
    return SignalAssessment(score,confidence,expected,pct,scale,tuple(x[2] for x in weighted),tuple(caveats))
