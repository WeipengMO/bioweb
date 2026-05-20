from pathlib import Path

import duckdb
import pandas as pd


def query_parquet(parquet_glob: str | Path, sql: str) -> pd.DataFrame:
    path = str(parquet_glob)
    with duckdb.connect(database=":memory:") as con:
        con.execute("CREATE VIEW source AS SELECT * FROM read_parquet(?)", [path])
        return con.execute(sql).df()

