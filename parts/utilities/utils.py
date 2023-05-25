
import pandas as pd
import numpy as np
import copy
import os
import random

def fetch_asset_prices(assets, timestep):
    asset_prices = {}
    for asset in assets:
        try:
            file_path = os.path.join('data', f'{asset}.xlsx')
            df = pd.read_excel(file_path)
        except:
            file_path = os.path.join('parts', 'data', f'{asset}.xlsx')
            df = pd.read_excel(file_path)
        price_high = df.loc[timestep, 'High']
        price_low = df.loc[timestep, 'Low']
        asset_prices.update({asset: [price_low, price_high]})
    return asset_prices

def get_asset_prices(asset_prices):
    asset_prices = copy.deepcopy(asset_prices)
    for asset in asset_prices.keys():
        #print(asset_prices)
        asset_prices[asset] = asset_prices[asset][0] + random.random() * (asset_prices[asset][1] - asset_prices[asset][0])
    return asset_prices

def get_asset_volatility(assets, timestep):
    asset_volatility = {}
    for asset in assets:
        try:
            file_path = os.path.join('data', f'{asset}.xlsx')
            df = pd.read_excel(file_path)
        except:
            file_path = os.path.join('parts', 'data', f'{asset}.xlsx')
            df = pd.read_excel(file_path)    

        try:
            close_prices = df.loc[timestep-10:timestep, 'Close']
            volatility = close_prices.std()
        except:
            volatility = None  # If there isn't enough data to compute volatility, return None

        asset_volatility.update({asset: volatility})
    return asset_volatility

def pool_total_holdings(pool, asset_prices):
    holdings = pool['holdings']
    tvl = 0
    for asset in holdings.keys():
        tvl += holdings[asset] * asset_prices[asset]
    return tvl

def get_account_value(trader, asset_prices):
    total_value = sum([trader['liquidity'][asset] * asset_prices[asset] for asset in trader['liquidity'].keys()])
    total_value += sum([(trader['positions'][asset][0] * asset_prices[asset] - trader['loans'][asset][0]) for asset in trader['positions'].keys()])
    return total_value


def number_of_lqprov(timestep):
    return 20

def calculate_interest(position_size, duration, asset, pool, rate_params):
    optimal_utilization = rate_params[0]
    slope1 = rate_params[1]
    slope2 = rate_params[2]

    total_holdings = pool['holdings'][asset]
    total_borrowed = pool['oi_long'][asset] + pool['oi_short'][asset]

    # Handle division by zero
    if total_holdings == 0:
        return 0

    current_utilization = total_borrowed / total_holdings

    if current_utilization < optimal_utilization:
        rate = (current_utilization / optimal_utilization) * slope1
    else:
        rate = slope1 + (current_utilization - optimal_utilization) / (1 - optimal_utilization) * slope2

    cumulative_interest = duration * rate
    borrow_fee_amount = cumulative_interest * position_size

    return borrow_fee_amount


