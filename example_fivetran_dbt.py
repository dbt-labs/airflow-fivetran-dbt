
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

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization

FIVETRAN_API_KEY = os.getenv('FIVETRAN_API_KEY', '')
DBT_API_KEY = os.getenv('DBT_API_KEY', '')

ft = FivetranApi(api_token=FIVETRAN_API_KEY)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@fishtownanalytics.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
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

# def fivetran_connector_sync(ds, base_url=BASE_URL, api_route='connectors', api_key=FIVETRAN_API_KEY, **kwargs):
#     """Print the Airflow context and ds variable from the context."""

#     #pprint(kwargs)
#     #print(ds)
#     #return 'Whatever you return gets printed in the logs'
#     connector_id = kwargs['dag_run'].conf['connector_id'] #warn_enormously

#     url = base_url + api_route + '/' + connector_id + '/' + 'force'
#     headers = {'Content-Type': 'application/json', 'Authorization': f'Basic {api_key}' }
#     data = {} # this endpoint takes an empty payload
#     response = requests.post(url, json=data, headers=headers)

#     if response.status_code == 200:
#         return json.loads(response.content)
    
#     else:
#         raise RuntimeError(response.text)

run_fivetran_connector_sync = PythonOperator(
    task_id='start_data_sync',
    python_callable=ft.force_connector_sync,
    dag=dag,
)

def check_connector_sync_status(ds, **kwargs):
    return 'checking connector sync status'

run_check_connector_sync_status = PythonOperator(
    task_id='extract_pokemon_data',
    python_callable=check_connector_sync_status,
    dag=dag,
)

def dbt_job_run(ds, **kwargs):
    return 'Running dbt jobx'

run_dbt_job_run = PythonOperator(
    task_id='dbt_job_run',
    python_callable=dbt_job_run,
    dag=dag,
)

def check_dbt_job_run_status(ds, **kwargs):
    return 'checking dbt job run status'

run_check_dbt_job_run_status = PythonOperator(
    task_id='check_dbt_job_run_status',
    python_callable=check_dbt_job_run_status,
    dag=dag,
)

run_fivetran_connector_sync >> check_connector_sync_status >> run_dbt_job_run >> check_dbt_job_run_status

# start sync (above)
# poll to check connector status - GET connector data
## verify whether last succeeded date is after the trigger date
## if so, start dbt run

# start dbt run

# check run status