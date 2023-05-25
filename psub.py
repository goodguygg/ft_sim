from parts.liquidity import *
from parts.trading import *
from parts.traction import *

partial_state_update_block = [
    {
        # liquidity.py
        'policies': {
            'liquidity': liquidity_policy,
        },
        'variables': {
            'liquidity_providers': liquidity_providers_update,
            'pools': pool_liquidity_update,
            # 'treasury': treasury_liquidity_update,
        }
    },
    {
        # trading.py
        'policies': {
            'trading': trading_policy,
        },
        'variables': {
            'traders': traders_update,
            'pools': pool_trading_update,
            'liquidations': liquidations_uodate,
            # 'liquidity_providers': distribution_providers_update,
            # 'treasury': treasury_update,
            # 'nominal_exposure': nominal_exposure_update,
            # 'oracle_attack': oracle_attack_update
        }
    },
    # {
    #     # interest.py
    #     'policies': {
    #         'charge_interest': charge_interest_policy,
    #     },
    #     'variables': {
    #         'traders': traders_interes_update,
    #         'pools': pool_interest_update,
    #         'liquidity_providers': providers_interest_update,
    #         'treasury': treasury_interest_update,
    #     }
    # },
    # {
    #     # traction.py
    #     'policies': {
    #         'generate_more_agents': more_agents_policy,
    #     },
    #     'variables': {
    #         'liquidity_providers': more_providers_update,
    #         'traders': more_traders_update,
    #     }
    # },
]