import csv
import re


from .graphkb import GraphKB

BASE_URL = 'http://creisle04.phage.bcgsc.ca:8080/api'
IPRKB_DUMP = '/projects/vardb/downloads/ipr/select_kb_references_ident_as_kb_reference_uuid_kb_references_cr_201905281636.tsv'


def read_tsv(filename):
    print('reading: {}'.format(filename))
    with open(filename, 'r') as fh:
        reader = csv.DictReader(fh, delimiter='\t')
        return [row for row in reader]


def check_cosmic_entries(rows):
    # look for missing oncogene/TSG annotations

    annotated_genes = {}
    missing_oncogenes = set()
    missing_tsg = set()
    validated_oncogenes = set()
    validated_tsg = set()

    for row in rows:
        gene_name = row['kb_reference_events_expression']
        ref_id = row['kb_reference_ref_id']
        if ref_id != 'cancer.sanger.ac.uk/census':
            continue
        if not re.match(r'^\w+$', gene_name):
            print('SKIPPING', gene_name)
            continue
        elif row['kb_reference_relevance'] not in ['oncogene', 'tumour suppressor']:
            continue
        # collect annotations for this gene
        if gene_name in annotated_genes:
            annotations = annotated_genes[gene_name]
        else:
            annotations = api.gene_annotations(gene_name)
            annotated_genes[gene_name] = annotations

        if row['kb_reference_relevance'] == 'oncogene':
            if 'oncogenic' not in annotations:
                print('missing oncogene annotation for {}'.format(gene_name))
                missing_oncogenes.add(gene_name)
            else:
                validated_oncogenes.add(gene_name)
        elif row['kb_reference_relevance'] == 'tumour suppressor':
            if 'tumour suppressive' not in annotations:
                print('missing TSG annotation for {}'.format(gene_name))
                missing_tsg.add(gene_name)
            else:
                validated_tsg.add(gene_name)
    print()
    print('validated onocgenes', len(validated_oncogenes))
    print(sorted(list(validated_oncogenes)))
    print('\n')
    print('validated TSG', len(validated_tsg))
    print(sorted(list(validated_tsg)))
    print('\n')
    print('MISSING oncogene list', len(missing_oncogenes))
    print(sorted(list(missing_oncogenes)))
    print([(m, annotated_genes[m]) for m in missing_oncogenes if annotated_genes[m]])
    print('\n')
    print('MISSING TSG list', len(missing_tsg))
    print(sorted(list(missing_tsg)))
    print([(m, annotated_genes[m]) for m in missing_tsg if annotated_genes[m]])


def check_mdanderson(api, rows):
    expected_ref_id = 'pct.mdanderson.org'
    count = 0
    missing_variant = set()
    relevance_mismatch = 0

    for row in rows:
        # ident = row['kb_reference_uuid']
        for variant in [v.strip() for v in row['kb_reference_events_expression'].split('|')]:
            # b/c otherwise search is a pain
            variant = variant.replace('EGFR:NM_005228:', 'EGFR:')
            ref_id = row['kb_reference_ref_id']

            if row['kb_reference_relevance'] in ['observed', 'not determined']:
                continue
            if ref_id != expected_ref_id:
                continue
            if not variant.startswith('MUT_'):
                continue

            relevance = {
                v['name']
                for v in api.get_vocabulary([row['kb_reference_relevance'].replace('-', ' ')])
            }
            count += 1
            variant = variant.replace('MUT_', '')
            try:
                variants = api.match_protein_variant(variant)

                if variants:
                    pass
                    # print('{}, fetched {} variants'.format(variant, len(variants)))
                    # print({v['displayName'] for v in variants})
                    # now find the statements for this
                    statements = api.statements_by_variants(variants)
                    if not (
                        relevance
                        & {statement['relevance']['displayName'] for statement in statements}
                    ):
                        print(
                            'MISSING STATEMENT RELEVANCE ({}) for variant ({})'.format(
                                row['kb_reference_relevance'], variant
                            )
                        )
                        print(
                            'found:',
                            {statement['relevance']['displayName'] for statement in statements},
                        )
                        relevance_mismatch += 1
                else:
                    print('MISSING VARIANT', variant)
                    missing_variant.add(variant)

            except NotImplementedError as err:
                print(err)

    print('checked {} variants'.format(count))
    print('relevance_mismatch', relevance_mismatch)
    print('missing_variant', len(missing_variant))
    print(missing_variant)


api = GraphKB(BASE_URL)
api.login()

rows = read_tsv(IPRKB_DUMP)

check_mdanderson(api, rows)
