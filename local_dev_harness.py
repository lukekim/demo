#!/usr/bin/env python3

import os
import shutil
import runpy
from pathlib import Path
import spicepy

flight_address = 'grpc+tls://flight.spiceai.io'
api_key = os.environ['SPICE_API_KEY']
outputs_dir = Path('/tmp/spice-demo-outputs')
shutil.rmtree(outputs_dir, ignore_errors=True)
os.makedirs(outputs_dir)

runpy.run_path(
  'uniswap_predictions_preprocessor',
  init_globals={
    'SPICE_CLIENT': spicepy.Client(api_key, flight_address),
    'QUERY_VARIABLES': {
      'block_number': 17196976, # hardcode a recent block number
    },
    'OUTPUT_DIR': outputs_dir,
  },
  run_name="__main__",
)

print('user code completed, loading results up:')
with open(outputs_dir / 'results.csv', 'r', encoding='utf8') as f:
  print(f.read())
print('harness done')
