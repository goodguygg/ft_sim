from .utils import *
from .mechanisms import liquidity_provider_decision, liquidity_fee
import copy

def liquidity_policy(params, substep, state_history, previous_state):
    liquidity_providers = copy.deepcopy(previous_state['liquidity_providers'])
    pools = copy.deepcopy(previous_state['pools'])
    fees_collected = []
    timestep = previous_state['timestep']
    print(timestep, 'liquidity')

    p = 0
    for pool_id in pools.keys():
        pool = pools[pool_id]
        asset_prices = get_asset_prices(pool['assets'], timestep)
        asset_volatility = get_asset_volatility(pool['assets'], timestep)
        fees_collected.append({ast: 0 for ast in pool['assets']})

        for liquidity_provider_id in liquidity_providers.keys():
            liquidity_provider = liquidity_providers[liquidity_provider_id]
            provider_decision = liquidity_provider_decision(liquidity_provider, pool['yield'], asset_prices, asset_volatility)
            for asset in provider_decision.keys():
                if provider_decision[asset] == 0:
                    continue
                elif provider_decision[asset] < 0:
                    # check provider in the pool and change his decision to withdraw all liquidity (assumption that if someone wants out they withdraw all
                    provider_id = liquidity_provider['id']
                    if provider_id in pool['liquidity_providers']:
                        provider_decision[asset] = pool['liquidity_providers'][provider_id][asset]
                    else:
                        continue

                # Fetch the fee amount
                fee_perc = liquidity_fee(pool, asset, provider_decision, asset_prices, params['base_fee'], params['ratio_mult'])

                # fee amount returns -1 if the provider decision if does not pass the constraints
                if fee_perc == -1:
                    continue
                
                # calculate fees
                fee_amount = provider_decision[asset] * fee_perc
                lot_size = provider_decision[asset] - fee_amount

                # consider the open pnl of the pool in proportion to the provider
                provder_open_pnl = (liquidity_provider['liquidity'][asset] / pool['holdings'][asset]) * (pool['open_pnl_long'][asset] + pool['open_pnl_short'][asset]) / asset_prices[asset]

                # update the provider and pool values
                prov_temp = update_provider(pool, liquidity_provider, provider_decision[asset], lot_size, asset, provder_open_pnl)
                pool_tmp = update_pool_liquidity(pool, liquidity_provider, lot_size, asset, provder_open_pnl)
                if pool_tmp == -1 or prov_temp == -1:
                    continue

                liquidity_provider = prov_temp
                pool = pool_tmp
                fees_collected[p][asset] += fee_amount

        pools[pool_id] = pool
        p += 1
        
    action = {
        'liquidity_providers': liquidity_providers,
        'pools': pools,
        'fees_collected': fees_collected
    }

    return action

def liquidity_providers_update(params, substep, state_history, previous_state, policy):
    key = 'liquidity_providers'
    value = policy['liquidity_providers']
    return (key, value)

def pool_liquidity_update(params, substep, state_history, previous_state, policy):
    key = 'pools'
    value = policy['pools']
    return (key, value)

def treasury_liquidity_update(params, substep, state_history, previous_state, policy):
    key = 'treasury'
    value = {asset: previous_state['treasury'][asset] + sum([policy['fees_collected'][i][asset] for i in range(len(policy['fees_collected']))]) for asset in previous_state['treasury'].keys()}
    return (key, value)