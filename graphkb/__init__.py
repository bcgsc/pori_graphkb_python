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

            self.refresh_login()
            resp = requests.request(method, url, headers=self.headers, **kwargs)

        resp.raise_for_status()

        return resp.json()

    def post(self, uri, data={}, **kwargs):
        """Convenience method for making post requests"""
        return self.request(uri, method='POST', data=json.dumps(data), **kwargs)

    def login(self, username, password):
        self.username = username
        self.password = password

        # use requests package directly to avoid recursion loop on login failure
        resp = requests.request(
            url=f'{self.url}/token',
            method='POST',
            headers=self.headers,
            data=json.dumps({'username': username, 'password': password}),
        )
        resp.raise_for_status()
        content = resp.json()
        self.token = content['kbToken']
        self.headers['Authorization'] = self.token

    def refresh_login(self):
        self.login(self.username, self.password)

    def query(self, requestBody={}, paginate=True, limit=1000):
        result = []

        while True:
            content = self.post('query', data={**requestBody, 'limit': limit, 'skip': len(result)})
            records = content['result']
            result.extend(records)
            if len(records) < limit or not paginate:
                break

        return result

    def parse(self, hgvs_string, requireFeatures=False):
        content = self.post(
            'parse', data={'content': hgvs_string, 'requireFeatures': requireFeatures}
        )
        return content['result']
