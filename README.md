# airflow-fivetran-dbt
Example orchestration pipeline for Fivetran + dbt managed by Airflow

# Introduction
This is one way to orchetstrate dbt in coordination with other tools, such as Fivetran for data loading. Our focus is on coordinating Fivetran for loading data to a warehouse, and then triggering a dbt run in an event-driven pipeline. The final step in dbt extracts the `manifest.json` from the dbt run results to capture relevant metadata for downstream logging, alerting and analysis. We did not develop code to ship the `manifest.json` to a logging system such as DataDog or Sumologic. The code provided in this repository are intended as a demonstration to build upon, *not* as a production-ready solution. 

# Solution Architecture
Below is a system diagram with a brief description of each step in the process

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/airflow-fivetran-dbt-arch.png "Solution Architecture Diagram")

# What you need to run this guide

#### Systems
1) Snowflake account with database, warehouse etc. configured  
2) Fivetran account with permission to upload data to Snowflake  
3) Source data configured in Fivetran - this guide uses Google Sheets as the source  
4) Google Cloud Platform account  
5) dbt Cloud account  
6) Git repository for dbt code. Here is a [link to ours](https://github.com/fishtown-analytics/airflow-fivetran-dbt--dbt-jobs)

#### User permissions
1) User with access to run database operations in Snowflake. dbt operates under a user account alias  
2) User account in Fivetran with permissions to create new connectors. In this example, we use Google Sheets as the connector source data. You will also need sufficient permissions (or a friend who has them :) ) to obtain an API token and secret from the Fivetran Admin console as described [here](https://fivetran.com/docs/rest-api/getting-started)  
3) User account in dbt with sufficient permissions to create database connections, repositories, and API keys. 
4) User account in Github/Gitlab/Bitbucket etc with permissions to create repositories and associate ssh deploy keys with them. You can read more about this setup [here](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

# GCP & Airflow Server Configuration
We mainly followed the process described in Jostein Leira's [Medium Post](https://medium.com/grensesnittet/airflow-on-gcp-may-2020-cdcdfe594019) <sup>1</sup>

There are a couple of configurations we changed: 
- Whitelist only the [Google IP Ranges](https://support.google.com/a/answer/60764?hl=en) and any developer IP addresses  
- Install apache-airflow version `2.0.0` instead of `1.10.10`. Note that airflow command syntax changed slightly across major versions. The Airflow v2.0.0 CLI command syntax is documented [here](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)  

## Git Repository Configuration
We use ssh keys to manage both this git repository and the one containing dbt code. You need access to manage ssh keys for your repository (in Settings > Deploy Keys > Add Key). Below is an example of creating an ssh key and granting access in Github: 

* Generate ssh key: `$ ssh-keygen -t ed25519 -C "your_email@example.com"`  
* Choose where to save the key, e.g. $HOME/.ssh/<your-key-pair-name>
* Start the ssh agent in the background: `eval "$(ssh-agent -s)"`
* Check for existing ssh configuration: `open ~/.ssh/config`
* If the configuration file doesn't exist, create it: `touch ~/.ssh/config`
* Open the config file and replace the key Id as necessary: 
```
Host *
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

## Aiflow Environment Setup
Shell scripts and service configuration files are located in the `airflow-setup` folder. 

## Environment Variables  
The provided Python code uses several environment variables as configuration inputs:  

* `FIVETRAN_API_KEY`: This is a base64 encoded value of your account's `<api-key>:<api-secret>`. [This link from Fivetran](https://fivetran.com/docs/rest-api/getting-started) documents how to generate this value. For example, an API key of `d9c4511349dd4b86` and API secret of `1f6f2d161365888a1943160ccdb8d968` encode to `ZDljNDUxMTM0OWRkNGI4NjoxZjZmMmQxNjEzNjU4ODhhMTk0MzE2MGNjZGI4ZDk2OA==`. The specific values will be different on your system.  
* `FIVETRAN_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`
* `AIRFLOW_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`
* `DBT_ACCOUNT_ID` which can be obtained from the URLs when logged in to dbt Cloud. For example in the URL cloud.getdbt.com/#/accounts/**<account-id>**/projects/<project-id>/dashboard/
* `DBT_API_KEY` which can be obtained by navigating to Profile > API Access in dbt Cloud.
* `DBT_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`




Sources
======
<sup>1</sup> GCP Setup Guide created by Jostein Leira: https://medium.com/grensesnittet/airflow-on-gcp-may-2020-cdcdfe594019