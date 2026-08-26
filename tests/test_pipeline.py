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
    def test_calls_stages_in_order_with_chained_output(
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
        """Each stage's output must be passed as the next stage's input,
        in the exact declared order: load -> clean -> parse_date ->
        parse_period -> unpivot -> validate_grain -> fx_margin ->
        transparency -> duplicates."""
        stage_outputs = [MagicMock(name=f"df_stage_{i}") for i in range(9)]

        mock_load_raw_parquet.return_value = stage_outputs[0]
        mock_clean_geography_nulls.return_value = stage_outputs[1]
        mock_parse_date_column.return_value = stage_outputs[2]
        mock_parse_period_column.return_value = stage_outputs[3]
        mock_unpivot_cc.return_value = stage_outputs[4]
        mock_validate_grain.return_value = (stage_outputs[5], mock_report_df)
        mock_check_fx_margin.return_value = (stage_outputs[6], mock_report_df)
        mock_check_transparency.return_value = (
            stage_outputs[7],
            mock_report_df,
        )
        mock_check_duplicates.return_value = (stage_outputs[8], mock_report_df)

        spark = MagicMock(name="SparkSession")
        raw_path = "s3://remittance-corridor-raw-data-bucket-011294328070/raw/full_history/rpw_q2_2016_2025.parquet"

        clean_df, reports = run_pipeline(spark, raw_path)

        # Correct input threading: each stage receives the previous
        # stage's output, not the raw df or some other stage's output.
        mock_load_raw_parquet.assert_called_once_with(spark, raw_path)
        mock_clean_geography_nulls.assert_called_once_with(stage_outputs[0])
        mock_parse_date_column.assert_called_once_with(stage_outputs[1])
        mock_parse_period_column.assert_called_once_with(stage_outputs[2])
        mock_unpivot_cc.assert_called_once_with(stage_outputs[3])
        mock_validate_grain.assert_called_once_with(stage_outputs[4])
        mock_check_fx_margin.assert_called_once_with(stage_outputs[5])
        mock_check_transparency.assert_called_once_with(stage_outputs[6])
        mock_check_duplicates.assert_called_once_with(stage_outputs[7])

        # Final clean_df is the last stage's clean output.
        assert clean_df is stage_outputs[8]

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
    def test_writes_clean_df_to_clean_prefix(self, mock_df, mock_report_df):
        write_outputs(
            mock_df,
            {"grain_duplicates": mock_report_df},
            "s3://remittance-corridor-curated-data-bucket-011294328070",
        )

        mock_df.write.mode.assert_any_call("overwrite")
        mock_df.write.mode.return_value.parquet.assert_any_call(
            "s3://remittance-corridor-curated-data-bucket-011294328070/clean"
        )

    def test_writes_each_report_to_its_own_quality_reports_subdir(
        self, mock_df, mock_report_df
    ):
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
        write_outputs(mock_df, {}, "s3://curated-bucket/")

        mock_df.write.mode.return_value.parquet.assert_any_call(
            "s3://curated-bucket/clean"
        )
