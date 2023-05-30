

initial_conditions = {
    'genesis_traders': 1,
    'genesis_providers': 1,
}

sys_params = {
    # protocol params
    'base_fee': [0.05],
    'ratio_mult': [2],
    'max_margin': [20],
    'liquidation_threshold': [0.01],
    'rate_params': [[0.8, 0.1, 0.1]], # we need to figure this part out and optimize it
    'base_fees_swap': [{'BTC': 0.00025, 'ETH': 0.00025, 'SOL': 0.00015, 'USDC': 0.0001, 'USDT': 0.0001}],
    'om_fees_swap': [[0.01, 0.005]]
    # simulation params
}