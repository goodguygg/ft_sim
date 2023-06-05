from .utilities.utils import *
from .utilities.liq_mech import *
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
        asset_volatility = get_asset_volatility(pool['assets'], timestep)
        fees_collected.append({ast: 0 for ast in pool['assets']})
        price_dict = fetch_asset_prices(pool['assets'], timestep)

        # print(pool['yield'])

        for liquidity_provider_id in liquidity_providers.keys():
            if liquidity_provider_id == 0:
                continue
            liquidity_provider = liquidity_providers[liquidity_provider_id]
            asset_prices = get_asset_prices(price_dict)
            # print("ass vol",asset_volatility)
            provider_decision = liquidity_provider_decision(liquidity_provider, pool['yield'], asset_prices, asset_volatility)

            for asset in provider_decision.keys():
                if provider_decision[asset] == 0:
                    continue
                elif provider_decision[asset] < 0:
                    # check provider in the pool and change his decision to withdraw all liquidity (assumption that if someone wants out they withdraw all
                    provider_id = liquidity_provider['id']
                    if provider_id in pool['liquidity_providers']:
                        if asset in pool['liquidity_providers'][provider_id]:
                            provider_decision[asset] = pool['liquidity_providers'][provider_id][asset]
                        else:
                            continue
                    else:
                        continue

                # # consider the open pnl of the pool in proportion to the provider
                provder_open_pnl = (liquidity_provider['liquidity'][asset] / pool['holdings'][asset]) * (pool['open_pnl_long'][asset] + pool['open_pnl_short'][asset])
                lot_size = provider_decision[asset]
                tvl = pool_total_holdings(pool, asset_prices)
                pool_size_change = lot_size * asset_prices[asset] / tvl
                #print(pool_size_change, lot_size, asset_prices[asset], tvl, pool['lp_shares'])
                lp_tokens = pool_size_change * pool['lp_shares']

                if lp_tokens < 0 and liquidity_provider['pool_share'] < abs(lp_tokens):
                    lp_tokens = -liquidity_provider['pool_share']
                    lot_size = (lp_tokens / pool['lp_shares']) * (tvl / asset_prices[asset])

                # Fetch the fee amount
                fee_perc = liquidity_fee(pool, asset, provider_decision, asset_prices, params['base_fee'], params['ratio_mult'])

                # fee amount returns -1 if the provider decision if does not pass the constraints
                if fee_perc == -1:
                    continue
                
                # calculate the fee
                fee_amount = lot_size * fee_perc
                prot_lp = lp_tokens * fee_perc
                lp_tokens = lp_tokens - prot_lp

                # print(lot_size, asset, asset_prices[asset], lp_tokens, prot_lp, fee_perc, provder_open_pnl)
                # update the provider and pool values
                prov_temp = update_provider(liquidity_provider, lot_size, asset, fee_amount, lp_tokens, provder_open_pnl)
                prot_tmp = update_provider(liquidity_providers[0], abs(fee_amount), asset, 0, prot_lp, 0)
                pool_tmp = update_pool_liquidity(pool, liquidity_provider, lot_size, asset, provder_open_pnl, fee_amount, lp_tokens, prot_lp, asset_prices)
                if pool_tmp == -1 or prov_temp == -1:
                    # if pool_tmp == -1:
                    #     print('denied pool', pool_tmp) 
                    # if prov_temp == -1:
                    #     print('denied prov', prov_temp) 
                    continue
                
                liquidity_provider = prov_temp
                liquidity_providers[0] = prot_tmp
                pool = pool_tmp
                fees_collected[p][asset] += fee_amount

            liquidity_providers[liquidity_provider_id] = liquidity_provider
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