# airflow-fivetran-dbt
Example orchestration pipeline for Fivetran + dbt managed by Airflow

# Introduction
This is one way to orchetstrate dbt in coordination with other tools, such as Fivetran for data loading. Our focus is on coordinating Fivetran for loading data to a warehouse, and then triggering a dbt run in an event-driven pipeline. We use the Fivetran  and dbt Cloud APIs to accomplish this, with Airflow managing the scheduling / orchestration of the job flow. The final step extracts the `manifest.json` from the dbt run results to capture relevant metadata for downstream logging, alerting and analysis. The code provided in this repository are intended as a demonstration to build upon, *not* as a production-ready solution. 

# Table of Contents
1. [Highlights](#Highlights)  
2. [Solution Architecture](#Solution-Architecture)  
3. [Airflow DAG](#Airflow-DAG)  
4. [dbt Job DAG](#dbt-Job-DAG)  
5. [How to Guide](#How-to-Guide)   
   * [Systems](#Systems)  
   * [User permissions](#User-permissions)
   * [Airflow server configuration](#Airflow-server-configuration)
   * [Aiflow environment setup](#Aiflow-environment-setup)
   * [SSH key configuration in Github](#SSH-key-configuration-in-Github)
   * [Git repository configuration](#Git-repository-configuration)
   * [Environment variables](#Environment-variables)
   * [Running the code](#Running-the-code)

## Highlights
- logical isolation of data load (Fivetran), data transform (dbt) and orchestration (Airflow) functions
- Airflow code would be portable to a tool like [Astronomer](https://www.astronomer.io/)  
- avoids complexity of re-creating dbt DAG in Airflow, which we've seen implemented at a few clients  
- demonstrates orchestrating Fivetran and dbt in an event-driven pipeline  
- configurable approach which can be extended to handle additional Fivetran connectors and dbt job definitions  
- captures relevant data from a job run which could be shipped to downstream logging & analytics services. It would also be feasible to log interim job status data using this setup, though we did not build it  into the current python codebase

## Solution Architecture
Below is a system diagram with a brief description of each step in the process

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/airflow-fivetran-dbt-arch.png "Solution Architecture Diagram")

## Aiflow DAG
If you are already using Airflow, you may want to skip the implementation guide below and focus on the key parts of the python code which enable this workflow. The DAG process we implemented looks like this: 

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/airflow-dag-process.png "Airflow DAG")

This is a simplified workflow meant to illustrate the coordination role Airflow can play between a data loading system like Fivetran and dbt. Airflow [XComs](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html?highlight=xcom#concepts-xcom) are used to share state among the tasks defined in the job. Additionally, the DAG takes a mapping for runtime input: 
```
    { 
    "connector_id": "warn_enormously",
    "dbt_job_name": "pokemon_aggregation_job"
    }
```

## dbt Job DAG
The dbt job run against this data is defined in [this repository](https://github.com/fishtown-analytics/airflow-fivetran-dbt--dbt-jobs). It runs a simple aggregation of the input source data to summarize the average HP per pokemon catch_number. It looks like this: 

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/dbt-lineage-graph.png "dbt Lineage Graph")

# How to Guide

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

#### Airflow server configuration
We mainly followed the process described in Jostein Leira's [Medium Post](https://medium.com/grensesnittet/airflow-on-gcp-may-2020-cdcdfe594019) <sup>1</sup>

There are a couple of configurations we changed: 
- Whitelist only the [Google IP Ranges](https://support.google.com/a/answer/60764?hl=en) and any developer IP addresses  
- Install apache-airflow version `2.0.0` instead of `1.10.10`. Note that airflow command syntax changed slightly across major versions. The Airflow v2.0.0 CLI command syntax is documented [here](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)  

#### Aiflow environment setup
A configuration script is located [here](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/airflow-setup/env-setup.sh). The user is prompted for the dbt and Fivetran API Keys as inputs and store them in environment variables. It's additionally useful to modify the environment activiation script in `/srv/airflow/bin/activate` to automatically set and unset these variables each time the environment starts.  

After running the shell script referenced above, verify you have a new directory under `/srv/airflow`. You should be able to run `source bin/activate` from this location to start your virtual environment.

#### SSH key configuration in Github
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
  IdentityFile ~/.ssh/<your-key-pair-name>
```
* Add the ssh key to the agent: `ssh-add -K ~/.ssh/<your-key-pair-name>`
* It's useful to add a line to your `.bashrc` or `.zshrc` file to automatically start the agent and add your ssh keys each time you open a terminal. 
* Add the key to your repository: 

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/git-repo-ssh-keys.png "Adding Deploy Keys to a Repository")

#### Git repository configuration
Once you've set ssh keys for both the airflow and dbt code repositories, you clone the respective codebases on the airflow server and in dbt Cloud. Instructions for configuring Github repositories in dbt Cloud are [here](https://docs.getdbt.com/docs/dbt-cloud/cloud-configuring-dbt-cloud/cloud-installing-the-github-application)

#### Environment variables  
The provided Python code uses several environment variables as configuration inputs:  

* `FIVETRAN_API_KEY`: This is a base64 encoded value of your account's `<api-key>:<api-secret>`. [This link from Fivetran](https://fivetran.com/docs/rest-api/getting-started) documents how to generate this value. For example, an API key of `d9c4511349dd4b86` and API secret of `1f6f2d161365888a1943160ccdb8d968` encode to `ZDljNDUxMTM0OWRkNGI4NjoxZjZmMmQxNjEzNjU4ODhhMTk0MzE2MGNjZGI4ZDk2OA==`. The specific values will be different on your system.  
* `FIVETRAN_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`
* `AIRFLOW_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`
* `DBT_ACCOUNT_ID` which can be obtained from the URLs when logged in to dbt Cloud. For example in the URL cloud.getdbt.com/#/accounts/**<account-id>**/projects/<project-id>/dashboard/
* `DBT_API_KEY` which can be obtained by navigating to Profile > API Access in dbt Cloud.
* `DBT_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`

#### Running the code

-- From the Airflow UI -- 

1) From the DAGs list, click on the run button for the  `example_fivetran_dbt_operator` DAG 

2) Add the optional configuration JSON to the DAG. These inputs are accessed in the `dag_run` configuration variables within the python code, as follows: 

```python
connector_id = kwargs['dag_run'].conf['connector_id']
```

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/airflow-dag-trigger-ui.png "Adding configurations for a Airflow DAG run")

 -- From the command line --
With your virtual environment activated, run:  
```shell
airflow dags trigger --conf '{"connector_id": "warn_enormously", "dbt_job_name": "pokemon_aggregation_job"}' example_fivetran_dbt_operator
```

Sources
======
<sup>1</sup> GCP Setup Guide created by Jostein Leira: https://medium.com/grensesnittet/airflow-on-gcp-may-2020-cdcdfe594019

