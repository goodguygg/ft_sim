import random
from .utils import *
import copy
import numpy as np

def liquidity_provider_decision(liquidity_provider, pool_yield, asset_prices, asset_volatility):
    assets = pool_yield.keys()
    decision = {asset: 0 for asset in assets}

    for asset in assets:
        add_threshold = copy.copy(liquidity_provider['add_threshold'][asset])
        remove_threshold = copy.copy(liquidity_provider['remove_threshold'][asset])

        # Adjust thresholds based on volatility
        if asset_volatility[asset] is not None:
            add_threshold += asset_volatility[asset]
            remove_threshold += asset_volatility[asset]

        asset_yield = pool_yield[asset]

        # print(f"yield {asset_yield} add thresh {add_threshold} rem thresh {remove_threshold}")

        if asset_yield > add_threshold:
            # The provider adds liquidity proportional to the excess yield
            liquidity_to_add = (liquidity_provider['funds'][asset] / asset_prices[asset]) * 10 * (asset_yield - add_threshold)
            liquidity_provider['funds'][asset] -= liquidity_to_add * asset_prices[asset]
            decision[asset] += liquidity_to_add
            #print(f"attempt to add {liquidity_to_add} {asset}")

        elif asset_yield < remove_threshold:
            # The provider removes liquidity proportional to the shortfall
            liquidity_to_remove = liquidity_provider['liquidity'][asset] * 10 * (remove_threshold - asset_yield)
            liquidity_provider['liquidity'][asset] -= liquidity_to_remove
            decision[asset] -= liquidity_to_remove
            #print(f"attempt to remove {liquidity_to_remove} {asset}")

    
    return decision

def liquidity_fee(pool, asset, provider_decision, asset_prices, base_fee, ratio_mult):
    # if token ratio is improved:           
    #     fee = base_fee / ratio_fee
    # otherwise:         
    #     fee = base_fee * ratio_fee
    # where:          
    # if new_ratio < ratios.target:
    #         ratio_fee = 1 + custody.fees.ratio_mult * (ratios.target - new_ratio) / (ratios.target - ratios.min);          
    # otherwise:
    #     ratio_fee = 1 + custody.fees.ratio_mult * (new_ratio - ratios.target) / (ratios.max - ratios.target);

    target_ratio = pool['target_ratios'][asset]
    tvl = pool_total_holdings(pool, asset_prices)
    current_ratio = (pool['holdings'][asset] * asset_prices[asset]) / tvl

    new_holding = pool['holdings'][asset] + provider_decision[asset]
    new_tvl = tvl + provider_decision[asset] * asset_prices[asset]
    new_ratio = new_holding * asset_prices[asset] / new_tvl

    if new_ratio - target_ratio > pool['deviation']:
        return -1

    if (new_ratio - current_ratio) < (target_ratio - current_ratio):
        ratio_fee = base_fee / ratio_mult
    else:
        if new_ratio < target_ratio:
            ratio_fee = 1 + ratio_mult * (target_ratio - new_ratio) / (pool['deviation'])
        else:
            ratio_fee = 1 + ratio_mult * (new_ratio - target_ratio) / (pool['deviation'])
        #ratio_fee = base_fee * ratio_fee

    return ratio_fee

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
    # print('provider_updated')
    return provider

def update_pool_liquidity(pool, liquidity_provider, lot_size, asset, provder_open_pnl):
    provider_id = liquidity_provider['id']
    tmp_pool = copy.deepcopy(pool)

    # If lot_size is negative, we check if the provider has a position in the pool
    if lot_size < 0:
        # print('liquidity removed')
        # If the provider is in the pool and the absolute value of lot_size is less than or equal to 
        # the liquidity they provided for the given asset, we update the pool
        lot_size = lot_size - provder_open_pnl
        if provider_id in tmp_pool['liquidity_providers'] and asset in tmp_pool['liquidity_providers'][provider_id] and abs(lot_size) <= tmp_pool['liquidity_providers'][provider_id][asset]:
            tmp_pool['holdings'][asset] += lot_size
            tmp_pool['liquidity_providers'][provider_id][asset] += lot_size
        else:
            # The provider doesn't have enough liquidity for the given asset to withdraw
            return -1
    else:
        # lot_size is positive
        # print('liquidity added')

        tmp_pool['holdings'][asset] += lot_size
        if provider_id in tmp_pool['liquidity_providers']:
            if asset in tmp_pool['liquidity_providers'][provider_id]:
                tmp_pool['liquidity_providers'][provider_id][asset] += lot_size
            else:
                tmp_pool['liquidity_providers'][provider_id][asset] = lot_size
        else:
            tmp_pool['liquidity_providers'][provider_id] = {asset: lot_size}

    return tmp_pool