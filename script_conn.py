import os
from graphkb import GraphKBConnection

GKB_USER = {
    "local" : os.environ['USER'],
    "dev" : os.environ['USER'],
    # "staging" : 'graphkb_importer',
    "staging" : os.environ['USER'],
    "prod" : os.environ['USER'],
}
GKB_PASSWORD = {
    "local" : os.environ['JIRA_PASS'],
    "dev" : os.environ['JIRA_PASS'],
    # "staging" : os.environ['GKB_PASS'],
    "staging" : os.environ['JIRA_PASS'],
    "prod" : os.environ['JIRA_PASS'],
}
GKB_API_URL = {
    "local" : "http://mlemieux01.phage.bcgsc.ca:8080/api/",
    "dev" : "https://graphkbdev-api.bcgsc.ca/api",
    "staging" : "https://graphkbstaging-api.bcgsc.ca/api",
    "prod" : "https://graphkb-api.bcgsc.ca/api",
}

def connection(env):
    conn = GraphKBConnection(GKB_API_URL[env], use_global_cache=False)
    conn.login(GKB_USER[env], GKB_PASSWORD[env])
    return conn