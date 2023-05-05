import pandas as pd

df = QUERY_RESULT
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

df.to_parquet(OUTPUT_PATH)
print(f"you did it! {len(df)}")
