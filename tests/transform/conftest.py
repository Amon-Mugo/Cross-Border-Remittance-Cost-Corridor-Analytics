# tests/transform/conftest.py
#
# Purpose: Provides a single session-scoped SparkSession shared across all
# transform tests. Session scope avoids the overhead of starting a new JVM
# per test — Spark session startup is slow, so sharing it keeps the test
# suite fast while each test still gets a fresh DataFrame from its own input.

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def spark():
    session = (
        SparkSession.builder.master("local[*]")
        .appName("remittance-corridor-tests")
        .config("spark.sql.shuffle.partitions", "2")  # keep local test runs fast
        .config("spark.ui.enabled", "false")  # no need for Spark UI in tests
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")  # quiet down noisy Spark logs in test output

    yield session

    session.stop()