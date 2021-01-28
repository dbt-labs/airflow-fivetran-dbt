# airflow-fivetran-dbt
Example orchestration pipeline for Fivetran + dbt managed by Airflow

# Introduction
This is one way to orchetstrate dbt in coordination with other tools, such as Fivetran for data loading. Our focus is on coordinating Fivetran for loading data to a warehouse, and then triggering a dbt run in an event-driven pipeline. We use the Fivetran  and dbt Cloud APIs to accomplish this, with Airflow managing the scheduling / orchestration of the job flow. The final step extracts the `manifest.json` from the dbt run results to capture relevant metadata for downstream logging, alerting and analysis. The code provided in this repository are intended as a demonstration to build upon, not as a production-ready solution. 

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
If you are already using Airflow, you may want to skip the implementation guide below and focus on the key parts of the python code which enable this workflow.

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/airflow-dag-process.png "Airflow DAG")

This is a simplified workflow meant to illustrate the coordination role Airflow can play between a data loading system like Fivetran and dbt. Airflow [XComs](https://airflow.apache.org/docs/apache-airflow/stable/concepts.html?highlight=xcom#concepts-xcom) are used to share state among the tasks defined in the job. An example Xcom reference in the code is

Add XCom value in `dbt_job` task
```python
run_id = trigger_resp['id']
kwargs['ti'].xcom_push(key='dbt_run_id', value=str(run_id))
```

Retrieve XCom value associated with `dbt_job` task in downstream `get_dbt_job_status` task
```python
ti = kwargs['ti']
run_id = ti.xcom_pull(key='dbt_run_id', task_ids='dbt_job')
```


Additionally, the DAG takes a mapping for runtime input: 
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

### What you'll need
1) Snowflake account with database, warehouse etc. configured  
2) Fivetran account with permission to upload data to Snowflake  
3) Source data configured in Fivetran - this guide uses Google Sheets as the source  
4) Google Cloud Platform account. Google offers $300 in credits for new accounts, which should be more than enough to get this up and running.  
5) dbt Cloud account  
6) Git repository for dbt code. Here is a [link to ours](https://github.com/fishtown-analytics/airflow-fivetran-dbt--dbt-jobs)

### User permissions
1) User with access to run database operations in Snowflake. dbt operates under a user account alias  
2) User account in Fivetran with permissions to create new connectors. In this example, we use Google Sheets as the connector source data. You will also need sufficient permissions (or a friend who has them :) ) to obtain an API token and secret from the Fivetran Admin console as described [here](https://fivetran.com/docs/rest-api/getting-started)  
3) User account in dbt with sufficient permissions to create database connections, repositories, and API keys. 
4) User account in Github/Gitlab/Bitbucket etc with permissions to create repositories and associate ssh deploy keys with them. You can read more about this setup [here](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

### Airflow Installation

We configured a VM in Google Cloud Platform to host the Airflow server. There are many options for hosting, including managed services like [Astronomer](https://www.astronomer.io/). Your preferred installation method will likely depend on your company's security posture and your desire to customize the implementation.

We began by following the process described in Jostein Leira's [Medium Post](https://medium.com/grensesnittet/airflow-on-gcp-may-2020-cdcdfe594019) <sup>1</sup>. During the installation, we implemented several changes and additions to the architecture, described below. 

The elemnts included in the final GCP setup include:

- GCP Project  
- Networking - VPC  
- Networking - Firewall rules    
- The VM running the Airflow application (we used Ubuntu v...)  
- Instance group  
- Static IP Address  
- Cloud SQL database  
- Load Balancer  

The specific steps to set up and test each of these components are described below.

### Create the GCP Project  

The project will contain all the resources you create in the following steps. Click the project dropdown at the top left of the console and create a new project. We named ours `airflow-server`.  

### Create the VPC Network

First we'll set up the VPC in which the Airflow VM will run. When first accessing the VPC Network pane within GCP, you may need to enable the Compute Engine API.

1) Navigate to the hamburger menu at the top left of the GCP console, then click "VPC Networks"  
2) Click "Create VPC Network"  
3) Give the network a name (e.g. `fishtown-airflow-network`)
4) Create a subnet for the network (e.g. `fishtown-airflow-network-subnet1`)  
5) Choose a region  
6) Choose a CIDR range for the subnet (10.0.0.0/8 works)  
-- Leave the default settings on the rest of the page  

### Set up the Firewall Rules

1) From the VPC Networks page, click the name of the network you created in the previous step.  
2) Click Firewall rules > Add firewall rule  
3) We need to allow http (temporarily), https, and ssh access to the network from an external IP. Google "what is my ip address" and use the returned value in your firewall settings, plus "/32". For example, if your IP is 11.222.33.444, you would add `11.222.33.444/32`
4) Set Targets to "All instances in the network"  
5) Set your IP in the list of allows IP addresses  
6) Open port 80 and 8080   
7) Click "Create"    
8) Add additional rules for HTTPS (port 443), SSH (port 22), and load balancer (IP ranges 130.211.0.0/32 and 35.191.0.0/16) traffic. The load balancer traffic IPs are internal to Google.  

