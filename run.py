import pandas as pd
from parts.utilities.utils import * 
from cadCAD.engine import ExecutionMode, ExecutionContext,Executor
from config import exp
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows


def run():
    '''
    Definition:
    Run simulation
    '''
    # Single
    exec_mode = ExecutionMode()
    local_mode_ctx = ExecutionContext(context=exec_mode.local_mode)

    simulation = Executor(exec_context=local_mode_ctx, configs=exp.configs)
    raw_system_events, tensor_field, sessions = simulation.execute()
    # Result System Events DataFrame
    df = pd.DataFrame(raw_system_events)
 
    return df

def postprocessing(df):
    '''
    Definition:
    Refine and extract metrics from the simulation
    
    Parameters:
    df: simulation dataframe

    format of output:
    df = {
        number of liquidity providers,
        liquidity added,
        pool balances,
        fees collected,
        treasury balances,
    }
    '''
    data = df
    json_data = df.to_json(orient='records')
    with open('data.json', 'w') as file:
        file.write(json_data)
    print(df.T)
    # number_of_liquidity_providers = []
    # liquidity_added = []
    # pool_balances = []
    # fees_collected = []
    # treasury_balances = []
    
    # Pool balances and ratios
    # Amount of traders and providers
    # Cumulative PnL for traders, max and min PnL for traders (per market)
    # Cumulative apy for liquidity providers (per market)
    # Open interest (long and short supplies per market)
    # Volumes
    # Number of liquidations
    # Fees collected
    # Treasury balance

    # track pnl of the pool as metric

    data = pd.DataFrame({
        'number_of_traders',
        'number_of_liquidity_providers',
        'pool_balance_btc',
        'pool_balance_eth',
        'pool_balance_sol',
        'pool_balance_usdc',
        'pool_balance_usdT',
        'cum_pnl_traders',
        'max_pnl_traders',
        'min_pnl_traders',
        'cum_apy_providers',
        'oi_long',
        'oi_short',
        'volume_btc',
        'volume_eth',
        'volume_sol',
        'number_of_liquidations',
        'fees_collected',
        'treasury_balance'
    })
    
    return data

def to_xslx(df):

    wb = openpyxl.Workbook()
    sheet = wb.active
    rows = dataframe_to_rows(df)
    for r_idx, row in enumerate(rows, 1):
        for c_idx, value in enumerate(row, 1):
            try:
                value = float(value)
            except:
                pass
            sheet.cell(row=r_idx, column=c_idx, value=value)
    wb.save(f'run.xlsx')

def main():
    '''
    Definition:
    Run simulation and extract metrics
    '''
    df = run()
    df = postprocessing(df)
    to_xslx(df) 
    return df

if __name__ == '__main__':
    main()