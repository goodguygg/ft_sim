from parts.utilities.utils import * 
from sys_params import initial_conditions

def generate_providers(n_providers):
    liquidity_providers = {}
    assets = ['BTC', 'ETH', 'SOL', 'USDC', 'USDT']
    price_dict = fetch_asset_prices(assets, 0)
    asset_prices = get_asset_prices(price_dict)    
    for i in range(n_providers):
        thresholds = {asset: np.random.uniform(low=0, high=0.1) for asset in assets}
        liquidity_provider = {
            'id': i,
            'funds': {asset: np.random.uniform(low=100, high=5000)/asset_prices[f'{asset}'] for asset in assets},
            'liquidity': {asset: 0 for asset in assets},
            'add_threshold': thresholds,
            'remove_threshold': {asset: (thresholds[f'{asset}'] * 0.7) for asset in assets},
        }
        liquidity_providers[i] = liquidity_provider
        print("theresholds", thresholds)
    return liquidity_providers

def generate_traders(n_traders):
    traders = {}
    assets = ['BTC', 'ETH', 'SOL', 'USDC', 'USDT']
    price_dict = fetch_asset_prices(assets, 0)
    asset_prices = get_asset_prices(price_dict)
    for i in range(n_traders):
        trader = {
            'id': i,
            'liquidity': {asset: np.random.uniform(low=100, high=5000)/asset_prices[f'{asset}'] for asset in assets},  # Sample initial liquidity from some distribution
            'positions_long': {},  # {token: {quantity: 0, entry_price: 0, collateral: 0, timestep: 0}}
            'positions_short': {},  # {token: {quantity: 0, entry_price: 0, collateral: {amount: 0, denomination: "USDC"}, timestep: 0}}
            'PnL': 0,
            'avg_position_hold': np.random.uniform(low=1, high=10),
            'risk_factor': np.random.uniform(low=1, high=10)
        }
        traders[i] = trader
    return traders

def generate_pools(n_pools):
    pools = {}
    for i in range(n_pools):
        #token_a, token_b = np.random.choice(tokens, size=2, replace=False)  # Choose two different tokens for the pool
        pool = {
            'id': i,
            'assets': ['BTC', 'ETH', 'SOL', 'USDC', 'USDT'],
            'holdings': {'BTC': 10, 'SOL': 2500, 'ETH': 110, 'USDC': 450000, 'USDT': 450000},
            'oi_long': {'BTC': 0, 'SOL': 0, 'ETH': 0, 'USDC': 0, 'USDT': 0},
            'oi_short': {'BTC': 0, 'SOL': 0, 'ETH': 0, 'USDC': 0, 'USDT': 0},
            'open_pnl_long': {'BTC': 0, 'SOL': 0, 'ETH': 0, 'USDC': 0, 'USDT': 0},
            'open_pnl_short': {'BTC': 0, 'SOL': 0, 'ETH': 0, 'USDC': 0, 'USDT': 0},
            'volume': {'BTC': 0, 'SOL': 0, 'ETH': 0, 'USDC': 0, 'USDT': 0},
            'total_fees_collected': {'BTC': 0, 'SOL': 0, 'ETH': 0, 'USDC': 0, 'USDT': 0},
            'yield': {'BTC': 0.01, 'SOL': 0.01, 'ETH': 0.01, 'USDC': 0.01, 'USDT': 0.01},
            'target_ratios': {'BTC': 0.2, 'SOL': 0.2, 'ETH': 0.2, 'USDC': 0.2, 'USDT': 0.2},
            'deviation': 0.05,
            'liquidity_providers': {},  # {agent_id: liquidity_provided}
            'loan_book_longs': {},  # {agent_id: {token: {amount, collateral}}}
            'loan_book_shorts': {},  # {agent_id: {token: {amount, collateral}}}
            'utilization_mult': {'BTC': 0.01, 'SOL': 0.01, 'ETH': 0.01, 'USDC': 0.01, 'USDT': 0.01},
            'fees': {'open': 0.01, 'close': 0.01}
        }
    pools[i] = pool
    return pools

genesis_states = {
    'traders': generate_traders(initial_conditions['genesis_traders']),
    'liquidity_providers': generate_providers(initial_conditions['genesis_providers']),    
    'pools': generate_pools(1),
    'treasury': {'BTC': 0, 'SOL': 0, 'ETH': 0, 'USDC': 0, 'USDT': 0},
    'liquidations': 0,
    'num_of_trades': 0,
    'num_of_swaps': 0
    # 'nominal_exposure': 0,
    # 'oracle_attack': False
}
