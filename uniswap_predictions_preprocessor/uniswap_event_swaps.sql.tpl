select block_number, amount0, amount1
from eth.uniswap_v3.recent_event_swaps
where address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640'
and block_number = $block_number
