from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
from .config import OperationalConfig
from .models import *
from .optimizer import demand_between,evaluate_candidates
from .signal_model import build_signal

def simulate_strategy(strategy:str,tanks:list[TankState],demand_profiles:list[DemandProfile],quotations:list[QuotationPoint],events:list[PatternEvent],summaries:list[PatternSummary],config:OperationalConfig):
    if strategy not in {"AS_IS","WIDGET"}: raise ValueError(strategy)
    lookup={(x.distributor_id,x.product,x.weekday):x.forecast_daily_litres for x in demand_profiles}
    byp=defaultdict(list)
    for q in quotations:byp[q.product].append(q)
    for v in byp.values():v.sort(key=lambda x:x.date)
    start=date.fromisoformat(config.simulation_start) if config.simulation_start else min(x.date for x in quotations)
    end=date.fromisoformat(config.simulation_end) if config.simulation_end else max(x.date for x in quotations)
    inv={(t.distributor_id,t.product):t.opening_inventory_litres for t in tanks}; led=[]; dec=[]
    qlookup={(q.product,q.date):q for q in quotations}
    for day_i in range((end-start).days+1):
        day=start+timedelta(days=day_i)
        for t in sorted(tanks,key=lambda x:(x.distributor_id,x.product)):
            key=(t.distributor_id,t.product); opening=inv[key]; today=lookup.get((t.distributor_id,t.product,day.weekday()),0.0)
            point=qlookup.get((t.product,day)); purchase=0.0; decision=None
            if point is not None:
                qdates=[x.date for x in byp[t.product]]; nextq=next((d for d in qdates if d>day),end+timedelta(days=1))
                hist=[x for x in byp[t.product] if x.date<=day]
                sig=build_signal(hist,events,day,config)
                # Retrospective feasibility floor: enough stock to survive until the next observed quotation.
                required_end=min(nextq,end+timedelta(days=1))
                req_target=demand_between(lookup,t.distributor_id,t.product,day,required_end)
                req_buy=max(0.0,min(req_target,t.capacity_litres*config.max_fill_ratio)-opening)
                candidates=[]; required=None; chosen=None
                if day==end:
                    purchase=max(0.0,min(t.capacity_litres*config.max_fill_ratio,t.opening_inventory_litres+today)-opening)
                    selected=0.0; reason="Final quotation-date stock equalisation"; downside=0.0
                elif strategy=="AS_IS":
                    purchase=req_buy; selected=float((required_end-day).days); reason="Reference policy: cover until next observed quotation"; downside=0.0
                else:
                    candidates=evaluate_candidates(day=day,end=end,tank=t,inventory=opening,current_price=point.price_per_litre,required_buy=req_buy,demand_lookup=lookup,signal=sig,history=hist,config=config)
                    required=min(candidates,key=lambda c:(abs(c.purchase_litres-req_buy),c.expected_total_cost_eur))
                    chosen=min(candidates,key=lambda c:(c.expected_total_cost_eur,c.purchase_litres))
                    # Bearish evidence may justify waiting, but never below the operational feasibility floor.
                    if sig.score<=0 and chosen.purchase_litres>required.purchase_litres:
                        chosen=required
                    purchase=max(req_buy,chosen.purchase_litres); selected=chosen.target_cover_days; reason="Lowest robust expected-cost volume" if chosen is not required else "Operational minimum selected"; downside=chosen.downside_cost_eur
                purchase=min(purchase,max(0.0,t.capacity_litres*config.max_fill_ratio-opening))
                chosen_cost=(chosen.expected_total_cost_eur if strategy=="WIDGET" and day!=end else purchase*point.price_per_litre)
                required_cost=(required.expected_total_cost_eur if strategy=="WIDGET" and day!=end else purchase*point.price_per_litre)
                decision=PurchaseDecision(day,strategy,t.distributor_id,t.product,point.price_per_litre,opening,purchase,purchase*point.price_per_litre+(config.order_cost_eur if purchase>0 else 0),selected,req_buy,max(0,purchase-req_buy),sig.score,sig.confidence,sig.expected_change_per_litre_day,sig.price_percentile,len(candidates),chosen_cost,required_cost,required_cost-chosen_cost,downside," | ".join(sig.patterns)," | ".join(sig.caveats),reason)
                dec.append(decision)
            sold=min(today,opening+purchase); lost=max(0,today-sold); closing=opening+purchase-sold; inv[key]=closing
            regime=point.regime if point else "No new quotation"
            led.append(DailyLedgerRow(day,strategy,t.distributor_id,t.product,opening,purchase,decision.purchase_spend_eur if decision else 0.0,sold,lost,closing,regime))
    return led,dec
