import requests
import os
import getpass
import json
import re


class TestRegex:
    def __init__(self):
        self.last_match = None

    def match(self, pattern, string):
        self.last_match = re.match(pattern, string)
        return self.last_match

    def __call__(self, pattern, string):
        return self.match(pattern, string)

    def groups(self):
        return self.last_match.groups()


test_match = TestRegex()


def match_clause(attr, *possible_values):
    filters = [{'attr': attr, 'value': None}, {'attr': attr, 'value': '?'}]
    for value in possible_values:
        filters.append({'attr': attr, 'value': value})
    return {'operator': 'OR', 'comparisons': filters}


def match_pos_clause(attr, *possible_values):
    filters = [{'attr': attr, 'value': None}]
    for value in possible_values:
        filters.append({'attr': attr, 'value': value})
    return {'operator': 'OR', 'comparisons': filters}


class GraphKB:
    def __init__(self, url, verbose=False, cache_requests=True):
        self.url = url
        self.verbose = verbose
        self.headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.request_cache = {}
        self.cache_requests = cache_requests

    def request(self, endpoint, method='GET', **kwargs):
        """Request wrapper to handle adding common headers and logging

        Args:
            endpoint (string): api endpoint, excluding the base uri
            method (str, optional): the http method. Defaults to 'GET'.

        Returns:
            dict: the json response as a pythno dict
        """
        url = f'{self.url}/{endpoint}'
        if self.verbose:
            print(method, url)
        resp = requests.request(method, url, headers=self.headers, **kwargs)
        return resp.json()

    def post(self, uri, data={}, **kwargs):
        """Convenience method for making post requests"""
        return self.request(uri, method='POST', data=json.dumps(data), **kwargs)

    def search(self, model_name, data={}, **kwargs):
        """Convenience method for making search requests

        Args:
            model_name (str): the database model/class ex. diseases
            data (dict): the payload/data to send in the request

        Returns:
            dict: the json response as a pythno dict
        """
        data = json.dumps(data, sort_keys=True)
        cache_key = ('search', model_name, data)

        if self.cache_requests and cache_key in self.request_cache:
            return self.request_cache[cache_key]
        resp = self.request(f'{model_name}/search', method='POST', data=data, **kwargs)
        if self.cache_requests:
            self.request_cache[cache_key] = resp
        return resp

    def get(self, uri, **kwargs):
        """Convenience method for get requests"""
        return self.request(uri, method='GET', **kwargs)

    def login(self, username=getpass.getuser(), password=None):
        """
        get the authorization token and add it to the default headers

        Args:
            username (string): the user name
            password (string): the password for the current user
        """
        if password is None:
            if os.environ.get('PASSWORD', None) is None:
                password = getpass.getpass()
            else:
                password = os.environ['PASSWORD']

        self.username = username
        self.password = password

        content = self.post('token', data={'username': self.username, 'password': self.password})
        self.token = content['kbToken']
        self.headers['Authorization'] = self.token

    def search_for_gene(self, gene_name):
        """Given some gene name, search for it or deprecated/alias forms of it"""
        return self.search('features', data={'search': {'name': [gene_name]}})['result']

    def match_fusion(self, gene1, gene2):
        genes1 = [g['@rid'] for g in self.search_for_gene(gene1)]
        genes2 = [g['@rid'] for g in self.search_for_gene(gene2)] if gene2 else None
        vocab = [t['@rid'] for t in self.get('vocabulary', params={'name': '~fusion'})['result']]
        # 2. Get the variants related to these genes
        filters = [
            {'attr': 'reference1', 'value': genes1, 'operator': 'in'},
            {'attr': 'reference2', 'value': genes2, 'operator': 'in' if gene2 else 'IS'},
            {'attr': 'type', 'operator': 'in', 'value': vocab},
        ]
        variants = self.search('variants', data={'where': filters})['result']
        return variants

    def match_exon_fusion(self, gene1, gene2, exon1=None, exon2=None):
        genes1 = [g['@rid'] for g in self.search_for_gene(gene1)]
        genes2 = [g['@rid'] for g in self.search_for_gene(gene2)]
        vocab = [t['@rid'] for t in self.get('vocabulary', params={'name': '~fusion'})['result']]
        # 2. Get the variants related to these genes
        filters = [
            {'attr': 'reference1', 'value': genes1, 'operator': 'in'},
            {'attr': 'reference2', 'value': genes2, 'operator': 'in'},
            {'attr': 'type', 'value': vocab, 'operator': 'in'},
            {'attr': 'break1Start.pos', 'value': exon1},
            {'attr': 'break2Start.pos', 'value': exon2},
        ]
        variants = self.search('variants', data={'where': filters})['result']
        return variants

    def statements_by_gene_name(self, gene_name):
        """Given some gene name, loosely look for associated statements"""
        # 1. Get the gene you are intersted in
        genes = [g['@rid'] for g in self.search_for_gene(gene_name)]

        # 2. Get the variants related to this gene
        variants = self.search(
            'variants',
            data={
                'where': {
                    'operator': 'OR',
                    'comparisons': [
                        {'attr': 'reference1', 'value': genes, 'operator': 'in'},
                        {'attr': 'reference2', 'value': genes, 'operator': 'in'},
                    ],
                }
            },
        )['result']

        statements = self.search(
            'statements', data={'search': {'impliedBy': [v["@rid"] for v in variants]}}
        )['result']
        return statements

    def statements_by_variants(self, variants):
        statements = self.search(
            'statements', data={'search': {'impliedBy': [v["@rid"] for v in variants]}}
        )['result']
        return statements

    def drugs_targeting_gene_name(self, gene_name):
        """Given some gene name, loosely look for drugs which target it"""
        genes = '|'.join([g['@rid'].replace(r'^#', '') for g in self.search_for_gene(gene_name)])
        # 2. Get the drugs related to these genes
        return self.get('targetof', params={'out': genes, 'neighbors': 1})['result']

    def get_vocabulary(self, terms):
        """Given some gene name, search for it or deprecated/alias forms of it"""
        return self.search('vocabulary', data={'search': {'name': terms}})['result']

    def gene_annotations(self, gene_name, relevance=['oncogenic', 'tumour suppressive']):
        genes = [g['@rid'].replace(r'^#', '') for g in self.search_for_gene(gene_name)]
        if not genes:
            return {}
        vocab = [
            v['@rid'].replace(r'^#', '')
            for v in self.get_vocabulary(relevance)
        ]
        statements = self.get(
            'statements',
            params={'appliesTo': '|'.join(genes), 'relevance': '|'.join(vocab), 'neighbors': 1},
        )['result']

        return {s['relevance']['name'] for s in statements}

    def match_category_variant(
        self, gene_name, category, zygosity=None, germline=None, strict=False
    ):
        genes = [g['@rid'] for g in self.search_for_gene(gene_name)]
        if not strict:
            types = [t['@rid'] for t in self.get_vocabulary([category])]
        else:
            types = [t['@rid'] for t in self.get('vocabulary', params={'name': category})['result']]
        filters = [
            {'attr': 'reference1', 'operator': 'in', 'value': genes},
            {'attr': 'type', 'operator': 'in', 'value': types},
        ]
        if zygosity is not None:
            filters.append({'attr': 'zygosity', 'value': zygosity})
        if germline is not None:
            filters.append({'attr': 'germline', 'value': bool(germline)})
        # deletion
        variants = self.search('categoryvariants', data={'where': filters})
        return variants['result']

    def match_protein_variant(self, protein_variant, zygosity=None, germline=None):

        filters = []
        gene_name = None

        if zygosity is not None:
            filters.append({'attr': 'zygosity', 'value': zygosity})
        if germline is not None:
            filters.append({'attr': 'germline', 'value': bool(germline)})

        if test_match(r'^(\w+):p\.([A-Z?])(\d+)([A-Z?*])$', protein_variant):
            # protein substitution/missense variant
            [gene_name, ref_aa, aa_pos, alt_aa] = test_match.groups()

            filters.extend(
                [
                    match_pos_clause('untemplatedSeqSize', 1),
                    {'attr': 'break1Start.pos', 'value': aa_pos},
                ]
            )
            if alt_aa not in ['?', 'X']:
                filters.append(match_clause('untemplatedSeq', alt_aa, 'X'))
        elif test_match(
            r'(\w+):p\.([A-Z?])(\d+)(_([A-Z?])(\d+))?del([A-Z\*?]+)?$', protein_variant
        ):
            # deletion
            [gene_name, start_aa, start, _, end_aa, end, ref_seq] = test_match.groups()
            filters.extend(
                [
                    match_pos_clause('untemplatedSeqSize', 0),
                    match_clause('untemplatedSeq', ''),
                    {'attr': 'break1Start.pos', 'value': start},
                ]
            )
            if end:
                filters.append({'attr': 'break2Start.pos', 'value': end})
            if ref_seq:
                filters.append(match_clause('refSeq', ref_seq))
        elif test_match(r'(\w+):p\.([A-Z?])(\d+)_([A-Z?])(\d+)ins([A-Z\*?]+)?$', protein_variant):
            # insertion
            [gene_name, start_aa, start, end_aa, end, alt_seq] = test_match.groups()
            filters.extend(
                [
                    {'attr': 'break1Start.pos', 'value': start},
                    {'attr': 'break2Start.pos', 'value': end},
                ]
            )
            if alt_seq:
                filters.append(match_pos_clause('untemplatedSeqSize', len(alt_seq)))
                filters.append(match_clause('untemplatedSeq', alt_seq))
        elif test_match(
            r'(\w+):p\.([A-Z?])(\d+)_([A-Z?])(\d+)del([A-Z\*?]+)?ins([A-Z\*?]+)?$', protein_variant
        ):
            # indel
            [gene_name, start_aa, start, end_aa, end, ref_seq, alt_seq] = test_match.groups()
            filters.extend(
                [
                    {'attr': 'break1Start.pos', 'value': start},
                    {'attr': 'break2Start.pos', 'value': end},
                ]
            )
            if ref_seq:
                filters.append(match_clause('refSeq', ref_seq))
            if alt_seq:
                filters.append(match_pos_clause('untemplatedSeqSize', len(alt_seq)))
                filters.append(match_clause('untemplatedSeq', alt_seq))
        elif test_match(r'^(\w+):p.([A-Z?])(\d+)([A-Z?])?fs(\*(\d+))?$', protein_variant):
            [gene_name, ref_seq, pos, alt_seq, _, truncation] = test_match.groups()
            filters.extend(
                [
                    {'attr': 'break1Start.pos', 'value': pos},
                    {'attr': 'type.name', 'value': 'frameshift'},
                ]
            )
            if ref_seq:
                filters.append(match_clause('refSeq', ref_seq))
            # if alt_seq:
            #     filters.append(match_pos_clause('untemplatedSeqSize', len(alt_seq)))
            #     filters.append(match_clause('untemplatedSeq', alt_seq))
            # if truncation:
            #     filters.append({'attr': 'truncation', 'value': int(truncation)})

        else:
            raise NotImplementedError(f'missing logic to handle ({protein_variant}) variant')

        genes = [g['@rid'] for g in self.search_for_gene(gene_name)]
        filters.append({'attr': 'reference1', 'operator': 'in', 'value': genes})
        # deletion
        variants = self.search('positionalvariants', data={'where': filters})
        return variants['result']
