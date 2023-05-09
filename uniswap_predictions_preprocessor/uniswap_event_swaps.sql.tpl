select block_number, reserve0 as amount0, reserve1 as amount1
from eth.uniswap_v2.recent_pool_stats
where pool_address = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'
and block_number = $block_number
