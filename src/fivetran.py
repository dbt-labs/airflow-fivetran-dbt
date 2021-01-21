
# -*- coding: utf-8 -*-
import json
import requests
import time
from datetime import datetime
import pytz

class FivetranApi(object):
    """
    Class for interacting with the Fivetran API
    * :py:meth:`get_groups` - list all groups in the target account
    * :py:meth:`get_group_connectors` - list all connectors attached to a given group
    * :py:meth:`get_connector` - get connector information
    * :py:meth: `force_connector_sync` - Trigger a sync of the connector's target dataset
    * :py:meth: `get_connector_sync_status` - Return the status of connector sync process
    """

    def __init__(self, api_token, fivetran_datetime_format, airflow_datetime_format):
        self.api_token = api_token
        self.fivetran_datetime_format = fivetran_datetime_format
        self.airflow_datetime_format = airflow_datetime_format
        self.api_base = 'https://api.fivetran.com/v1/'
        self.polling_timeout = 300 # timeout in seconds on a polling loop
        

    def _get(self, url_suffix):
        url = self.api_base + url_suffix
        headers = {'Content-Type': 'application/json', 'Authorization': 'Basic %s' % self.api_token}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise RuntimeError(response.content)

    def _post(self, url_suffix, data=None):
        url = self.api_base + url_suffix
        print('request url: ', url)
        print('showing request body: ', json.dumps(data))
        headers = {'Content-Type': 'application/json', 'Authorization': 'Basic %s' % self.api_token}

        response = requests.post(url, data=json.dumps(data), headers=headers)
        
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise RuntimeError(response.text)
    
    def get_groups(self):
        """Returns group information from the fivetran account"""
        return self._get(url_suffix='groups/').get('data')

    def get_group_connectors(self, group_id):
        """Returns information about connectors attached to a group"""
        return self._get(url_suffix=f'groups/{group_id}/connectors').get('data')
    
    def get_connector(self, connector_id):
        """Returns information about the connector under connector_id"""
        return self._get(url_suffix=f'connectors/{connector_id}').get('data')
    
    def force_connector_sync(self, request_body={}, **kwargs):
        """Triggers a run of the target connector under connector_id"""
        connector_id = kwargs['dag_run'].conf['fivetran_connector_id'] # this comes from the airflow runtime configs
        response = self._post(url_suffix=f'connectors/{connector_id}/force', data=request_body).get('data')
        start_time = datetime.now()
        kwargs['ti'].xcom_push(key='start_time', value=str(start_time))
        
        return {
            'message': f'successfully ran connector sync for {connector_id}',
            'response': response
            }
    
    def get_connector_sync_status(self, **kwargs):
        """Checks the execution status of connector"""
        connector_id = kwargs['dag_run'].conf['fivetran_connector_id'] # this comes from the airflow runtime configs        
        
        ti = kwargs['ti']
        connector_sync_start_time = ti.xcom_pull(key = 'start_time', task_ids='fivetran_connector_sync')
        connector_sync_start_time = datetime.strptime(connector_sync_start_time, self.airflow_datetime_format)
        
        # use this polling process with a timeout, because fivetran
        # returns the last time a given connector sync completed
        # this COULD BE from a prior run of the sync process
        tracker = 0
        poll_for_success = True
        while poll_for_success:
            # wait a bit between polling runs 
            time.sleep(5) 
            # check on the sync data
            response = self._get(url_suffix=f'connectors/{connector_id}').get('data')
            # get the sync success timestamp from the response
            succeeded_at = response['succeeded_at']
            # convert succeeded_at to UTC so it matches the start_time recorded by airflow server
            succeeded_at = datetime.strptime(succeeded_at, self.fivetran_datetime_format)
            
            if succeeded_at > connector_sync_start_time:
                poll_for_success = False
                return {
                    'message': f'successfully returned connector sync status for {connector_id}',
                    'response': response
                }
            
            tracker += 5
            if tracker > self.polling_timeout:
                raise Exception(f'Error, the data sync for the {connector_id} connecter failed to complete within {self.polling_timeout} seconds')