
# let ratios = TokenRatios {
#     target: 5000,
#     min: 1000,
#     max: 9000,
# };

from parts.utils import *

initial_conditions = {
    'genesis_traders': 30,
    'genesis_providers': 20,
}

sys_params = {
    'base_fee': [0.05],
    'ratio_mult': [2],
    'max_margin': [50],
    'liquidation_threshold': [0.01],
    'rate_params': [[0.8, 0.1, 0.1]],
    'base_fees_swap': [{'BTC': 0.00025, 'ETH': 0.00025, 'SOL': 0.00015, 'USDC': 0.0001, 'USDT': 0.0001}],
    'om_fees_swap': [[0.01, 0.005]]
}

    
# sys_params = {
#     'borrow_fee': [borrow_fee]
#     'open_position_fee': [open_position_fee], 
#     'close_position_fee': [close_position_fee], 
#     'add_liquidity_fee': [add_liquidity_fee], 
#     'remove_liquidity_fee': [remove_liquidity_fee], 
#     'swap_fee': [swap_fee],
#     'liquidation_penalty': [liquidation_penalty],
#     'liquidation_threshold': [liquidation_threshold] # ratio of loan value to collateral value
#     'optimal_utilization': [optimal_utilization], 
#     'utilization_multiplier': [utilization_multiplier],
#     'oracle_attack_probability': [0.01],
#     'number_of_agents': [agents_func],
#     'number_of_pools': [1],
#     'tokens': [{}],
#     'token_price': [token_price]
# }

