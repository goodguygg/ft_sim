

initial_conditions = {
    'genesis_traders': 100,
    'genesis_providers': 30,
    'num_of_hrs': 311,
    'initial_liquidity': {'BTC': 1, 'ETH': 13, 'SOL': 625, 'USDC': 20000, 'USDT': 20000},
    'pool_fees': {'open': 0.01, 'close': 0.01}
}

sys_params = {
    # protocol params
    'base_fee': [0.05],
    'ratio_mult': [2],
    'max_margin': [{'BTC': 50, 'ETH': 50, 'SOL': 50, 'USDC': 50, 'USDT': 50}],
    'liquidation_threshold': [{'BTC': 0.02, 'ETH': 0.02, 'SOL': 0.02, 'USDC': 0.02, 'USDT': 0.02}],
    'rate_params': [[0.8, 0.1, 0.1]], # we need to figure this part out and optimize it
    'base_fees_swap': [{'BTC': 0.00025, 'ETH': 0.00025, 'SOL': 0.00015, 'USDC': 0.0001, 'USDT': 0.0001}],
    'om_fees_swap': [[0.01, 0.005]],
    # simulation params
    'trader_traction': [0.0],
    'lp_traction': [0.0],
    'trade_chance': [[0.1, 0.9]], # 1st value is the barrier for longs, second is for shorts
    'swap_chance': [[0.1, 0.9]], # chance of swapping in and swapping out tokens 
    'event': ['FTX'],
    'start_date': ['2022-11-01']
}