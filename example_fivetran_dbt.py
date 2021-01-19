
import os
import requests

from datetime import timedelta
from pprint import pprint

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

# Operators; we need this to operate!
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization

FIVETRAN_API_KEY = os.getenv('FIVETRAN_API_KEY', '')
BASE_URL = 'api.fivetran.com/v1/'

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
}

dag = DAG(
    dag_id='example_fivetran_dbt_operator',
    default_args=args,
    schedule_interval=None,
    start_date=days_ago(2),
    tags=['example'],
)

def fivetran_connector_sync(ds, base_url=BASE_URL, api_route='connectors/', api_key=FIVETRAN_API_KEY, **kwargs):
    """Print the Airflow context and ds variable from the context."""

    #pprint(kwargs)
    #print(ds)
    #return 'Whatever you return gets printed in the logs'
    url = base_url + api_route + 'repair_chocolate/force'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Basic {api_key}' }
    data = {} # this endpoint takes an empty payload
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        return json.loads(response.content)
    else:
        raise RuntimeError(response.text)

run_fivetran_connector_sync = PythonOperator(
    task_id='extract_pokemon_data',
    python_callable=fivetran_connector_sync,
    dag=dag,
)

run_fivetran_connector_sync