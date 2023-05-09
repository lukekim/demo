#!/usr/bin/env python3

import numpy as np
import pandas as pd
from pathlib import Path
from string import Template
import sys
import os

# Runner exposes three global variables:
# - SPICE_CLIENT: a spice client initialised with our API key to allow us to run queries
# - QUERY_VARIABLES: a dictionary of available variables for running our queries
# - OUTPUT_DIR: where to write our results that can either be written as a .sql or .parquet file

template_filename = 'uniswap_event_swaps.sql.tpl' if QUERY_VARIABLES.get('block_number') else 'uniswap_event_swaps_latest.sql.tpl'
template_filename = os.path.join(os.path.dirname(__file__), template_filename)
query_template = Template(__loader__.get_data(template_filename).decode("utf8"))
query = query_template.substitute(QUERY_VARIABLES)
try:
    reader = SPICE_CLIENT.query(query)
    df = reader.read_pandas()
except Exception as e:
    print(f"Error running '{query}': {e}", file=sys.stderr)
    raise e

if len(df) == 0:
    print("Skipping run due to no data")
    sys.exit(0)

df["amount0"] = df["amount0"].astype(np.float32).apply(np.abs)
df["amount1"] = df["amount1"].astype(np.float32).apply(np.abs)
df = df.groupby(by=["block_number"]).mean()
df.sort_values("block_number", inplace=True)
df["y"] = df["amount0"] / df["amount1"]
df = df.drop(columns=["amount0", "amount1"]).reset_index()
df = df.rename(columns={"block_number": "ts"})
pad_df = pd.DataFrame(data={"ts": np.arange(df["ts"].min(), df["ts"].max() + 1)})
df = df.merge(pad_df, how="right", on="ts")
df.sort_values("ts", inplace=True, ignore_index=True)
df = df.interpolate(method="pad")
df = df.set_index('ts')

df.to_csv(OUTPUT_DIR / "results.csv")

# Read the content of the .csv file
with open(OUTPUT_FILE, "r") as file:
    content = file.read()

# Print the content of the .csv file to stdout
print(content)

print(f"done! {len(df)}")
