from graphkb.genes import get_cancer_predisposition_info, get_pharmacogenomic_info

from script_conn import connection


# CONNECTION
##############################################################
env = 'dev'  # 'local' | 'dev' | 'staging' | 'prod'
conn = connection(env)

# get_cancer_predisposition_info
genes, variants = get_cancer_predisposition_info(conn)
print('\nget_cancer_predisposition_info', '\n#############################################')
print(f'\ngenes: {len(genes)}', '\n**************************')
with open("genes.txt", "w") as f:
    for gene in genes:
        print(gene, file=f)
print(f'\nvariants: {len(variants)}', '\n**************************')
with open("variants.tsv", "w") as f:
    for k, v in variants.items():
        print(k, v, sep="\t", file=f)

# # get_pharmacogenomic_info
# genes, variants = get_pharmacogenomic_info(conn)
# print('\nget_pharmacogenomic_info', '\n#############################################')
# print(f'\ngenes: {len(genes)}', '\n**************************')
# for gene in genes:
#     print(gene)
# print(f'\nvariants: {len(variants)}', '\n**************************')
# for k, v in variants.items():
#     print(k, v)
