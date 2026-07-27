import pandas as pd


def test_verified_outputs_are_balanced():
    comp=pd.read_csv('/mnt/data/cuebit_v10_robust_mpc/results/cuebit_vs_as_is.csv')
    assert abs(comp.as_is_litres_purchased.sum()-comp.cuebit_litres_purchased.sum())<1e-5
    assert abs(comp.as_is_closing_inventory_litres.sum()-comp.cuebit_closing_inventory_litres.sum())<1e-5
    assert comp.cuebit_lost_sales_litres.sum()<1e-6
    assert comp.estimated_saving_eur.sum()>0
