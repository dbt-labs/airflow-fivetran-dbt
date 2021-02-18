# airflow-fivetran-dbt
The purpose of this github repo is to provide an example of what an orchestration pipeline for Fivetran + dbt managed by Airflow would look like. If you have any questions about this, feel free to ask in our [dbt Slack community](https://community.getdbt.com/).

# Introduction
This is one way to orchetstrate dbt in coordination with other tools, such as Fivetran for data loading. In this example, our focus is on coordinating a Fivetran sync for loading data to a warehouse, and then triggering a dbt run in an event-driven pipeline. We use the Fivetran and dbt Cloud APIs to accomplish this, with Airflow managing the scheduling / orchestration of the job flow. The final step extracts the `manifest.json` from the dbt run results to capture relevant metadata for downstream logging, alerting and analysis. The code provided in this repository are intended as a demonstration to build upon and should not be utilized as a production-ready solution. 

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
- Airflow code can be run from a managed service like [Astronomer](https://www.astronomer.io/)  
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
3) User account in dbt Cloud with sufficient permissions to create database connections, repositories, and API keys. 
4) User account in Github/Gitlab/Bitbucket etc with permissions to create repositories and associate ssh deploy keys with them. You can read more about this setup [here](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

### Airflow Installation

Key Notes not mentioned in Jostein Leira's Post:
- Make sure to create the instance in the desired project (whether an existing one or a new one)
- You will need to enable the Compute Engine API
- When you create the subnet, make sure to select a region that makes sense to your infastructure. 
- For your VM machine type, use E2 series. 
- You do not need to setup a load balancer for this flow. 
- When you go to setup your Postgres database, do not click on Storage. The interface has updated and you should see 
`SQL` in the GCP console. 
- Whitelist only the [Google IP Ranges](https://support.google.com/a/answer/60764?hl=en) and any developer IP addresses. You will be asked this when you setup the VPC.  
- Install apache-airflow v2.0.0 instead of v1.10.10. Note that airflow command syntax changed slightly across major versions. The Airflow v2.0.0 CLI command syntax is documented [here](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)  

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

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/gcp-create-project.png "Create new GCP project")

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

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/gcp-create-firewall-rules.png "VPC firewall rules")

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

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/gcp-place-instance-in-network.png "Add the instance to your network")

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

#### SSH from the browser

1) Ensure that you've set up [OS Login](https://cloud.google.com/compute/docs/instances/managing-instance-access#enable_oslogin). You can set this on the project level or instance level. Here is an example of setting this at the instance level:  

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/gcp-ssh-to-vm.png "SSH to the VM")

2) Whitelist the list of Google IPs [listed here](https://www.gstatic.com/ipranges/goog.json) for port 22 in your custom network. Connections from the browser are initiated from a Google IP, not your network's IP.  
3) Navigate back to the VM instance screen  
4) Click the "SSH" buttom to the right of your VM's listing  

### Cloning this Git Repository to the VM

#### SSH key configuration in Github
We use ssh keys to manage both this git repository with the Airflow code and the one containing dbt code. You will need access to manage ssh keys for your repository (in Settings > Deploy Keys > Add Key). Below is an example of creating an ssh key and granting access in Github: 

1) Generate ssh key: `$ ssh-keygen -t ed25519 -C "your_email@example.com"`  
2) Choose where to save the key, e.g. $HOME/.ssh/<your-key-pair-name>
3) Start the ssh agent in the background: `eval "$(ssh-agent -s)"`
4) If the configuration file doesn't exist, create it: `vim ~/.ssh/config`
5) Open the config file and replace the key Id as necessary: 

```
Host github.com-airflow-fivetran-dbt
  AddKeysToAgent yes
  IdentityFile ~/.ssh/<your-key-pair-name>
```

6) Add the ssh key to the agent: `ssh-add ~/.ssh/<your-key-pair-name>`
Note: It's useful to add a line to your `.bashrc` or `.zshrc` file to automatically start the agent and add your ssh keys each time you open a terminal. 
7) run `cd ~/.ssh/`  
8) run `cat <your-key-pair-name>.pub`  
9) Copy the output on the screen  
10) In github, add the public key to the repository. This is in Settings > Deploy Keys > Add New Key. The screenshot below shows what this looks like  

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/git-repo-ssh-keys.png "Adding Deploy Keys to a Repository")

11) Run `cd /srv/airflow`  
12) Run `git clone git@github.com:fishtown-analytics/airflow-fivetran-dbt.git` to clone the repository

### Cloning the dbt Code repository in dbt Cloud

