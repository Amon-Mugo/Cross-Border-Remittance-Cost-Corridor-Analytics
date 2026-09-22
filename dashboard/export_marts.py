
# One-off/rerunnable export: pulls the 4 dbt marts from Snowflake and
# writes them into a local DuckDB file so the Streamlit dashboard can
# run fully offline, with no warehouse credentials needed at deploy time.

from __future__ import annotations

import logging
import os
from pathlib import Path

import duckdb
import snowflake.connector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SNOWFLAKE_ACCOUNT = "DWKUOTC-QXC31171"
SNOWFLAKE_USER = "MUGO"
SNOWFLAKE_ROLE = "REMITTANCE_DBT_ROLE"
SNOWFLAKE_WAREHOUSE = "REMITTANCE_CORRIDOR_WH"
SNOWFLAKE_DATABASE = "REMITTANCE_CORRIDOR"
SNOWFLAKE_SCHEMA = "DEV_MARTS"

PRIVATE_KEY_PATH = Path.home() / ".dbt" / "keys" / "rsa_key_mugo.p8"
PASSPHRASE_PATH = Path.home() / ".dbt" / "keys" / "mugo_passphrase"

OUTPUT_DB_PATH = Path(__file__).parent / "data" / "marts.duckdb"

MART_TABLES = [
    "mart_corridor_cost_trends",
    "mart_provider_comparison",
    "mart_transparency_flags",
    "mart_kenya_corridors",
]


def _load_private_key_bytes() -> bytes:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    passphrase = PASSPHRASE_PATH.read_text().strip().encode()
    with open(PRIVATE_KEY_PATH, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(), password=passphrase, backend=default_backend()
        )
    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def connect_to_snowflake() -> snowflake.connector.SnowflakeConnection:
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        role=SNOWFLAKE_ROLE,
        warehouse=SNOWFLAKE_WAREHOUSE,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        private_key=_load_private_key_bytes(),
    )


def export_marts_to_duckdb() -> None:
    OUTPUT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with connect_to_snowflake() as sf_conn:
        with duckdb.connect(str(OUTPUT_DB_PATH)) as duck_conn:
            for table_name in MART_TABLES:
                logger.info("Exporting %s from Snowflake", table_name)
                cursor = sf_conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                df = cursor.fetch_pandas_all()
                cursor.close()

                df.columns = [c.lower() for c in df.columns]
                duck_conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                duck_conn.register("tmp_df", df)
                duck_conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM tmp_df")
                duck_conn.unregister("tmp_df")

                logger.info("  -> %s rows written", len(df))

    logger.info("Export complete: %s", OUTPUT_DB_PATH)


if __name__ == "__main__":
    export_marts_to_duckdb()