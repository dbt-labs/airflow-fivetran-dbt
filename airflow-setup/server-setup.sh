#!/bin/bash

## sourced from https://medium.com/grensesnittet/airflow-on-gcp-may-2020-cdcdfe594019

echo -n "Enter dbt API Key:";
read dbt_api_key
echo -n "Enter Fivetran API Key:";
read -s fivetran_api_key
echo -n "Enter dbt Account Id:";
read -s dbt_account_id

sudo su
apt update -y
apt upgrade -y
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa -y
apt install python3.7 python3.7-venv python3.7-dev -y
apt install vim -y
apt install postgresql-client-12 -y
apt-get install git -y

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