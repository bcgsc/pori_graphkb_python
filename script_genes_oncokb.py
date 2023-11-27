from graphkb.genes import get_oncokb_oncogenes, get_oncokb_tumour_supressors

from script_conn import connection


# CONNECTION
##############################################################
env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)


oncogenic = get_oncokb_oncogenes(conn)
print(f'oncogenic genes: {len(oncogenic)}')
print(oncogenic)
# for gene in oncogenic:
#     print(gene['displayName'])

suppressor = get_oncokb_tumour_supressors(conn)
print(f'suppressor genes: {len(suppressor)}')
# for gene in suppressor:
#     print(gene['displayName'])
