from typing import Dict, Sequence, Set, Union, cast

from .types import DataRecord, Record, Statement

TEMPLATE_KEYS = {
    'disease': '{conditions:disease}',
    'variant': '{conditions:variant}',
    'conditions': '{conditions}',
    'subject': '{subject}',
    'evidence': '{evidence}',
    'relevance': '{relevance}',
}


def rid(record: Record) -> str:
    return record['@rid']


def natural_list_join(items: Sequence[str]) -> str:
    if not items:
        return ''
    elif len(items) > 1:
        return ', '.join(items[:-1]) + ', and ' + items[-1]
    return items[0]


def build_sentence(statement: Statement) -> str:
    """
    Given a statement record, autofill its template display name from the linked records
    """
    template = statement['displayNameTemplate']
    records_consumed: Set[str] = set()
    conditions = statement.get('conditions', [])
    replacements: Dict[str, str] = {}

    def variant_filter(rec: Record) -> bool:
        return rec['@class'].lower().endswith('variant')

    def disease_filter(rec: Record) -> bool:
        return rec['@class'].lower() == 'disease'

    if TEMPLATE_KEYS['subject'] in template and statement['subject']:
        records_consumed.add(rid(statement['subject']))
        replacements[TEMPLATE_KEYS['subject']] = get_preview(statement['subject'])

    for key, filter_func in [
        ('variant', variant_filter),
        ('disease', disease_filter),
        ('conditions', None),
    ]:
        if TEMPLATE_KEYS[key] in template:
            records = [
                rec
                for rec in conditions
                if (not filter_func or filter_func(rec)) and rid(rec) not in records_consumed
            ]
            records_consumed.update([rid(r) for r in records])
            replacements[TEMPLATE_KEYS[key]] = natural_list_join([get_preview(v) for v in records])

    if TEMPLATE_KEYS['relevance'] in template and statement['relevance']:
        replacements[TEMPLATE_KEYS['relevance']] = get_preview(statement['relevance'])

    if TEMPLATE_KEYS['evidence'] in template and statement['evidence']:
        replacements[TEMPLATE_KEYS['evidence']] = ', '.join(
            [get_preview(e) for e in statement['evidence']]
        )

    result = template
    for key, substitution in replacements.items():
        result = result.replace(key, substitution)
    return result


def get_preview(record: Union[DataRecord, Statement]) -> str:
    if record.get('displayName', ''):
        return record['displayName']
    if record['@class'] != 'Statement':
        return record['name']  # type: ignore
    return build_sentence(cast(Statement, record))
