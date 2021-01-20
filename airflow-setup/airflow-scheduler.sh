#!/usr/bin/env bash
# To enable this script to activate the virtualenv and set AIRFLOW_HOME, it must be run from MyRepo i.e. your repository
cd /srv/airflow-2.0

source bin/activate

export AIRFLOW_HOME=$(pwd)
export PYTHONPATH=$(pwd)

airflow scheduler