from graphkb.genes import get_gene_information
from script_conn import connection

# CONNECTION
##############################################################
env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# DATA
##############################################################
genes = ['BRCA2', 'ALB']
info = get_gene_information(conn, genes)

# LOGGING
##############################################################
print(info)
