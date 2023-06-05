import random
from .utils import *
import copy
import numpy as np

def liquidity_provider_decision(liquidity_provider, pool_yield, asset_prices, asset_volatility):
    assets = pool_yield.keys()
    decision = {asset: 0 for asset in assets}
    liquidity_provider = copy.deepcopy(liquidity_provider)

    for asset in assets:
        add_threshold = liquidity_provider['add_threshold'][asset]
        remove_threshold = liquidity_provider['remove_threshold'][asset]

        # Adjust thresholds based on volatility
        if asset_volatility[asset] is not None:
            add_threshold += asset_volatility[asset]
            remove_threshold += asset_volatility[asset]

        asset_yield = pool_yield[asset]

        # print(f"yield {asset_yield} add thresh {add_threshold} rem thresh {remove_threshold}")

        if asset_yield > add_threshold:
            # The provider adds liquidity proportional to the excess yield
            liquidity_to_add = (liquidity_provider['funds'][asset] / asset_prices[asset]) * 10 * (asset_yield - add_threshold)
            decision[asset] += liquidity_to_add
            #print(f"attempt to add {liquidity_to_add} {asset}")

        elif asset_yield < remove_threshold:
            # The provider removes liquidity proportional to the shortfall
            liquidity_to_remove = liquidity_provider['liquidity'][asset] * 10 * (remove_threshold - asset_yield)
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
            ratio_fee = (1 + ratio_mult * (target_ratio - new_ratio) / (pool['deviation']))/100
        else:
            ratio_fee = (1 + ratio_mult * (new_ratio - target_ratio) / (pool['deviation']))/100

        #ratio_fee = base_fee * ratio_fee

    return ratio_fee

def update_provider(liquidity_provider, lot_size, asset, fee_amount, lp_tokens, provder_open_pnl):
    provider = copy.deepcopy(liquidity_provider)
    # print(lp_tokens)
    # handle case for protocol provider
    if provider['id'] == 0:
        provider['liquidity'][asset] += lot_size
        provider['pool_share'] += lp_tokens
        return provider

    # in case of liquidity removal update the lot_size and the amount with the provider's pnl
    if lot_size < 0 and provider['liquidity'][asset] >= lot_size:
        provider['liquidity'][asset] += lot_size
        provider['funds'][asset] -= lot_size - fee_amount - provder_open_pnl
        provider['pool_share'] += lp_tokens
    # check if the provider has enough funds to provide the liquidity
    elif lot_size > 0 and provider['funds'][asset] >= lot_size:
        provider['liquidity'][asset] += lot_size - fee_amount
        provider['funds'][asset] -= lot_size
        provider['pool_share'] += lp_tokens
    else:
        return -1
    # print('provider_updated')
    return provider

def update_pool_liquidity(pool, liquidity_provider, lot_size, asset, provder_open_pnl, fee_amount, lp_tokens, prot_lp, asset_prices):
    provider_id = liquidity_provider['id']
    tmp_pool = copy.deepcopy(pool)

    # print(tmp_pool['lp_shares'], lp_tokens, prot_lp, lot_size)

    # If lot_size is negative, we check if the provider has a position in the pool
    if lot_size < 0:
        # print('liquidity removed')
        # If the provider is in the pool and the absolute value of lot_size is less than or equal to 
        # the liquidity they provided for the given asset, we update the pool
        if provider_id in tmp_pool['liquidity_providers'] and asset in tmp_pool['liquidity_providers'][provider_id] and abs(lot_size) <= tmp_pool['liquidity_providers'][provider_id][asset]:
            tmp_pool['holdings'][asset] += lot_size - provder_open_pnl + abs(fee_amount)
            tmp_pool['liquidity_providers'][provider_id][asset] = liquidity_provider['liquidity'][asset]
            tmp_pool['lp_shares'] += lp_tokens
        else:
            # The provider doesn't have enough liquidity for the given asset to withdraw or is not in the pool
            return -1
    else:
        # lot_size is positive
        # print('liquidity added')
        tmp_pool['holdings'][asset] += lot_size
        tmp_pool['lp_shares'] += lp_tokens
        if provider_id in tmp_pool['liquidity_providers']:
            if asset in tmp_pool['liquidity_providers'][provider_id]:
                tmp_pool['liquidity_providers'][provider_id][asset] += lot_size
            else:
                tmp_pool['liquidity_providers'][provider_id][asset] = lot_size
        else:
            tmp_pool['liquidity_providers'][provider_id] = {asset: lot_size}

    tmp_pool['holdings'][asset] += abs(fee_amount)
    tmp_pool['liquidity_providers']["0"][asset] += abs(fee_amount)
    tmp_pool['lp_shares'] += prot_lp
    tmp_pool['total_fees_collected'][asset] += abs(fee_amount)
    tmp_pool['tvl'] = pool_total_holdings(tmp_pool, asset_prices)
    # print("////")
    # print(tmp_pool['lp_shares'], lp_tokens, prot_lp)


    return tmp_pool