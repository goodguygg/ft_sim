
import pandas as pd
import numpy as np
import copy
import os
import random

def get_asset_prices(assets, timestep):
    asset_prices = {}
    for asset in assets:
        try:
            file_path = os.path.join('data', f'{asset}.xlsx')
            df = pd.read_excel(file_path)
        except:
            file_path = os.path.join('parts', 'data', f'{asset}.xlsx')
            df = pd.read_excel(file_path)    
        price = df.loc[timestep, 'Close']
        asset_prices.update({asset: price})
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

def update_provider(pool, liquidity_provider, amount, lot_size, asset, provder_open_pnl):
    provider = copy.deepcopy(liquidity_provider)

    # in case of liquidity removal update the lot_size and the amount with the provider's pnl
    if lot_size < 0:
        provider['liquidity'][asset] = provider['liquidity'][asset] + provder_open_pnl
        amount = amount - provder_open_pnl
        lot_size = lot_size - provder_open_pnl
    # check if the provider has enough funds to provide the liquidity
    if provider['funds'][asset] >= amount:
        provider['funds'][asset] -= amount
        provider['liquidity'][asset] += lot_size
    else:
        return -1
    
    return provider

def update_pool_liquidity(pool, liquidity_provider, lot_size, asset, provder_open_pnl):
    provider_id = liquidity_provider['id']
    tmp_pool = copy.deepcopy(pool)

    # If lot_size is negative, we check if the provider has a position in the pool
    if lot_size < 0:
        # If the provider is in the pool and the absolute value of lot_size is less than or equal to 
        # the liquidity they provided for the given asset, we update the pool
        amount = amount - provder_open_pnl
        lot_size = lot_size - provder_open_pnl
        
        if provider_id in tmp_pool['liquidity_providers'] and abs(lot_size) <= tmp_pool['liquidity_providers'][provider_id][asset]:
            tmp_pool['holdings'][asset] += lot_size
            tmp_pool['liquidity_providers'][provider_id][asset] += lot_size
        else:
            # The provider doesn't have enough liquidity for the given asset to withdraw
            return -1
    else:
        # lot_size is positive
        tmp_pool['holdings'][asset] += lot_size
        if provider_id in tmp_pool['liquidity_providers']:
            if asset in tmp_pool['liquidity_providers'][provider_id]:
                tmp_pool['liquidity_providers'][provider_id][asset] += lot_size
            else:
                tmp_pool['liquidity_providers'][provider_id][asset] = lot_size
        else:
            tmp_pool['liquidity_providers'][provider_id] = {asset: lot_size}

    return tmp_pool

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


