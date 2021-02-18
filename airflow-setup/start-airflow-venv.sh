#!/bin/bash

## sourced from https://medium.com/grensesnittet/airflow-on-gcp-may-2020-cdcdfe594019

echo -n "Enter dbt API Key:";
read dbt_api_key
echo -n "Enter Fivetran API Key:";
read -s fivetran_api_key
echo -n "Enter dbt Account Id:";
read -s dbt_account_id

cd /srv/airflow
source bin/activate

export AIRFLOW_HOME=/srv/airflow
export FIVETRAN_API_KEY=$fivetran_api_key
export DBT_API_KEY=$dbt_api_key
export DBT_ACCOUNT_ID=$dbt_account_id
export FIVETRAN_DATETIME_FORMAT=%Y-%m-%dT%H:%M:%S.%fZ
export DBT_DATETIME_FORMAT=%Y-%m-%dT%H:%M:%S.%fZ
export AIRFLOW_DATETIME_FORMAT=%Y-%m-%dT%H:%M:%S.%fZ