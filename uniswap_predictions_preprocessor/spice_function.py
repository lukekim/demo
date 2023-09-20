#!/usr/bin/env python3

import numpy as np
import pandas as pd
import duckdb
import spicepy
from pathlib import Path
from string import Template
import sys
import os

def process(context: dict, 
            duckdb: duckdb.DuckDBPyConnection, 
            spice_client: spicepy.Client):
  api_key = os.environ["SPICE_API_KEY"]
  query = f"""
  select block_timestamp_last as ts, reserve0 / reserve1 as y
  from eth.uniswap_v2.pool_stats
  where pool_address = '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc'
  and block_number = {context['block_number']}
  """
  reader = spice_client.query(query)
  df = reader.read_pandas()
              
  if len(df) == 0:
      print("Skipping run due to no data")
      sys.exit(0)

  df["y"] = df["y"].astype(np.float32)
  df = df.groupby(by=["ts"]).mean().reset_index()
  df.sort_values("ts", inplace=True)
  pad_df = pd.DataFrame(data={"ts": np.arange(df["ts"].min(), df["ts"].max() + 1)})
  df = df.merge(pad_df, how="right", on="ts")
  df.sort_values("ts", inplace=True, ignore_index=True)
  df = df.interpolate(method="pad")
  print(df)

  duckdb.sql(f"INSERT INTO output.uniswap_v2_eth_usdc SELECT * FROM df")

  print("Done!")
