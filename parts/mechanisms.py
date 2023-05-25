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

        if asset_yield > add_threshold:
            # The provider adds liquidity proportional to the excess yield
            liquidity_to_add = (liquidity_provider['funds'][asset] / asset_prices[asset]) * 10 * (asset_yield - add_threshold)
            liquidity_provider['funds'][asset] -= liquidity_to_add * asset_prices[asset]
            decision[asset] += liquidity_to_add

        elif asset_yield < remove_threshold:
            # The provider removes liquidity proportional to the shortfall
            liquidity_to_remove = liquidity_provider['liquidity'][asset] * 10 * (remove_threshold - asset_yield)
            liquidity_provider['liquidity'][asset] -= liquidity_to_remove
            decision[asset] -= liquidity_to_remove
    
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

def close_long(trader, timestep, asset, asset_price, liquidated, pool, rate_params):
    trader = copy.deepcopy(trader)

    usd_pnl = (asset_price - trader['positions_long'][asset]['entry_price']) * trader['positions_long'][asset]['quantity']
    pnl = usd_pnl / asset_price
    duration = timestep - trader[f'positions_long'][asset]['timestep']
    interest = calculate_interest(trader[f'positions_long'][asset]['quantity'], duration, asset, pool, rate_params)
    payout = trader[f'positions_long'][asset]['collateral'] - interest + pnl

    decision = {
        'quantity': trader['positions'][asset]['quantity'],
        'payout': payout,
        'interest_paid': interest,
        'PnL': pnl,
        'usd_pnl': usd_pnl,
        'liquidation': liquidated,
        'direction': 'close'
    }
    return decision


def close_short(trader, timestep, asset, asset_price, liquidated, pool, rate_params):
    trader = copy.deepcopy(trader)

    pnl = (trader['positions_short'][asset]['entry_price'] - asset_price) * trader['positions_short'][asset]['quantity']
    duration = timestep - trader[f'positions_short'][asset]['timestep']
    interest = calculate_interest(trader[f'positions_short'][asset]['quantity'], duration, asset, pool, rate_params)
    payout = trader[f'positions_short'][asset]['collateral']['amount'] - interest + pnl

    decision = {
        'quantity': trader['positions'][asset]['quantity'],
        'payout': payout,
        'interest_paid': interest,
        'PnL': pnl,
        'liquidation': liquidated,
        'denomination': trader[f'positions_short'][asset]['collateral']['denomination'], # {token: {quantity: 0, entry_price: 0, collateral: {amount: 0, denomination: "USDC"}, timestep: 0}}
        'direction': 'close'
    }
    return decision


