#!/bin/bash

echo -n "Enter dbt API Key:";
read dbt_api_key
echo -n "Enter Fivetran API Key:";
read -s fivetran_api_key
echo -n "Enter dbt Account Id:";
read -s dbt_account_id

sudo su
apt update
apt upgrade
apt install software-properties-common
add-apt-repository ppa:deadsnakes/ppa
apt install python3.7 python3.7-venv python3.7-dev

adduser airflow --disabled-login --disabled-password --gecos "Airflow system user"

cd /srv

# creates a virtual environment called "airflow"
python3.7 -m venv airflow
cd airflow
source bin/activate

# With an activated virtual environment
pip install --upgrade pip
pip install wheel
pip install apache-airflow[postgres,crypto]==2.0.0
chown airflow.airflow . -R
chmod g+rwx . -R

export AIRFLOW_HOME=/srv/airflow
export FIVETRAN_API_KEY=$fivetran_api_key
export DBT_API_KEY=$dbt_api_key
export DBT_ACCOUNT_ID=$dbt_account_id
export FIVETRAN_DATETIME_FORMAT=%Y-%m-%dT%H:%M:%S.%fZ
export DBT_DATETIME_FORMAT=%Y-%m-%dT%H:%M:%S.%fZ
export AIRFLOW_DATETIME_FORMAT=%Y-%m-%dT%H:%M:%S.%fZ