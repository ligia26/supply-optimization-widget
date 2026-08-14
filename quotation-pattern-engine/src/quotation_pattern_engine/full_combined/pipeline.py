from __future__ import annotations
import json
from dataclasses import asdict
from pathlib import Path
from quotation_pattern_engine.external.loaders import load_external_market_observations, load_external_news_events
from quotation_pattern_engine.operational.loaders import build_demand_profiles, load_daily_sales, load_growth_factors, load_pattern_events, load_pattern_summaries, load_quotation_points, load_tank_states
from quotation_pattern_engine.operational.simulator import simulate_strategy
from quotation_pattern_engine.combined.simulator import simulate_combined_strategy
from quotation_pattern_engine.combined.reporting import dataclass_row, write_csv
from quotation_pattern_engine.local_market.loaders import load_market_signals, load_competitor_history
from .simulator import simulate_full_strategy


def _metrics(strategy, ledgers, decisions):
    ds=[x for x in decisions if x.strategy==strategy]; ls=[x for x in ledgers if x.strategy==strategy]
    return {'strategy':strategy,'supplier_spend_eur':sum(x.purchase_spend_eur for x in ds),'litres_purchased':sum(x.purchase_litres for x in ds),'orders':sum(x.purchase_litres>0.05 for x in ds),'lost_sales_litres':sum(x.lost_sales_litres for x in ls),'closing_inventory_litres':sum(x.closing_inventory_litres for x in ls[-len({(x.distributor_id,x.product) for x in ls}):]) if ls else 0}


def run_full_combined_simulation(*, serbatoi_path, daily_sales_path, monthly_sales_path, daily_analysis_csv, pattern_events_csv, pattern_summary_csv, external_market_csv, external_news_csv, competitor_history_csv, local_market_signals_csv, output_dir, operational_config, external_config, combined_config, local_config):
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    tanks=load_tank_states(serbatoi_path,operational_config)
    daily=load_daily_sales(daily_sales_path,operational_config); growth=load_growth_factors(monthly_sales_path,operational_config)
    demand=build_demand_profiles(daily,growth); quotations=load_quotation_points(daily_analysis_csv,operational_config)
    events=load_pattern_events(pattern_events_csv,operational_config); summaries=load_pattern_summaries(pattern_summary_csv,operational_config)
    market=load_external_market_observations(external_market_csv); news=load_external_news_events(external_news_csv)
    local_daily=load_market_signals(local_market_signals_csv); competitor=load_competitor_history(competitor_history_csv)
    op_ledgers=[]; op_decisions=[]
    for strategy in ('AS_IS','WIDGET'):
        l,d=simulate_strategy(strategy,tanks,demand,quotations,events,summaries,operational_config); op_ledgers+=l; op_decisions+=d
    ext_ledgers,ext_decisions=simulate_combined_strategy(tanks,demand,quotations,events,summaries,market,news,operational_config,external_config,combined_config)
    full_ledgers,full_decisions=simulate_full_strategy(tanks,demand,quotations,events,summaries,market,news,local_daily,competitor,operational_config,external_config,combined_config,local_config)
    all_ledgers=op_ledgers+ext_ledgers+full_ledgers; all_decisions=op_decisions+ext_decisions+full_decisions
    metrics=[_metrics(s,all_ledgers,all_decisions) for s in ('AS_IS','WIDGET','WIDGET_EXTERNAL','WIDGET_FULL')]
    base=metrics[0]['supplier_spend_eur']
    for row in metrics: row['saving_vs_as_is_eur']=base-row['supplier_spend_eur']
    paths={'strategy_comparison':out/'all_four_strategies.csv','full_decisions':out/'purchase_decisions_full.csv','full_inventory':out/'daily_inventory_full.csv','method':out/'simulation_method_full.json'}
    write_csv(paths['strategy_comparison'],metrics)
    write_csv(paths['full_decisions'],[dataclass_row(x,exclude=('candidate_trace',)) for x in full_decisions])
    write_csv(paths['full_inventory'],[dataclass_row(x) for x in full_ledgers])
    paths['method'].write_text(json.dumps({'strategies':['AS_IS','WIDGET','WIDGET_EXTERNAL','WIDGET_FULL'],'WIDGET':'operational + quotation patterns','WIDGET_EXTERNAL':'operational + quotation patterns + macro external market/news','WIDGET_FULL':'operational + quotation patterns + macro external market/news + local competitor history/signals','local_config':asdict(local_config)},indent=2),encoding='utf-8')
    return paths