def trading_decision(trader_passed, timestep, asset, asset_price, max_margin, liquidation_threshold, pool, rate_params):
    trader = copy.deepcopy(trader_passed)

    decision = {
        'long': None,
        'short': None
    }
    
    # Handle liquidations or position expirations
    if asset in trader['positions_long'] and trader['positions_long'][asset]['quantity'] != 0:
        if timestep - trader['positions_long'][asset]['timestep'] >= trader['avg_position_hold'] * np.random.uniform(low=0.8, high=1.4):
            decision['long'] = close_long(trader, timestep, asset, asset_price, False, pool, rate_params)
        # consider liquidation condition: 1% and consider entry collateral / position = 10% then if price dropped by 10% hence triggers liquidation hence
        # if collateral / position - (entry_price / asset_price - 1) > liquidation_condition then liquidate
        elif trader['positions_long'][asset]['collateral'] / trader['positions_long'][asset]['quantity'] - (trader['positions_long'][asset]['entry_price'] / asset_price - 1) > liquidation_threshold:
            decision['long'] = close_long(trader, timestep, asset, asset_price, True, pool, rate_params)
        
    elif asset in trader['positions_short'] and trader['positions_short'][asset]['quantity'] != 0:
        if timestep - trader['positions_short'][asset]['timestep'] >= trader['avg_position_hold'] * np.random.uniform(low=0.8, high=1.4):
            decision['short'] = close_short(trader, timestep, asset, asset_price, 0, 'short', pool, rate_params)
        # consider liquidation condition: 1% and consider entry collateral / position = 10% then price went up by 10% hence triggers liquidation hence
        # if collateral / position - (asset_price / entry_price - 1) > liquidation_condition then liquidate
        elif trader['positions_short'][asset]['collateral'] / trader['positions_long'][asset]['quantity'] - (asset_price / trader['positions_short'][asset]['entry_price'] - 1) > liquidation_threshold:
            decision['short'] = close_short(trader, timestep, asset, asset_price, 1, 'short', pool, rate_params)

    trade_action = random.random() # 1/4 enter a long, 1/4 enter a short, 1/2 do nothing. if position was closed then pass
    available_asset = pool['holdings'][asset] - (pool['oi_long'][asset] + pool['oi_short'][asset])

    if trade_action < 0.25 and decision['long'] == None: # enter a long
        asset_held = trader['liquidity'][asset]
        max_leverage_lot = asset_held * max_margin
        lot_size = np.random.uniform(low=0.01, high=(trader['risk_factor'] / 10)) * max_leverage_lot
        scal = 1
        while lot_size > available_asset:
            #print('long', lot_size, available_asset)
            lot_size = np.random.uniform(low=0.01, high=(trader['risk_factor'] / (10 + scal))) * max_leverage_lot
            scal += 1
            if scal == 20:
                break
        if scal < 20:
            interest = 0
            # charge interest if position exits
            if asset in trader['positions_long'] and trader['positions_long'][asset]['quantity'] != 0:
                duration = timestep - trader[f'positions_long'][asset]['timestep']
                interest = calculate_interest(trader[f'positions_long'][asset]['quantity'], duration, asset, pool, rate_params)

            required_collateral = lot_size / max_margin
            collateral_added = 0
            while collateral_added < required_collateral + interest:
                collateral_added = asset_held * random.random()
            
            decision['long'] = {
                'quantity': lot_size,
                'asset_price': asset_price,
                'collateral': collateral_added,
                'interest_paid': interest,
                'direction': "open"
            }

    elif trade_action > 0.75 and decision['short'] == None: # enter a short
        usd_liquidity = trader['liquidity']['USDC'] + trader['liquidity']['USDT']
        max_leverage_lot = (usd_liquidity / asset_price) * max_margin
        lot_size = np.random.uniform(low=0.01, high=(trader['risk_factor'] / 10)) * max_leverage_lot
        scal = 1
        while lot_size > available_asset:
            #print('short', lot_size, available_asset)
            lot_size = np.random.uniform(low=0.01, high=(trader['risk_factor'] / (10 + scal))) * max_leverage_lot
            scal += 1
            if scal == 20:
                break
        if scal < 20:

            interest = 0
            # charge interest if position exits
            if asset in trader['positions_short'] and trader['positions_short'][asset]['quantity'] != 0:
                duration = timestep - trader[f'positions_short'][asset]['timestep']
                interest = calculate_interest(trader[f'positions_short'][asset]['quantity'], duration, asset, pool, rate_params)
                denomination  = trader['positions_short'][asset]['collateral']['denomination']

            required_collateral = (lot_size * asset_price) / max_margin
            collateral_added = 0
            while collateral_added < required_collateral + interest:
                collateral_added = usd_liquidity * random.random()   

            swap = 0    
            # Choose the stable to use
            if asset not in trader['positions_short']:
                if trader['liquidity']['USDC'] > collateral_added:
                    denomination = 'USDC'
                elif trader['liquidity']['USDT'] > collateral_added:
                    denomination = 'USDT'
                else:
                    denomination = 'USDC'
                    swap = collateral_added - trader['liquidity']['USDC']
            
            decision['short'] = {
                'quantity': lot_size,
                'asset_price': asset_price,
                'collateral': collateral_added,
                'interest_paid': interest,
                'denomination': denomination,
                'swap': swap,
                'direction': 'open"'
            }

    return decision

