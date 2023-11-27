from graphkb.genes import _get_tumourigenesis_genes_list, get_cancer_genes, get_oncokb_oncogenes, get_oncokb_tumour_supressors
from graphkb.constants import TSO500_SOURCE_NAME, ONCOKB_SOURCE_NAME, CANCER_GENE

from script_conn import connection


# CONNECTION
##############################################################
env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)


# oncogenic = get_oncokb_oncogenes(conn)
# print(f'\noncogenic genes:')
# print(len(oncogenic))
# print(oncogenic[0])

# suppressor = get_oncokb_tumour_supressors(conn)
# print(f'\nsuppressor genes:')
# print(len(suppressor))
# print(suppressor[0])

cancer_genes = get_cancer_genes(conn)
print(f'cancer genes ({len(cancer_genes)}) :')
# print(len(cancer_genes))
geneList = [gene["displayName"] for gene in cancer_genes]
geneList.sort()
for gene in geneList:
     print(gene)


# cancer_genes2 = _get_tumourigenesis_genes_list(
#     conn,
#     CANCER_GENE,
#     [
#         ONCOKB_SOURCE_NAME,
#         TSO500_SOURCE_NAME,
#     ]
# )
# print(f'\ncancer_genes2:')
# print(len(cancer_genes2))
# print(cancer_genes2[0])

