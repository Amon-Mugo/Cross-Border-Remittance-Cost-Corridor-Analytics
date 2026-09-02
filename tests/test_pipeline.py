# tests/test_pipeline.py
#
# Tests for the pipeline orchestration layer (src/pipeline.py). These
# tests mock every transform/quality function -- each already has its
# own unit tests in tests/transform/ and tests/quality/ -- so this file
# verifies only what pipeline.py itself is responsible for: call order,
# correct data flow between stages, and correct output paths/writes.

from unittest.mock import MagicMock, patch

import pytest

from src.pipeline import run_pipeline, write_outputs


@pytest.fixture
def mock_df():
    """A MagicMock standing in for a PySpark DataFrame."""
    return MagicMock(name="DataFrame")


@pytest.fixture
def mock_report_df():
    """A MagicMock standing in for a quality-report DataFrame, with a
    .count() that returns 0 by default (no flagged rows)."""
    report = MagicMock(name="ReportDataFrame")
    report.count.return_value = 0
    return report


class TestRunPipeline:
    @patch("src.pipeline.check_duplicates")
    @patch("src.pipeline.check_transparency")
    @patch("src.pipeline.check_fx_margin")
    @patch("src.pipeline.validate_grain")
    @patch("src.pipeline.unpivot_cc")
    @patch("src.pipeline.parse_period_column")
    @patch("src.pipeline.parse_date_column")
    @patch("src.pipeline.clean_geography_nulls")
    @patch("src.pipeline.load_raw_parquet")
    def test_calls_stages_in_order_with_correct_data_flow(
        self,
        mock_load_raw_parquet,
        mock_clean_geography_nulls,
        mock_parse_date_column,
        mock_parse_period_column,
        mock_unpivot_cc,
        mock_validate_grain,
        mock_check_fx_margin,
        mock_check_transparency,
        mock_check_duplicates,
        mock_df,
        mock_report_df,
    ):
        """Transform stages chain load -> clean -> parse_date ->
        parse_period -> unpivot -> validate_grain, in order, each
        receiving the previous stage's output. validate_grain's clean
        output is the only hard filter: fx_margin, transparency, and
        duplicate_check are flag-only checks that all receive that
        same grain-deduped df (not each other's output), and their
        clean-side return value is discarded -- final clean_df is
        validate_grain's output, unmodified by the three checks."""
        stage_outputs = [MagicMock(name=f"df_stage_{i}") for i in range(6)]

        mock_load_raw_parquet.return_value = stage_outputs[0]
        mock_clean_geography_nulls.return_value = stage_outputs[1]
        mock_parse_date_column.return_value = stage_outputs[2]
        mock_parse_period_column.return_value = stage_outputs[3]
        mock_unpivot_cc.return_value = stage_outputs[4]
        mock_validate_grain.return_value = (stage_outputs[5], mock_report_df)
        mock_check_fx_margin.return_value = (MagicMock(), mock_report_df)
        mock_check_transparency.return_value = (MagicMock(), mock_report_df)
        mock_check_duplicates.return_value = (MagicMock(), mock_report_df)

        spark = MagicMock(name="SparkSession")
        raw_path = "s3://remittance-corridor-raw-data-bucket-011294328070/raw/full_history/rpw_q2_2016_2025.parquet"

        clean_df, reports = run_pipeline(spark, raw_path)

        # Correct input threading through the transform stages.
        mock_load_raw_parquet.assert_called_once_with(spark, raw_path)
        mock_clean_geography_nulls.assert_called_once_with(stage_outputs[0])
        mock_parse_date_column.assert_called_once_with(stage_outputs[1])
        mock_parse_period_column.assert_called_once_with(stage_outputs[2])
        mock_unpivot_cc.assert_called_once_with(stage_outputs[3])
        mock_validate_grain.assert_called_once_with(stage_outputs[4])

        # The three quality checks all receive validate_grain's clean
        # output directly -- not each other's output.
        mock_check_fx_margin.assert_called_once_with(stage_outputs[5])
        mock_check_transparency.assert_called_once_with(stage_outputs[5])
        mock_check_duplicates.assert_called_once_with(stage_outputs[5])

        # Final clean_df is validate_grain's output, untouched by the
        # three flag-only checks.
        assert clean_df is stage_outputs[5]

    @patch("src.pipeline.check_duplicates")
    @patch("src.pipeline.check_transparency")
    @patch("src.pipeline.check_fx_margin")
    @patch("src.pipeline.validate_grain")
    @patch("src.pipeline.unpivot_cc")
    @patch("src.pipeline.parse_period_column")
    @patch("src.pipeline.parse_date_column")
    @patch("src.pipeline.clean_geography_nulls")
    @patch("src.pipeline.load_raw_parquet")
    def test_reports_dict_has_correct_keys_and_values(
        self,
        mock_load_raw_parquet,
        mock_clean_geography_nulls,
        mock_parse_date_column,
        mock_parse_period_column,
        mock_unpivot_cc,
        mock_validate_grain,
        mock_check_fx_margin,
        mock_check_transparency,
        mock_check_duplicates,
        mock_df,
    ):
        """reports dict must map each check to its own distinct report
        DataFrame, keyed correctly -- not mixed up or overwritten."""
        for mock_fn in (
            mock_load_raw_parquet,
            mock_clean_geography_nulls,
            mock_parse_date_column,
            mock_parse_period_column,
            mock_unpivot_cc,
        ):
            mock_fn.return_value = mock_df

        grain_report = MagicMock(name="grain_report")
        grain_report.count.return_value = 0
        fx_report = MagicMock(name="fx_report")
        fx_report.count.return_value = 0
        transparency_report = MagicMock(name="transparency_report")
        transparency_report.count.return_value = 0
        duplicate_report = MagicMock(name="duplicate_report")
        duplicate_report.count.return_value = 0

        mock_validate_grain.return_value = (mock_df, grain_report)
        mock_check_fx_margin.return_value = (mock_df, fx_report)
        mock_check_transparency.return_value = (mock_df, transparency_report)
        mock_check_duplicates.return_value = (mock_df, duplicate_report)

        _, reports = run_pipeline(MagicMock(), "s3://fake/raw.parquet")

        assert reports == {
            "grain_duplicates": grain_report,
            "fx_margin": fx_report,
            "transparency": transparency_report,
            "duplicate_check": duplicate_report,
        }

    @patch("src.pipeline.check_duplicates")
    @patch("src.pipeline.check_transparency")
    @patch("src.pipeline.check_fx_margin")
    @patch("src.pipeline.validate_grain")
    @patch("src.pipeline.unpivot_cc")
    @patch("src.pipeline.parse_period_column")
    @patch("src.pipeline.parse_date_column")
    @patch("src.pipeline.clean_geography_nulls")
    @patch("src.pipeline.load_raw_parquet")
    def test_logs_warning_when_rows_flagged(
        self,
        mock_load_raw_parquet,
        mock_clean_geography_nulls,
        mock_parse_date_column,
        mock_parse_period_column,
        mock_unpivot_cc,
        mock_validate_grain,
        mock_check_fx_margin,
        mock_check_transparency,
        mock_check_duplicates,
        mock_df,
        caplog,
    ):
        """A report with flagged rows (.count() > 0) must trigger a
        logged warning naming the check and the flagged row count."""
        for mock_fn in (
            mock_load_raw_parquet,
            mock_clean_geography_nulls,
            mock_parse_date_column,
            mock_parse_period_column,
            mock_unpivot_cc,
        ):
            mock_fn.return_value = mock_df

        clean_report = MagicMock()
        clean_report.count.return_value = 0
        flagged_report = MagicMock()
        flagged_report.count.return_value = 7

        mock_validate_grain.return_value = (mock_df, clean_report)
        mock_check_fx_margin.return_value = (mock_df, flagged_report)
        mock_check_transparency.return_value = (mock_df, clean_report)
        mock_check_duplicates.return_value = (mock_df, clean_report)

        with caplog.at_level("WARNING"):
            run_pipeline(MagicMock(), "s3://fake/raw.parquet")

        assert any(
            "fx_margin" in record.message and "7" in record.message
            for record in caplog.records
        )