def update_trader(trader, trade_decision, fees, asset, timestep):
    updated_trader = copy.deepcopy(trader)

    # If there's a long decision
    if trade_decision['long'] != None:
        if trade_decision['long']['direction'] == 'open':
            long_asset = trade_decision['long']
            long_fee = fees[0]
            long_quantity = long_asset['quantity']
            long_collateral = long_asset['collateral']
            
            # Deduct the fee from the liquidity
            updated_trader['liquidity'][asset] -= long_fee

            # Check if enough liquidity for the transaction
            if updated_trader['liquidity'][asset] < 0:
                return -1

            # Deduct the collateral from the liquidity
            updated_trader['liquidity'][asset] -= long_collateral

            # Check if enough liquidity for the transaction
            if updated_trader['liquidity'][asset] < 0:
                return -1

            # Update the positions
            if asset in updated_trader['positions_long']:
                updated_trader['positions_long'][asset]['entry_price'] = (long_asset['asset_price'] * long_quantity + updated_trader['positions_long'][asset]['entry_price'] * updated_trader['positions_long'][asset]['quantity']) / (long_quantity + updated_trader['positions_long'][asset]['quantity'])
                updated_trader['positions_long'][asset]['quantity'] += long_quantity
                updated_trader['positions_long'][asset]['collateral'] += long_collateral - trade_decision['long']['interest']
                updated_trader['positions_long'][asset]['timestep'] = timestep
            else:
                updated_trader['positions_long'][asset] = {
                    'quantity': long_quantity,
                    'entry_price': long_asset['asset_price'],
                    'collateral': long_collateral,
                    'timestep': timestep
                }

        elif trade_decision['long']['direction'] == 'close':
            long_asset = trade_decision['long']

            updated_trader['liquidity'][asset] += long_asset['payout']
            updated_trader['pnl'] += long_asset['usd_pnl']

            # detete position
            del trader['positions_long'][asset]
        
    # If there's a short decision
    if trade_decision['short'] != None:
        if trade_decision['short']['direction'] == 'open':
            short_asset = trade_decision['short']
            short_fee = fees[1]
            short_quantity = short_asset['quantity']
            short_collateral = short_asset['collateral']
            denomination = short_asset['denomination']

            # Deduct the fee from the liquidity
            updated_trader['liquidity'][denomination] -= short_fee

            # Check if enough liquidity for the transaction
            if updated_trader['liquidity'][denomination] < 0:
                return -1

            # Deduct the collateral from the liquidity
            updated_trader['liquidity'][denomination] -= short_collateral

            # Check if enough liquidity for the transaction
            if updated_trader['liquidity'][denomination] < 0:
                return -1

            # Update the positions
            if asset in updated_trader['positions_short']:
                updated_trader['positions_short'][asset]['entry_price'] = (short_asset['asset_price'] * short_quantity + updated_trader['positions_short'][asset]['entry_price'] * updated_trader['positions_short'][asset]['quantity']) / (short_quantity + updated_trader['positions_short'][asset]['quantity'])
                updated_trader['positions_short'][asset]['quantity'] += short_quantity
                updated_trader['positions_short'][asset]['collateral']['amount'] += short_collateral
                updated_trader['positions_short'][asset]['collateral']['denomination'] = denomination
                updated_trader['positions_short'][asset]['timestep'] = timestep  # {token: {quantity: 0, entry_price: 0, collateral: {amount: 0, denomination: "USDC"}, timestep: 0}}
            else:
                updated_trader['positions_short'][asset] = {
                    'quantity': short_quantity,
                    'entry_price': short_asset['asset_price'],
                    'collateral': {
                        'amount': short_collateral,
                        'denomination': denomination
                    },
                    'timestep': timestep
                }
        elif trade_decision['short']['direction'] == 'close':
            short_asset = trade_decision['short']

            updated_trader['liquidity'][short_asset['denomination']] += short_asset['payout']
            updated_trader['pnl'] += short_asset['usd_pnl']

            # detete position
            del trader['positions_short'][asset]

    return updated_trader