When you're done, the firewall rules should look as shown in the screenshot below.  

### Create the Virtual Machine  

1) Click the hamburger icon at the top left of the console > Compute Engine > Virtual Machines > VM Instances > Create  
2) Give the instance a name, such as fishtown-airflow-vm1  
3) Be sure to place the VM in the same region you selected for your subnet in the VPC configuration step  
4) Select the instance type. We used an `e2-standard-2` instance for this  
5) Change the operating system to Ubuntu version 20.04 LTS Minimal  
6) Check the box to allow HTTP traffic to the instance  
7) Place the instance in the VPC Network you created in the VPC setup step  
-- Leave the rest of the defaults when adding the instance to your VPC  
-- Optional -- you can use the `env-setup.sh` script in the `airflow-setup` folder of this repository to bootstrap the instance when it starts.  

### Create the Instance Group  

1) Click the hamburger icon at the top left of the console > Compute Engine > Instance Groups > Click Create Instance Group > New Unmanaged Instance Group   
2) Choose the same region you've been working from   \
3) Select the name of the network you created in the VPC configuration step  
4) Add the VM instance you created in the Create Virtual Machine Step  
5) Click Create  

### Test SSH access to the VM  

GCP offers multiple options for ssh access to instances, including via the browser. There is some extra configuration necessary for browser-based connections. You can also ssh to your machine from a local terminal.  

#### SSH from a local terminal

1) Open a terminal on your machine  
2) Run `gcloud auth login`  
3) This will open a browser window. Use it to sign in to your account.  
4) Ensure you have an ssh key set up and added to your project. Follow the instructions [here](https://cloud.google.com/compute/docs/instances/adding-removing-ssh-keys) for this   
5) To ssh to your machine, run the folloing in your terminal: `gcloud beta compute ssh --zone "<your-region-zone-here>" "<your-vm-name-here>" --project "<your-project-here>"`  
6) If you configured a password on your ssh key, enter it when prompted  
-- Upon successful login, your terminal should look similar to the image below

#TODO add image

#### SSH from the browser

1) Navigate back to the VM instance screen  
2) Ensure that you've set up [OS Login](https://cloud.google.com/compute/docs/instances/managing-instance-access#enable_oslogin). You can set this on the project level or instance level. Here is an example of setting this at the instance level:  

#TODO: add image 

3) Run `gcloud auth login` to ensure you're logged in to your account  
4) Run the command below in your terminal

```
gcloud compute os-login ssh-keys add \
    --key-file=KEY_FILE_PATH \
    --ttl=EXPIRE_TIME
```


### Aiflow environment setup
A configuration script is located [here](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/airflow-setup/env-setup.sh). The user is prompted for the dbt and Fivetran API Keys as inputs and store them in environment variables. It's additionally useful to modify the environment activiation script in `/srv/airflow/bin/activate` to automatically set and unset these variables each time the environment starts.  

After running the shell script referenced above, verify you have a new directory under `/srv/airflow`. You should be able to run `source bin/activate` from this location to start your virtual environment.

### SSH key configuration in Github
We use ssh keys to manage both this git repository and the one containing dbt code. You need access to manage ssh keys for your repository (in Settings > Deploy Keys > Add Key). Below is an example of creating an ssh key and granting access in Github: 

* Generate ssh key: `$ ssh-keygen -t ed25519 -C "your_email@example.com"`  
* Choose where to save the key, e.g. $HOME/.ssh/<your-key-pair-name>
* Start the ssh agent in the background: `eval "$(ssh-agent -s)"`
* Check for existing ssh configuration: `open ~/.ssh/config`
* If the configuration file doesn't exist, create it: `touch ~/.ssh/config`
* Open the config file and replace the key Id as necessary: 
```
Host github.com-airflow-fivetran-dbt
  AddKeysToAgent yes
  IdentityFile ~/.ssh/<your-key-pair-name>
```
* Add the ssh key to the agent: `ssh-add -K ~/.ssh/<your-key-pair-name>`
* It's useful to add a line to your `.bashrc` or `.zshrc` file to automatically start the agent and add your ssh keys each time you open a terminal. 
* Add the key to your repository: 

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/git-repo-ssh-keys.png "Adding Deploy Keys to a Repository")

### Git repository configuration
Once you've set ssh keys for both the airflow and dbt code repositories, you clone the respective codebases on the airflow server and in dbt Cloud. Instructions for configuring Github repositories in dbt Cloud are [here](https://docs.getdbt.com/docs/dbt-cloud/cloud-configuring-dbt-cloud/cloud-installing-the-github-application)

### Environment variables  
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

