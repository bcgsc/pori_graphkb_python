import requests
import os
import getpass
import json


BASE_URL = 'http://creisle04.phage.bcgsc.ca:8080/api'
# get the authorization token
r = requests.post(
    '{}/token'.format(BASE_URL),
    data={
        'username': os.environ['USER'],
        'password': getpass.getpass()
        if os.environ.get('PASSWORD', None) is None
        else os.environ['PASSWORD'],
    },
)
print(r.json())
token = r.json()[
    'kbToken'
]  # now you can use this token in the authorization header for all subsequent requests

HEADERS = {'Authorization': token, 'Accept': 'application/json', 'Content-Type': 'application/json'}

# How to use the search endpoint

# 1. Get the gene you are intersted in
query_string = '?name=kras'
genes = requests.get('{}/features{}'.format(BASE_URL, query_string), headers=HEADERS).json()[
    'result'
]
genes = [g['@rid'] for g in genes]
print(genes)

# 2. Get the variants related to this gene
payload = {
    'where': {
        'operator': 'OR',
        'comparisons': [
            {'attr': 'reference1', 'value': genes, 'operator': 'in'},
            {'attr': 'reference2', 'value': genes, 'operator': 'in'},
        ],
    }
}
variants = requests.post(
    '{}/variants/search'.format(BASE_URL), data=json.dumps(payload), headers=HEADERS
).json()['result']
print([v['displayName'] for v in variants])
print('returned {} variants'.format(len(variants)))

# 3. then extract the statements for that gene
payload = {'search': {'impliedBy': [v["@rid"] for v in variants]}}
statements = requests.post(
    '{}/statements/search'.format(BASE_URL), data=json.dumps(payload), headers=HEADERS
).json()['result']

for statement in statements:
    conditions = ', and '.join([cond['displayName'] for cond in statement['impliedBy']])
    support = ', '.join([v['displayName'] for v in statement['supportedBy']])
    print(statement['@rid'])
    print(
        statement['displayNameTemplate'].format(
            impliedBy=conditions,
            supportedBy=support,
            appliesTo=statement['appliesTo']['displayName'] if statement['appliesTo'] else '',
            relevance=statement['relevance']['displayName'],
        )
    )