Note, this repository is related to [another](https://github.com/fishtown-analytics/airflow-fivetran-dbt--dbt-jobs) which contains the dbt code run in the job triggered from Airflow. You'll need to set a similar repository to run the dbt jobs for your setup. Instructions for cloning git repositories in dbt Cloud can be found [here](https://docs.getdbt.com/docs/dbt-cloud/cloud-configuring-dbt-cloud/cloud-import-a-project-by-git-url)

Once you've set ssh keys for both the airflow and dbt code repositories,  clone the respective codebases on the airflow server and in dbt Cloud. Instructions for configuring Github repositories in dbt Cloud are [here](https://docs.getdbt.com/docs/dbt-cloud/cloud-configuring-dbt-cloud/cloud-installing-the-github-application)

### Aiflow environment setup
Make sure you have the Fivetran API Key, dbt Cloud API Key, and dbt Cloud Account ID handy before going further. These are set into environment variables for Airflow.  

1) Run `source airflow-fivetran-dbt/airflow-setup/start-airflow-venv.sh`  
2) Set the environment variables for the Fivetran API Key, dbt Cloud API Key and dbt Cloud Account ID  
3) Feel free to manage the virtual environment and environment variables as suits you  

Below is a description of each environment variable set by the script.  

* `FIVETRAN_API_KEY`: This is a base64 encoded value of your account's `<api-key>:<api-secret>`. [This link from Fivetran](https://fivetran.com/docs/rest-api/getting-started) documents how to generate this value. For example, an API key of `d9c4511349dd4b86` and API secret of `1f6f2d161365888a1943160ccdb8d968` encode to `ZDljNDUxMTM0OWRkNGI4NjoxZjZmMmQxNjEzNjU4ODhhMTk0MzE2MGNjZGI4ZDk2OA==`. The specific values will be different on your system.  
* `FIVETRAN_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`
* `AIRFLOW_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`
* `DBT_ACCOUNT_ID` which can be obtained from the URLs when logged in to dbt Cloud. For example in the URL cloud.getdbt.com/#/accounts/**<account-id>**/projects/<project-id>/dashboard/
* `DBT_API_KEY` which can be obtained by navigating to Profile > API Access in dbt Cloud.
* `DBT_DATETIME_FORMAT` set to `%Y-%m-%dT%H:%M:%S.%fZ` for a datetime like `2018-12-01T15:43:29.013729Z`

### Setting up the Postgres Database

Airflow persits artifacts into a database, often Postgresql.  

1) Navigate to the hamburger icon at the top left > Databases > SQL  
2) Click "Create Instance"  
3) Give the instance a name and default user password  
4) Click "Connectivity"  
5) Check the option for "Private IP", associate the instance with your vpc network, and uncheck the "Public IP" option at the bottom of the Connectivity tab  
6) Click "Allocate and Connect"  

![alt text](https://github.com/fishtown-analytics/airflow-fivetran-dbt/blob/main/images/gcp-associate-db-instance-with-network.png "Add db instance to your network")

7) Under the SQL menu at the top left, click "Databases"  
8) Click "Create database" and give your database a name  
9) Under the SQL menu at the top left, click "Users" and add a new user  
10) Be sure to add a user to the instance and not a Cloud IAM user  

### Test database connectivity

Note: make sure that the psql client is installed on your instance. This aspect is skipped in the guide linked from Medium above. If missing, you can install the client by running the following: 

```
sudo apt-get -y install postgresql-client-<version>
```

From the Airflow VM, test connectivity to the db instance

```
psql -h <db-server-ip> -U airflow-user -d airflow
```

Then enter the password you set when configuring the database  


### Start the Airflow server

1) Run the following sequence of commands:  
  * `sudo su airflow`  
  * `cd /srv/airflow`  
  * `source bin/activate`  
  * `export AIRFLOW_HOME=/srv/airflow`  
  * `airflow db init`  

2) Now you will update the `airflow.cfg` file to point airflow towards your sql database server instead of the default sqlite database. Update the following configurations in the file: 

`sql_alchemy_conn = postgresql+psycopg2://airflow-user:<db-password>@<db-server-ip>/<database-name>`
`default_impersonation = airflow`  
`enable_proxy_fix = True`  

3) Run `airflow db init` again
4) Run 
```
airflow users create \
          --username <user-name> \
          --password <password>
          --firstname <first-name> \
          --lastname <last-name> \
          --role Admin \
          --email <email>@example.org
```
5) Run `airflow webserver -p 8080`  
6) Run `airflow scheduler`  

You now have a functioning system to which you can upload the [airflow code provided here](https://github.com/fishtown-analytics/airflow-fivetran-dbt). Add the load balancer configuration per instructions in the linked Medium post. Additionally, we provide service configuration files in this repository as well to run your airflow webserver automatically upon starting up the VM.  

### Running the code

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