def update_pool_trade(pool, trader, trade_decision, fees, asset, cur_price):
    updated_pool = copy.deepcopy(pool)
    long_fee, short_fee = fees
    available_asset = updated_pool['holdings'][asset] - (updated_pool['oi_long'][asset] + updated_pool['oi_short'][asset])

    # Update the pool according to long decision
    if trade_decision['long'] != None:
        if trade_decision['long']['direction'] == 'open':
            long_asset = trade_decision['long']
            long_quantity = long_asset['quantity']
            long_collateral = long_asset['collateral']

            # Check if there is enough asset in the pool for the trade
            if available_asset < long_quantity:
                return -1

            # Increase the open interest
            updated_pool['oi_long'][asset] += long_quantity

            # Increase the trade volume
            updated_pool['volume'][asset] += long_quantity

            # Add to total fees collected
            updated_pool['total_fees_collected'][asset] += long_fee

            # Update loan book
            if trader['id'] not in updated_pool['loan_book_longs']:
                updated_pool['loan_book_longs'][trader['id']] = {}
            if asset not in updated_pool['loan_book_longs'][trader['id']]:
                updated_pool['loan_book_longs'][trader['id']][asset] = {'amount': long_quantity, 'collateral': long_collateral}
            else:
                updated_pool['loan_book_longs'][trader['id']][asset]['amount'] += long_quantity
                updated_pool['loan_book_longs'][trader['id']][asset]['collateral'] += long_collateral
                
        if trade_decision['long']['direction'] == 'close':
            long_asset = trade_decision['long']
            long_quantity = long_asset['quantity']
            pnl = long_asset['PnL']

            # Decrease the open interest and holdings
            updated_pool['oi_long'][asset] -= long_quantity
            updated_pool['holdings'][asset] -= pnl

            updated_pool['total_fees_collected'][asset] += long_fee

            # Update loan book
            del updated_pool['loan_book_longs'][trader['id']]

    # Update the pool according to short decision
    if trade_decision['short'] != None:
        if trade_decision['short']['direction'] == 'open':
            short_asset = trade_decision['short']
            short_quantity = short_asset['quantity']
            short_collateral = short_asset['collateral']

            # Increase the open interest
            updated_pool['oi_short'][asset] += short_quantity

            # Increase the trade volume
            updated_pool['volume'][asset] += short_quantity

            # Add to total fees collected
            updated_pool['total_fees_collected'][asset] += short_fee

            # Update loan book
            if trader['id'] not in updated_pool['loan_book_shorts']:
                updated_pool['loan_book_shorts'][trader['id']] = {}
            if asset not in updated_pool['loan_book_shorts'][trader['id']]:
                updated_pool['loan_book_shorts'][trader['id']][asset] = {'amount': short_quantity, 'collateral': short_collateral}
            else:
                updated_pool['loan_book_shorts'][trader['id']][asset]['amount'] += short_quantity
                updated_pool['loan_book_shorts'][trader['id']][asset]['collateral'] += short_collateral

        if trade_decision['short']['direction'] == 'close':
            short_asset = trade_decision['short']
            short_quantity =short_asset['quantity']
            pnl = short_asset['PnL']

            # Decrease the open interest and holdings
            updated_pool['oi_short'][asset] -= short_quantity
            updated_pool['holdings'][short_asset['denomination']] -= pnl

            updated_pool['total_fees_collected'][asset] += short_fee

            # Update loan book
            del updated_pool['loan_book_shorts'][trader['id']]
        
    # update pool open pnl based on cur_price and the postition of the trader
    pool['open_pnl_long'][asset] = trader['positions_short'][asset]['entry_price'] * trader['positions_short'][asset]['quantity'] - cur_price * trader['positions_short'][asset]['quantity']
    pool['open_pnl_short'][asset] = cur_price * trader['positions_long'][asset]['quantity'] - trader['positions_long'][asset]['entry_price'] * trader['positions_long'][asset]['quantity']

    return updated_pool

