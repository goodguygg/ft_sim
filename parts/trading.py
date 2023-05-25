from .utilities.utils import *
from .utilities.trad_mech import *
from .utilities.swap_mech import *

def trading_policy(params, substep, state_history, previous_state):

    traders = copy.deepcopy(previous_state['traders'])
    pools = copy.deepcopy(previous_state['pools'])
    fees_collected = []
    provider_pnl = []
    timestep = previous_state['timestep']
    treasury = copy.deepcopy(previous_state['treasury'])
    liquidations = previous_state['liquidations']

    print(timestep, 'traders')

    p = 0
    for pool_id in pools.keys():
        pool = pools[pool_id]
        fees_collected.append({ast: 0 for ast in pool['assets']})
        provider_pnl.append({ast: 0 for ast in pool['assets']})
        price_dict = fetch_asset_prices(pool['assets'], timestep)

        for trader_id in traders.keys():
            trader = traders[trader_id]
            asset_prices = get_asset_prices(price_dict)

            for asset in pool['assets']:
                if asset == 'USDT' or asset == 'USDC':
                    continue

                trade_decision = trading_decision(trader, timestep, asset, asset_prices[asset], params['max_margin'], params['liquidation_threshold'], pool, params['rate_params'])

                if trade_decision['long'] == None and trade_decision['short'] == None:
                    continue

                if trade_decision['short'] != None and trade_decision['short']['direction'] == 'open':
                    if trade_decision['short']['swap'] != 0:
                        tokens_in = trade_decision['short']['denomination']
                        tokens_out = 'USDT' if tokens_in == 'USDC' else 'USDC'
                        swap_fee = swap_fee_calc(pool, tokens_in, trade_decision['short']['swap'], tokens_out, trade_decision['short']['swap'], params['base_fees_swap'], params['om_fees_swap'], asset_prices)
                        trader = swap_tokens_trader(trader, trade_decision['short']['swap'], tokens_in, tokens_out, swap_fee)
                        pool = swap_tokens_pool(pool, trade_decision['short']['swap'], tokens_in, tokens_out, swap_fee)

                        # pay the fee to lps andtreasury
                        if trade_decision['long'] != None:
                            provider_pnl[p][asset] += swap_fee[0] * 0.7
                            treasury[asset] += swap_fee[0] * 0.3
                            if trade_decision['long']['direction'] == 'close':
                                liquidations += trade_decision['long']['liquidations']

                        if trade_decision['short'] != None:
                            provider_pnl[p][trade_decision['short']['denomination']] += swap_fee[1] * 0.7
                            treasury[trade_decision['short']['denomination']] += swap_fee[1] * 0.3
                            if trade_decision['short']['direction'] == 'close':
                                liquidations += trade_decision['short']['liquidations']

                # Fetch the fee amount
                fees = trading_fee(pool, asset, trade_decision, params['rate_params'], params['ratio_mult'])

                # update the provider and pool values
                trader_temp = update_trader(trader, trade_decision, fees, asset, timestep)
                pool_tmp = update_pool_trade(pool, trader, trade_decision, fees, asset, asset_prices[asset])

                if pool_tmp == -1 or trader_temp == -1:
                    continue

                trader = trader_temp
                pool = pool_tmp
                fees_collected[p][asset] += fees[0] * asset_prices[asset] + fees[1]

                # pay the fee to lps andtreasury, consider the pnl of the providers
                if trade_decision['long'] != None:
                    # distribute fees to providers
                    provider_pnl[p][asset] += fees[0] * 0.7
                    treasury[asset] += fees[0] * 0.3
                    if trade_decision['long']['direction'] == 'close':
                        # subtract pnl from providers
                        provider_pnl[p][trade_decision['short'][asset]] -= trade_decision['long']['PnL']
                        liquidations += trade_decision['long']['liquidations']

                if trade_decision['short'] != None:
                    # distribute fees to providers
                    provider_pnl[p][trade_decision['short']['denomination']] += fees[1] * 0.7
                    treasury[trade_decision['short']['denomination']] += fees[1] * 0.3
                    if trade_decision['short']['direction'] == 'close':
                        # subtract pnl from providers
                        provider_pnl[p][trade_decision['short']['denomination']] -= trade_decision['short']['PnL']
                        liquidations += trade_decision['short']['liquidations']

            
            # asset_prices = get_asset_prices(pool['assets'], timestep)
            # for asset in pool['assets']:
            #     swaping_decision = swap_decision

        pools[pool_id] = pool
        p += 1
        
    action = {
        'traders': traders,
        'pools': pools,
        'fees_collected': fees_collected,
        'treasury': treasury,
        'provider_pnl': provider_pnl,
        'liquidations': liquidations
    }

    return action

def traders_update(params, substep, state_history, previous_state, policy):
    key = 'traders'
    value = policy['traders']
    return (key, value)

def pool_trading_update(params, substep, state_history, previous_state, policy):
    key = 'pools'
    value = policy['pools']
    return (key, value)

def liquidations_uodate(params, substep, state_history, previous_state, policy):
    key = 'liquidations'
    value = policy['liquidations']
    return (key, value)

def distribution_providers_update(params, substep, state_history, previous_state, policy):
    key = 'liqudiity_providers'
    provider_rewards = policy['provider_pnl']
    providers = copy.deepcopy(previous_state['liquidity_providers'])
    pools = copy.deepcopy(previous_state['pools'])
    pool_num = 0
    for pool_id in pools.keys():
        pool = pools[pool_id]
        for provider_id in providers.keys():
            for asset in providers[provider_id]['liquidity'].keys():
                providers[provider_id]['funds'][asset] += provider_rewards[pool_num][asset] * (providers[provider_id]['liquidity'][asset] / pool['holdings'][asset])
        pool_num += 1

    value = providers
    return (key, value)

def treasury_update(params, substep, state_history, previous_state, policy):
    key = 'treasury'
    value = policy['treasury']
    return (key, value)

# def nominal_exposure_update(params, substep, state_history, previous_state, policy):
#     key = 'nominal_exposure'
#     value = previous_state['nominal_exposure']
#     return (key, value)

# def oracle_attack_update(params, substep, state_history, previous_state, policy):
#     key = 'oracle_attack'
#     value = previous_state['oracle_attack']
#     return (key, value)