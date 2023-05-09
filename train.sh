#!/bin/bash
PAYLOAD=$(cat << EOF
{
  "inference_query": "select block_number as ts, abs(cast(amount0 as double)) as amount0, abs(cast(amount1 as double)) as amount1 from eth.uniswap_v3.recent_event_swaps where address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640' order by block_number limit 20",
  "model_type": "tf_uniswapv3_usdc_eth_aggregated",
  "lookback_size": 5,
  "forecast_size": 1,
  "epochs": 1,
  "train_query": "select block_number as ts, abs(cast(amount0 as double)) as amount0, abs(cast(amount1 as double)) as amount1 from eth.uniswap_v3.event_swaps where address = '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640' order by block_number limit 100"
}
EOF
)
curl --data "$PAYLOAD" "https://data.spiceai.io/v0.1/train?api_key=$SPICE_API_KEY"
