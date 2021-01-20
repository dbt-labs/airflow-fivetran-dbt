# airflow-fivetran-dbt
Example orchestration pipeline for Fivetran + dbt managed by Airflow

# Introduction
This is one way to orchetstrate dbt in coordination with other tools, such as Fivetran for data loading. Our focus is on coordinating Fivetran for loading data to a warehouse, and then triggering a dbt run in an event-driven pipeline. The final step in dbt extracts the `manifest.json` from the dbt run results to capture relevant metadata for downstream logging, alerting and analysis. We did not develop code to ship the `manifest.json` to a logging system such as DataDog or Sumologic. The code provided in this repository are intended as a demonstration to build upon, *not* as a production-ready soluition. 

# What you need to run this guide

#### Systems
1) Snowflake account with database, warehouse etc. configured  
2) Fivetran account with permission to upload data to Snowflake  
3) Source data configured in Fivetran - this guide uses Google Sheets as the source  
4) Google Cloud Platform account  
5) dbt Cloud account  
6) Git repository for dbt code

#### User permissions
1) User with access to run database operations in Snowflake. dbt operates under a user account alias  
2) User account in Fivetran with permissions to create new connectors. In this example, we use Google Sheets as the connector source data. You will also need sufficient permissions (or a friend who has them :) ) to obtain an API token and secret from the Fivetran Admin console as described [here](https://fivetran.com/docs/rest-api/getting-started)  
3) User account in dbt with sufficient permissions to create database connections, repositories, and API keys. 
4) User account in Github/Gitlab/Bitbucket etc with permissions to create repositories and associate ssh deploy keys with them. You can read more about this setup [here](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)
