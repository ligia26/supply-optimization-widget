from datetime import date
from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.operational.models import QuotationPoint, SignalAssessment, TankState
from quotation_pattern_engine.operational.optimizer import evaluate_candidates


def _history(changes):
    price=1.40
    rows=[]
    for i,change in enumerate(changes):
        price += change
        rows.append(QuotationPoint(date(2026,1,1+i),'Diesel','Diesel',price,'Rising' if change>0 else 'Falling','Normal quotation',change))
    return rows


def test_bullish_signal_can_favour_advance_volume():
    cfg=OperationalConfig(planning_horizon_days=7)
    tank=TankState('1','Diesel',20000,0,1.0,None)
    lookup={('1','Diesel',i):1000 for i in range(7)}
    sig=SignalAssessment(.8,.8,.02,.2,.01,('P01 rising',),())
    history=_history([-.01,.01,.02,.01])
    rows=evaluate_candidates(day=date(2026,1,4),end=date(2026,1,15),tank=tank,inventory=0,current_price=1.4,required_buy=1000,demand_lookup=lookup,signal=sig,history=history,config=cfg)
    assert min(rows,key=lambda x:x.expected_total_cost_eur).purchase_litres>1000


def test_bearish_signal_keeps_expected_price_at_or_below_current_for_bearish_history():
    cfg=OperationalConfig(planning_horizon_days=7)
    tank=TankState('1','Diesel',20000,0,1.0,None)
    lookup={('1','Diesel',i):1000 for i in range(7)}
    sig=SignalAssessment(-.8,.8,-.02,.8,.01,('P01 falling',),())
    history=_history([-.03,-.02,-.01,-.02])
    rows=evaluate_candidates(day=date(2026,1,4),end=date(2026,1,15),tank=tank,inventory=0,current_price=1.4,required_buy=1000,demand_lookup=lookup,signal=sig,history=history,config=cfg)
    assert all(r.expected_future_price_eur_per_litre<=1.4 for r in rows)


def test_candidate_space_is_dense_and_capacity_bounded():
    cfg=OperationalConfig(planning_horizon_days=14)
    tank=TankState('1','Diesel',10000,2000,1.0,None)
    lookup={('1','Diesel',i):900 for i in range(7)}
    sig=SignalAssessment(.2,.5,.001,.4,.01,(),())
    history=_history([-.01,.00,.01,.01])
    rows=evaluate_candidates(day=date(2026,1,4),end=date(2026,1,20),tank=tank,inventory=2000,current_price=1.4,required_buy=500,demand_lookup=lookup,signal=sig,history=history,config=cfg)
    assert len(rows) >= 8
    assert max(r.purchase_litres for r in rows) <= 8000