class TestWriteOutputs:
    def test_writes_clean_df_per_quarter_to_quarter_clean_prefix(
        self, mock_df, mock_report_df
    ):
        """clean_df must be split by distinct 'period' and each slice
        written to its own <output_path>/<period>/clean prefix, matching
        the Snowflake LOAD_REMITTANCE_RAW stage path convention."""
        mock_df.select.return_value.distinct.return_value.collect.return_value = [
            {"period": "2016_2Q"},
            {"period": "2016_3Q"},
        ]

        write_outputs(
            mock_df,
            {"grain_duplicates": mock_report_df},
            "s3://remittance-corridor-curated-data-bucket-011294328070",
        )

        mock_df.select.assert_any_call("period")
        assert mock_df.filter.call_count == 2
        mock_df.filter.return_value.write.mode.assert_any_call("overwrite")
        mock_df.filter.return_value.write.mode.return_value.parquet.assert_any_call(
            "s3://remittance-corridor-curated-data-bucket-011294328070/2016_2Q/clean"
        )
        mock_df.filter.return_value.write.mode.return_value.parquet.assert_any_call(
            "s3://remittance-corridor-curated-data-bucket-011294328070/2016_3Q/clean"
        )

    def test_writes_each_report_to_its_own_quality_reports_subdir(
        self, mock_df, mock_report_df
    ):
        mock_df.select.return_value.distinct.return_value.collect.return_value = []
        reports = {
            "grain_duplicates": MagicMock(),
            "fx_margin": MagicMock(),
        }

        write_outputs(mock_df, reports, "s3://curated-bucket")

        reports["grain_duplicates"].write.mode.return_value.parquet.assert_any_call(
            "s3://curated-bucket/quality_reports/grain_duplicates"
        )
        reports["fx_margin"].write.mode.return_value.parquet.assert_any_call(
            "s3://curated-bucket/quality_reports/fx_margin"
        )

    def test_strips_trailing_slash_from_output_path(self, mock_df):
        mock_df.select.return_value.distinct.return_value.collect.return_value = [
            {"period": "2016_2Q"}
        ]

        write_outputs(mock_df, {}, "s3://curated-bucket/")

        mock_df.filter.return_value.write.mode.return_value.parquet.assert_any_call(
            "s3://curated-bucket/2016_2Q/clean"
        )
