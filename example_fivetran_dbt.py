
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

# initialize Fivetran API module
ft = FivetranApi(api_token=FIVETRAN_API_KEY, 
                 fivetran_datetime_format=FIVETRAN_DATETIME_FORMAT, 
                 airflow_datetime_format=AIRFLOW_DATETIME_FORMAT)

# initialize dbt Cloud module
dbt = DbtCloudApi(account_id=DBT_ACCOUNT_ID, 
                  api_token=DBT_API_KEY)

#default_args = {
    #'owner': 'airflow',
    #'depends_on_past': False,
    #'email': ['airflow@fishtownanalytics.com'],
    #'email_on_failure': False,
    #'email_on_retry': False,
    #'retries': 1,
    #'retry_delay': timedelta(minutes=5),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}

args = {
    'owner': 'airflow',
    'start_date': datetime.now()
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

run_check_connector_sync_status = PythonOperator(
    task_id='check_connector_sync_status',
    python_callable=ft.get_connector_sync_status,
    dag=dag,
)

run_dbt_job = PythonOperator(
    task_id='dbt_job',
    python_callable=dbt.trigger_job_run,
    dag=dag,
)

# run_check_dbt_job_status = PythonOperator(
#     task_id='check_dbt_job_status',
#     python_callable=check_dbt_job_run_status,
#     dag=dag,
# )

# set upstream / downstream relationships for the apps
run_check_connector_sync_status.set_upstream(run_fivetran_connector_sync)
run_dbt_job.set_upstream(run_check_connector_sync_status)


# create the DAG pipeline
run_fivetran_connector_sync >> run_check_connector_sync_status >> run_dbt_job