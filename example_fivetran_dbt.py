
import json
import os
import requests

from datetime import datetime, timedelta
from pprint import pprint

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

# Operators; we need this to operate!
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from fivetran import FivetranApi
from dbt_cloud import DbtCloudApi

# these are environment variables stored on the virtual environment where airflow is running
FIVETRAN_API_KEY = os.getenv('FIVETRAN_API_KEY', '')
FIVETRAN_DATETIME_FORMAT = os.getenv('FIVETRAN_DATETIME_FORMAT', '')

AIRFLOW_DATETIME_FORMAT = os.getenv('AIRFLOW_DATETIME_FORMAT', '')

DBT_ACCOUNT_ID = os.getenv('DBT_ACCOUNT_ID', '')
DBT_API_KEY = os.getenv('DBT_API_KEY', '')
DBT_DATETIME_FORMAT = os.getenv('DBT_DATETIME_FORMAT', '')

# initialize Fivetran API module
ft = FivetranApi(api_token=FIVETRAN_API_KEY, 
                 fivetran_datetime_format=FIVETRAN_DATETIME_FORMAT, 
                 airflow_datetime_format=AIRFLOW_DATETIME_FORMAT)

# initialize dbt Cloud module
dbt = DbtCloudApi(account_id=DBT_ACCOUNT_ID, 
                  api_token=DBT_API_KEY,
                  airflow_datetime_format=AIRFLOW_DATETIME_FORMAT,
                  dbt_datetime_format=DBT_DATETIME_FORMAT)

args = {
    'owner': 'airflow',
    'start_date': datetime.now(),
    'provide_context': True
}

dag = DAG(
    dag_id='example_fivetran_dbt_operator',
    default_args=args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['example'],
)

run_fivetran_connector_sync = PythonOperator(
    task_id='fivetran_connector_sync',
    python_callable=ft.force_connector_sync,
    dag=dag,
)

run_get_connector_sync_status = PythonOperator(
    task_id='get_connector_sync_status',
    python_callable=ft.get_connector_sync_status,
    dag=dag,
)

run_dbt_job = PythonOperator(
    task_id='dbt_job',
    python_callable=dbt.run_job,
    dag=dag,
)

run_get_dbt_job_status = PythonOperator(
    task_id='get_dbt_job_status',
    python_callable=dbt.get_dbt_job_run_status,
    dag=dag,
)

run_extract_dbt_job_run_manifest = PythonOperator(
    task_id='extract_dbt_job_run_manifest',
    python_callable=dbt.get_job_run_manifest,
    dag=dag,
)

# set upstream / downstream relationships for the apps
run_get_connector_sync_status.set_upstream(run_fivetran_connector_sync)
run_dbt_job.set_upstream(run_get_connector_sync_status)
run_get_dbt_job_status.set_upstream(run_dbt_job)
run_extract_dbt_job_run_manifest.set_upstream(run_get_dbt_job_status)

# create the DAG pipeline
run_fivetran_connector_sync >> run_get_connector_sync_status >> \
run_dbt_job >> run_get_dbt_job_status >> \
run_extract_dbt_job_run_manifest