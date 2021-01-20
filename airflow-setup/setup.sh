
sudo su
apt update
apt upgrade
apt install software-properties-common
add-apt-repository ppa:deadsnakes/ppa
apt install python3.7 python3.7-venv python3.7-dev

adduser airflow --disabled-login --disabled-password --gecos "Airflow system user"

cd /srv

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

airflow db init