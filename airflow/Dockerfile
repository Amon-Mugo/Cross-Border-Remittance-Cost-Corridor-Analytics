FROM apache/airflow:3.3.1-python3.12

USER airflow

COPY  requirements.txt /requirements.txt

RUN pip install --no-cache-dir \
     --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.1/constraints-3.12.txt" \
    -r /requirements.txt \
    apache-airflow-providers-amazon==9.34.0 \
    apache-airflow-providers-snowflake==6.16.0 \
    apache-airflow-providers-common-sql \
    pandas \
    openpyxl \
    pyarrow 

