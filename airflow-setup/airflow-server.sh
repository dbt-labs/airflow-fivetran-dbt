#!/usr/bin/env bash

# To enable this script to activate the virtualenv and set AIRFLOW_HOME, it must be run from MyRepo i.e. your repository
cd $(dirname "$0")/../..

source venv/bin/activate
export AIRFLOW_HOME=$(pwd)
export PYTHONPATH=$(dirname pwd)

airflow webserver -p 8080