from __future__ import annotations
import argparse
from pathlib import Path
from quotation_pattern_engine.operational.config import OperationalConfig
from quotation_pattern_engine.external.config import ExternalConfig
from quotation_pattern_engine.combined.config import CombinedConfig
from quotation_pattern_engine.local_market.config import LocalMarketConfig
from quotation_pattern_engine.full_combined.pipeline import run_full_combined_simulation

def first(label,*paths):
    for p in paths:
        if p.exists(): return p
    raise FileNotFoundError(f'Could not find {label}: '+', '.join(map(str,paths)))

def main():
    parser=argparse.ArgumentParser(description='Run all CUEBIT strategies, preserving current approaches and adding WIDGET_FULL')
    parser.add_argument('--project-root',type=Path,default=Path(__file__).resolve().parent.parent)
    a=parser.parse_args(); root=a.project_root.resolve(); op=root/'data/operational'; ext=root/'data/external'; loc=root/'data/local_market'
    qo=[root/'outputs/quotation_analysis',root/'quotation-pattern-engine/examples/output']
    oc=OperationalConfig.from_json(root/'config/operational.json') if (root/'config/operational.json').exists() else OperationalConfig()
    ec=ExternalConfig.from_json(root/'config/external.json') if (root/'config/external.json').exists() else ExternalConfig()
    cc=CombinedConfig.from_json(root/'config/combined.json') if (root/'config/combined.json').exists() else CombinedConfig()
    lc=LocalMarketConfig.from_json(root/'config/local_market.json') if (root/'config/local_market.json').exists() else LocalMarketConfig()
    paths=run_full_combined_simulation(serbatoi_path=first('Serbatoi',op/'Serbatoi.xlsx',op/'Serbatoi(2).xlsx'),daily_sales_path=first('Litres',op/'Litres.xlsx'),monthly_sales_path=first('Litri Venduti',op/'Litri Venduti.xlsx',op/'Litri Venduti (1)(1).xlsx'),daily_analysis_csv=first('daily_analysis.csv',*(x/'daily_analysis.csv' for x in qo)),pattern_events_csv=first('pattern_events.csv',*(x/'pattern_events.csv' for x in qo)),pattern_summary_csv=first('pattern_summary.csv',*(x/'pattern_summary.csv' for x in qo)),external_market_csv=ext/'external_market_daily.csv',external_news_csv=ext/'external_news_events.csv',competitor_history_csv=loc/'competitor_historical_pricing.csv',local_market_signals_csv=loc/'market_signals_daily.csv',output_dir=root/'outputs/full_combined',operational_config=oc,external_config=ec,combined_config=cc,local_config=lc)
    for k,v in paths.items(): print(f'{k}: {v.resolve()}')
if __name__=='__main__': main()
