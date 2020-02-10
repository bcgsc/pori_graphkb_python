import requests
import json
import hashlib

DEFAULT_URL = 'https://graphkb-api.bcgsc.ca/api'
DEFAULT_LIMIT = 1000


class GraphKBConnection:
    def __init__(self, url=DEFAULT_URL):
        self.token = None
        self.url = url
        self.username = None
        self.password = None
        self.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.cache = {}

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

    def query(
        self,
        requestBody={},
        paginate=True,
        ignore_cache=True,
        force_refresh=False,
        limit=DEFAULT_LIMIT,
    ):
        result = []
        hash_code = ""

        if not ignore_cache:
            body = json.dumps(requestBody, sort_keys=True)
            hash_code = hashlib.md5(f'/query{body}'.encode('utf-8')).hexdigest()
            if hash_code in self.cache and not force_refresh:
                return self.cache[hash_code]

        while True:
            content = self.post('query', data={**requestBody, 'limit': limit, 'skip': len(result)})
            records = content['result']
            result.extend(records)
            if len(records) < limit or not paginate:
                break

        if not ignore_cache:
            self.cache[hash_code] = result
        return result

    def parse(self, hgvs_string, requireFeatures=False):
        content = self.post(
            'parse', data={'content': hgvs_string, 'requireFeatures': requireFeatures}
        )
        return content['result']

    def get_records_by_id(self, record_ids):
        if not record_ids:
            return []
        result = self.query({'target': record_ids})
        if len(record_ids) != len(result):
            raise AssertionError(
                f'The number of Ids given ({len(record_ids)}) does not match the number of records fetched ({len(result)})'
            )
        return result

    def get_record_by_id(self, record_id):
        result = self.get_records_by_id([record_id])
        return result[0]

    def get_source(self, name):
        source = self.query({'target': 'Source', 'filters': {'name': name}})
        if len(source) != 1:
            raise AssertionError(f'Unable to unqiuely identify source with name {name}')
        return source[0]
