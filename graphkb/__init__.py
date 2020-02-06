import requests
import json


class GraphKBConnection:
    def __init__(self, url='https://graphkb-api.bcgsc.ca/api'):
        self.token = None
        self.url = url
        self.username = None
        self.password = None
        self.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def request(self, endpoint, method='GET', **kwargs):
        """Request wrapper to handle adding common headers and logging

        Args:
            endpoint (string): api endpoint, excluding the base uri
            method (str, optional): the http method. Defaults to 'GET'.

        Returns:
            dict: the json response as a pythno dict
        """
        url = f'{self.url}/{endpoint}'
        resp = requests.request(method, url, headers=self.headers, **kwargs)

        if resp.status_code == 401 or resp.status_code == 403:
            # try to re-login if the token expired
            self.login(self.username, self.password)
            resp = requests.request(method, url, headers=self.headers, **kwargs)

        return resp.json()

    def post(self, uri, data={}, **kwargs):
        """Convenience method for making post requests"""
        return self.request(uri, method='POST', data=json.dumps(data), **kwargs)

    def login(self, username, password):
        self.username = username
        self.password = password

        content = self.post('token', data={'username': self.username, 'password': self.password})
        self.token = content['kbToken']
        self.headers['Authorization'] = self.token

    def query(self, requestBody={}, paginate=True, limit=1000):
        result = []

        while True:
            content = self.post('query', data={**requestBody, 'limit': limit, 'skip': len(result)})
            records = content['result']
            result.extend(records)
            if len(records) < limit or not paginate:
                break

        return result
