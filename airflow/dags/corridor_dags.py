# used to define our dags and also the error handling

from airflow.models import Variable
from datetime import  datetime,timedelta
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.emr import EmrServerlessStartJobOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow import DAG
from utils.callbacks import notify_failure
from scripts.convert_raw_to_parquet import convert_xlsx_to_parquet # used to load data to s3 aws

DEFAULT_ARGS= {
    "owner": "amon",
    "retries":1,
    "retry_delay": timedelta(minutes=4),
    "on_failure_callback": notify_failure,
}

AWS_CONN_ID = "aws_default"
SNOWFLAKE_CONN_ID="snowflake_default"

LOCAL_XLSX_PATH= (
    "/home/amonmugo/PROJECTS/Cross-Border Remittance Cost & Corridor Analytics"
    "/data/drops/rpw_latest.xlsx"
) # this is the path of the raw input of the local file system

RAW_BUCKET= "remittance-corridor-raw-data-bucket-011294328070"
CURATED_BUCKET= "remittance-corridor-curated-data-bucket-011294328070"

EMR_APPLICATION_ID = "00g8ablrp8otls09"  #used to identify the emr currentky running
EMR_EXECUTION_ROLE_ARN = (
    "arn:aws:iam::011294328070:role/remittance-corridor-emr-execution-role-011294328070"
) # this is used to give aceess

ENTRY_POINT_S3_PATH=f"s3://{CURATED_BUCKET}/scripts/pipeline.py" #used for pyspark
SRC_PACKAGE_S3_PATH=f"s3://{CURATED_BUCKET}/scripts/src.zip" # used foridentifying the zip code (src.zip)

def run_ingestion(**context) -> str:
    quarter_label = convert_xlsx_to_parquet(LOCAL_XLSX_PATH, RAW_BUCKET)
    return quarter_label

with DAG(
     dag_id="remittance_corridor_analytics",
    description="ingestion -> EMR transform -> Snowflake load, latest quarter only",
    default_args=DEFAULT_ARGS,
    schedule=None,
    start_date=datetime(2026, 10, 7),
    catchup=False,
    tags=["remittance"],
) as dag:

    ingest = PythonOperator(
        task_id="ingestion",
        python_callable=run_ingestion,
    )

    transform = EmrServerlessStartJobOperator(
        task_id="transform_curated_spark",
        aws_conn_id=AWS_CONN_ID,
        application_id=EMR_APPLICATION_ID,
        execution_role_arn=EMR_EXECUTION_ROLE_ARN,
        job_driver={
            "sparkSubmit": {
                "entryPoint": ENTRY_POINT_S3_PATH,
                "entryPointArguments": [
                    "{{ ti.xcom_pull(task_ids='ingestion') }}",
                ],
                "sparkSubmitParameters": (
                    f"--py-files {SRC_PACKAGE_S3_PATH} "
                    "--conf spark.dynamicAllocation.enabled=false "
                    "--conf spark.executor.instances=2 "
                    "--conf spark.executor.cores=1 "
                    "--conf spark.executor.memory=2g"
                ),
            }
        },
        configuration_overrides={
            "monitoringConfiguration": {
                "s3MonitoringConfiguration": {
                    "logUri": f"s3://{CURATED_BUCKET}/emr_logs/",
                }
            }
        },
        wait_for_completion=True,
        name="corridor_transform_{{ ds }}",
    )

    load = SQLExecuteQueryOperator(
        task_id="load_raw_snowflake",
        conn_id=SNOWFLAKE_CONN_ID,
        sql=["CALL LOAD_REMITTANCE_RAW('{{ ti.xcom_pull(task_ids=\"ingestion\") }}');"],
        hook_params={
            "role": "REMITTANCE_CORRIDOR_ROLE",
            "database": "REMITTANCE_CORRIDOR",
            "warehouse": "REMITTANCE_CORRIDOR_WH",
            "schema": "RAW",
        },
    )

    ingest >> transform >> load
