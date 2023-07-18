#!/usr/bin/env python3

from spicepy import Client
import duckdb

def init_accumulator(duckdb: duckdb.DuckDBPyConnection):
  duckdb.sql("CREATE TABLE IF NOT EXISTS seen_eigenpods (num int)")
  existing_eigenpods_df = duckdb.sql("SELECT num from seen_eigenpods").df()
  if existing_eigenpods_df.empty:
    duckdb.sql("INSERT INTO seen_eigenpods VALUES (0)")

def process(context: dict, duckdb: duckdb.DuckDBPyConnection, spice_client: Client):
  data = spice_client.query(f"SELECT count(1) as cnt from eth.eigenlayer.eigenpods where block_number = {context['block_number']}")
  query_results = data.read_pandas()

  new_eigenpods = query_results["cnt"].iloc[0]

  # Set up the accumulator (only happens once)
  init_accumulator(duckdb)

  existing_eigenpods = duckdb.sql("SELECT num from seen_eigenpods").df()["num"].iloc[0]

  new_total_eigenpods = new_eigenpods + existing_eigenpods

  # Update the accumulator
  duckdb.sql(f"UPDATE seen_eigenpods SET num = {new_total_eigenpods}")

  # Temporary step
  duckdb.sql("""CREATE TABLE IF NOT EXISTS output.eigenpod_creation_counter (
                block_number BIGINT,
                eigenpods_created BIGINT
                )""")
  
  duckdb.sql(f"INSERT INTO output.eigenpod_creation_counter VALUES ({context['block_number']}, {new_total_eigenpods})")

  print("done!")