def trading_fee(pool, asset, trade_decision, rate_params, max_payoff_mult):
    # if new_utilization < custody.borrow_rate.optimal_utilization 
    #     entry_fee = (custody.fees.open_position * position.size)
    # else
    #     entry_fee = custody.fees.open_position * utilization_fee * size

    # where:
    #     utilization_fee = 1 + custody.fees.utilization_mult * (new_utilization - optimal_utilization) / (1 - optimal_utilization);
    #     optimum_utilization = optimum_utilization from custody
    #     new_utilization = custody.assets.locked + (position.size * custody.pricing.max_payoff_mult)
    long_fee = 0
    short_fee = 0
    optimal_utilization = rate_params[0]

    # Handle long
    if trade_decision['long'] != None:
        # Handle open
        if trade_decision['long']['direction'] == 'open':
            new_utilization = pool['oi_long'][asset] + (trade_decision['long']['quantity'] * max_payoff_mult)
            if new_utilization < optimal_utilization:
                long_fee = pool['fees']['open'] * trade_decision['long']['quantity']
            else:
                utilization_fee = 1 + pool['utilization_mult'][asset] * (new_utilization - optimal_utilization) / (1 - optimal_utilization)
                long_fee = pool['fees']['open'] * utilization_fee * trade_decision['long']['quantity']
        # Handle close
        elif trade_decision['long']['direction'] == 'close':
            long_fee = pool['fees']['close'] * trade_decision['long']['quantity']

    # Handle short
    if trade_decision['short'] != None:
        # Handle open
        if trade_decision['short']['direction'] == 'open':
            new_utilization = pool['oi_short'][asset] + (trade_decision['short']['quantity'] * max_payoff_mult)
            if new_utilization < optimal_utilization:
                long_fee = pool['fees']['open'] * trade_decision['short']['quantity']
            else:
                utilization_fee = 1 + pool['utilization_mult'][asset] * (new_utilization - optimal_utilization) / (1 - optimal_utilization)
                long_fee = pool['fees']['open'] * utilization_fee * trade_decision['short']['quantity']
        # Handle close
        elif trade_decision['short']['direction'] == 'close':
            short_fee = pool['fees']['close'] * trade_decision['short']['quantity']

    return [long_fee, short_fee]


#def trading_decision(trader_passed, timestep, asset, asset_price, max_margin, liquidation_threshold, pool, rate_params):

def swap_tokens_trader(trader_passed, amount, token_in, token_out, swap_fee):
    trader = copy.deepcopy(trader_passed)

    trader['liquidity'][token_in] -= amount - swap_fee[0]
    trader['liquidity'][token_out] += amount - swap_fee[1]

    return trader

# def trading_fee(pool, asset, trade_decision, rate_params, max_payoff_mult):
def swap_tokens_pool(pool, amount, token_in, token_out, swap_fee):

    pool = copy.deepcopy(pool)

    pool['holdings'][token_in] -= amount
    pool['holdings'][token_out] += amount
    pool['fees_collected'][token_in] += sum(swap_fee)

    return pool

def swap_fee_calc(pool, token_in, token_in_amt, token_out, token_out_amt, base_fees, om_fees, asset_prices):
    '''
    final fee = pool receiving swap fee + pool paying swap fee + pool receiving base fee + pool paying base fee

    base fees:
    btc: 0.00025
    eth: 0.00025
    sol: 0.00015
    usdc/usdt: 0.0001

    for pool receiving tokens (allocation % up)

    fee = A * (post trade ratio * 100 - target ratio * 100)^3 + fee optimal
    where A = (fee max - fee optional) / (max ratio * 100 - target ratio * 100) ^ 3

    for pool paying tokens (allocation % down)

    fee = A * (post trade ratio * 100 - target ratio * 100)^3 + fee optimal
    where A = (fee max - fee optional) / (min ratio * 100 - target ratio * 100) ^ 3
    
    '''

    # return ratio_fee
    tvl = pool_total_holdings(pool, asset_prices)
    fee_max = om_fees[0]
    fee_optimal = om_fees[1]

    target_ratio_in = pool['target_ratios'][token_in]
    post_trade_ratio_in = (pool['holdings'][token_in] + token_in_amt) * asset_prices[token_in] / tvl
    max_ratio_in = target_ratio_in + pool['deviation']

    # Calculate the pool receiving swap fee
    A_receiving = (fee_max - fee_optimal) / (max_ratio_in * 100 - target_ratio_in * 100) ** 3
    receiving_fee = A_receiving * (post_trade_ratio_in * 100 - target_ratio_in * 100) ** 3 + fee_optimal

    target_ratio_out = pool['target_ratios'][token_out]
    post_trade_ratio_out = (pool['holdings'][token_out] - token_out_amt) * asset_prices[token_out] / tvl
    min_ratio_out = target_ratio_out - pool['deviation']

    # Calculate the pool paying swap fee
    A_paying = (fee_max - fee_optimal) / (min_ratio_out * 100 - target_ratio_out * 100) ** 3
    paying_fee = A_paying * (post_trade_ratio_out * 100 - target_ratio_out * 100) ** 3 + fee_optimal

    # Get the pool receiving base fee and the pool paying base fee
    receiving_base_fee = base_fees[token_in]
    paying_base_fee = base_fees[token_out]

    return [receiving_fee + receiving_base_fee, paying_fee + paying_base_fee]
