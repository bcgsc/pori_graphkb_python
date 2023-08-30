"""Methods for retrieving gene annotation lists from GraphKB."""
from typing import Any, Dict, List, Sequence, Set, Tuple, cast

from . import GraphKBConnection
from .constants import (
    BASE_THERAPEUTIC_TERMS,
    CHROMOSOMES,
    FAILED_REVIEW_STATUS,
    GENE_RETURN_PROPERTIES,
    ONCOGENE,
    ONCOKB_SOURCE_NAME,
    PHARMACOGENOMIC_SOURCE_EXCLUDE_LIST,
    PREFERRED_GENE_SOURCE,
    RELEVANCE_BASE_TERMS,
    TUMOUR_SUPPRESSIVE,
)
from .match import get_equivalent_features
from .types import Ontology, Statement, Variant
from .util import get_rid, logger
from .vocab import get_terms_set


def _get_oncokb_gene_list(
    conn: GraphKBConnection, relevance: str, ignore_cache: bool = False
) -> List[Ontology]:
    source = conn.get_source(ONCOKB_SOURCE_NAME)["@rid"]

    statements = cast(
        List[Statement],
        conn.query(
            {
                "target": "Statement",
                "filters": [
                    {"source": source},
                    {"relevance": {"target": "Vocabulary", "filters": {"name": relevance}}},
                ],
                "returnProperties": [f"subject.{prop}" for prop in GENE_RETURN_PROPERTIES],
            },
            ignore_cache=ignore_cache,
        ),
    )
    genes: Dict[str, Ontology] = {}

    for statement in statements:
        if statement["subject"].get("biotype", "") == "gene":
            record_id = statement["subject"]["@rid"]
            genes[record_id] = statement["subject"]

    return [gene for gene in genes.values()]


def get_oncokb_oncogenes(conn: GraphKBConnection) -> List[Ontology]:
    """Get the list of oncogenes stored in GraphKB derived from OncoKB.

    Args:
        conn: the graphkb connection object

    Returns:
        gene (Feature) records
    """
    return _get_oncokb_gene_list(conn, ONCOGENE)


def get_oncokb_tumour_supressors(conn: GraphKBConnection) -> List[Ontology]:
    """Get the list of tumour supressor genes stored in GraphKB derived from OncoKB.

    Args:
        conn: the graphkb connection object

    Returns:
        gene (Feature) records
    """
    return _get_oncokb_gene_list(conn, TUMOUR_SUPPRESSIVE)


def get_therapeutic_associated_genes(graphkb_conn: GraphKBConnection) -> List[Ontology]:
    """Genes related to a cancer-associated statement in Graphkb."""
    therapeutic_relevance = get_terms_set(graphkb_conn, BASE_THERAPEUTIC_TERMS)
    statements = graphkb_conn.query(
        {
            "target": "Statement",
            "filters": {"relevance": sorted(list(therapeutic_relevance))},
            "returnProperties": ["reviewStatus"]
            + [f"conditions.{prop}" for prop in GENE_RETURN_PROPERTIES]
            + [
                f"conditions.reference{ref}.{prop}"
                for prop in GENE_RETURN_PROPERTIES
                for ref in ("1", "2")
            ],
        }
    )
    genes: List[Ontology] = []
    for statement in statements:
        if statement["reviewStatus"] == "failed":
            continue
        for condition in statement["conditions"]:
            if condition["@class"] == "Feature":
                genes.append(condition)
            elif condition["@class"].endswith("Variant"):
                cond = cast(Variant, condition)
                if cond["reference1"] and cond["reference1"]["@class"] == "Feature":
                    genes.append(cond["reference1"])
                if cond["reference2"] and cond["reference2"]["@class"] == "Feature":
                    genes.append(cond["reference2"])
    unique_genes: List[Ontology] = []
    for gene in genes:
        if not gene.get("deprecated", False):
            if gene["@rid"] not in [g["@rid"] for g in unique_genes]:
                unique_genes.append(gene)
    return unique_genes


def get_genes_from_variant_types(
    conn: GraphKBConnection,
    types: List[str],
    source_record_ids: List[str] = [],
    ignore_cache: bool = False,
) -> List[Ontology]:
    """Retrieve a list of Genes which are found in variants on the given types.

    Args:
        conn: the graphkb connection object
        types: list of names of variant types
        source_record_ids: list of sources ids to filter genes by

    Returns:
        List.<dict>: gene (Feature) records
    """
    filters: List[Dict[str, Any]] = []
    if types:
        filters.append(
            {"type": {"target": "Vocabulary", "filters": {"name": types, "operator": "IN"}}}
        )

    variants = cast(
        List[Variant],
        conn.query(
            {
                "target": "Variant",
                "filters": filters,
                "returnProperties": ["reference1", "reference2"],
            },
            ignore_cache=ignore_cache,
        ),
    )

    genes = set()
    for variant in variants:
        genes.add(variant["reference1"])
        if variant["reference2"]:
            genes.add(variant["reference2"])
    if not genes:
        return []

    filters: List[Dict[str, Any]] = [{"biotype": "gene"}]
    if source_record_ids:
        filters.append({"source": source_record_ids, "operator": "IN"})

    result = cast(
        List[Ontology],
        conn.query(
            {"target": list(genes), "returnProperties": GENE_RETURN_PROPERTIES, "filters": filters},
            ignore_cache=ignore_cache,
        ),
    )
    return result


def get_preferred_gene_name(
    conn: GraphKBConnection, gene_name: str, source: str = PREFERRED_GENE_SOURCE
) -> str:
    """Preferred gene symbol of a gene or transcript.

    Args:
        gene_name: the gene name to search features by
        ignore_cache (bool, optional): bypass the cache to always force a new request
        source: id of the preferred gene symbol source
    Returns:
        preferred displayName symbol.

    Example:
        return KRAS for get_preferred_gene_name(conn, 'NM_033360')
        return KRAS for get_preferred_gene_name(conn, 'ENSG00000133703.11')
    """
    if gene_name in CHROMOSOMES:
        logger.error(f"{gene_name} assumed to be a chromosome, not gene")
        return ""
    eq = get_equivalent_features(conn=conn, gene_name=gene_name)
    genes = [m for m in eq if m.get("biotype") == "gene" and not m.get("deprecated")]
    if not genes:
        logger.error(f"No genes found for: {gene_name}")
        return ""
    if source:
        source_filtered_genes = [m for m in genes if m.get("source") == source]
        if not source_filtered_genes:
            logger.error(f"No data from source {source} for {gene_name}")
        else:
            genes = source_filtered_genes

    gene_names = [g["displayName"] for g in genes if g]
    if len(gene_names) > 1:
        logger.error(
            f"Multiple gene names found for: {gene_name} - using {gene_names[0]}, ignoring {gene_names[1:]}"
        )
    return gene_names[0]


def get_cancer_predisposition_info(conn: GraphKBConnection) -> Tuple[List[str], Dict[str, str]]:
    """
    Return two lists from GraphKB, one of cancer predisposition genes and one of associated variants.

    GERO-272 - criteria for what counts as a "cancer predisposition" variant

    In short:
    * Statement 'source' is 'CGL'
    * Statement 'relevance' is 'pathogenic'
    * gene is gotten from any associated 'PositionalVariant' records

    Example: https://graphkb.bcgsc.ca/view/Statement/155:11616

    Returns:
        genes: list of cancer predisposition genes
        variants: dictionary mapping pharmacogenomic variant IDs to variant display names
    """
    genes = set()
    non_genes = set()
    infer_genes = set()
    variants = {}

    terms: dict = {term: lst for term, lst in RELEVANCE_BASE_TERMS}
    relevance_rids = list(get_terms_set(conn, terms.get("cancer predisposition", [])))

    for record in conn.query(
        {
            "target": "Statement",
            "filters": {
                "AND": [
                    {
                        "evidence": {
                            "target": "Source",
                            "filters": {"@rid": get_rid(conn, "Source", "CGL")},
                        },
                    },
                    {
                        "relevance": {"target": "Vocabulary", "filters": {"@rid": relevance_rids}},
                    },
                ],
            },
            "returnProperties": [
                "conditions.@class",
                "conditions.@rid",
                "conditions.displayName",
                "conditions.reference1.biotype",
                "conditions.reference1.displayName",
                "conditions.reference2.biotype",
                "conditions.reference2.displayName",
            ],
        },
        ignore_cache=False,
    ):
        for condition in record["conditions"]:  # type: ignore
            if condition["@class"] == "PositionalVariant":
                variants[condition["@rid"]] = condition["displayName"]
                for reference in ["reference1", "reference2"]:
                    name = (condition.get(reference) or {}).get("displayName", "")
                    biotype = (condition.get(reference) or {}).get("biotype", "")
                    if name and biotype == "gene":
                        genes.add(name)
                    elif name:
                        gene = get_preferred_gene_name(conn, name)
                        if gene:
                            infer_genes.add((gene, name, biotype))
                        else:
                            non_genes.add((name, biotype))
                            logger.error(
                                f"Non-gene cancer predisposition {biotype}: {name} for {condition['displayName']}"
                            )

    for gene, name, biotype in infer_genes:
        logger.debug(f"Found gene '{gene}' for '{name}' ({biotype})")
        genes.add(gene)

    for name, biotype in non_genes:
        logger.error(f"Unable to find gene for '{name}' ({biotype})")

    return sorted(genes), variants


def get_pharmacogenomic_info(conn: GraphKBConnection) -> Tuple[List[str], Dict[str, str]]:
    """
    Return two lists from GraphKB, one of pharmacogenomic genes and one of associated variants.

    SDEV-2733 - criteria for what counts as a "pharmacogenomic" variant

    In short:
    * Statement 'source' is not 'CGI' or 'CIViC'
    * Statement 'relevance' is 'increased toxicity' or 'decreased toxicity'
    * gene is gotten from any associated 'PositionalVariant' records

    Example: https://graphkb.bcgsc.ca/view/Statement/154:9574

    Returns:
        genes: list of pharmacogenomic genes
        variants: dictionary mapping pharmacogenomic variant IDs to variant display names
    """
    genes = set()
    non_genes = set()
    infer_genes = set()
    variants = {}

    relevance_rids = list(get_terms_set(conn, "pharmacogenomic"))

    for record in conn.query(
        {
            "target": "Statement",
            "filters": [
                {"relevance": {"target": "Vocabulary", "filters": {"@rid": relevance_rids}}}
            ],
            "returnProperties": [
                "conditions.@class",
                "conditions.@rid",
                "conditions.displayName",
                "conditions.reference1.biotype",
                "conditions.reference1.displayName",
                "conditions.reference2.biotype",
                "conditions.reference2.displayName",
                "source.name",
            ],
        },
        ignore_cache=False,
    ):
        if record["source"]:  # type: ignore
            if record["source"]["name"].lower() in PHARMACOGENOMIC_SOURCE_EXCLUDE_LIST:  # type: ignore
                continue

        for condition in record["conditions"]:  # type: ignore
            if condition["@class"] == "PositionalVariant":
                variants[condition["@rid"]] = condition["displayName"]
                for reference in ["reference1", "reference2"]:
                    name = (condition.get(reference) or {}).get("displayName", "")
                    biotype = (condition.get(reference) or {}).get("biotype", "")
                    if name and biotype == "gene":
                        genes.add(name)
                    elif name:
                        gene = get_preferred_gene_name(conn, name)
                        if gene:
                            infer_genes.add((gene, name, biotype))
                        else:
                            non_genes.add((name, biotype))
                            logger.error(
                                f"Non-gene pharmacogenomic {biotype}: {name} for {condition['displayName']}"
                            )

    for gene, name, biotype in infer_genes:
        logger.debug(f"Found gene '{gene}' for '{name}' ({biotype})")
        genes.add(gene)

    for name, biotype in non_genes:
        logger.error(f"Unable to find gene for '{name}' ({biotype})")

    return sorted(genes), variants


def convert_to_rid_set(records: Sequence[Dict]) -> Set[str]:
    return {r["@rid"] for r in records}


def get_gene_information(
    graphkb_conn: GraphKBConnection, gene_names: Sequence[str]
) -> List[Dict[str, bool]]:
    """Create a list of gene_info flag dicts for IPR report upload.

    Function is originally from pori_ipr_python::annotate.py

    Gene flags (categories) are: ['cancerRelated', 'knownFusionPartner', 'knownSmallMutation',
                                  'oncogene', 'therapeuticAssociated', 'tumourSuppressor']

    Args:
        graphkb_conn ([type]): [description]
        gene_names ([type]): [description]
    Returns:
        List of gene_info dicts of form [{'name':<gene_str>, <flag>: True}]
        Keys of False values are simply omitted from ipr upload to reduce info transfer.
            eg. [{'cancerRelated': True,
                  'knownFusionPartner': True,
                  'knownSmallMutation': True,
                  'name': 'TERT',
                  'oncogene': True}]
    """
    logger.info("fetching variant related genes list")
    # For query speed, only fetch the minimum needed details
    ret_props = [
        "conditions.@rid",
        "conditions.@class",
        "conditions.reference1",
        "conditions.reference2",
        "reviewStatus",
    ]
    body: Dict[str, Any] = {"target": "Statement", "returnProperties": ret_props}

    gene_names = sorted(set(gene_names))
    statements = graphkb_conn.query(body)
    statements = [s for s in statements if s.get("reviewStatus") != FAILED_REVIEW_STATUS]

    gene_flags: Dict[str, Set[str]] = {
        "cancerRelated": set(),
        "knownFusionPartner": set(),
        "knownSmallMutation": set(),
    }

    for statement in statements:
        for condition in statement["conditions"]:
            if not condition.get("reference1"):
                continue
            gene_flags["cancerRelated"].add(condition["reference1"])
            if condition["reference2"]:
                gene_flags["cancerRelated"].add(condition["reference2"])
                gene_flags["knownFusionPartner"].add(condition["reference1"])
                gene_flags["knownFusionPartner"].add(condition["reference2"])
            elif condition["@class"] == "PositionalVariant":
                gene_flags["knownSmallMutation"].add(condition["reference1"])

    logger.info("fetching oncogenes list")
    gene_flags["oncogene"] = convert_to_rid_set(get_oncokb_oncogenes(graphkb_conn))
    logger.info("fetching tumour supressors list")
    gene_flags["tumourSuppressor"] = convert_to_rid_set(get_oncokb_tumour_supressors(graphkb_conn))

    logger.info("fetching therapeutic associated genes lists")
    gene_flags["therapeuticAssociated"] = convert_to_rid_set(
        get_therapeutic_associated_genes(graphkb_conn)
    )

    logger.info(f"Setting gene_info flags on {len(gene_names)} genes")
    result = []
    for gene_name in gene_names:
        equivalent = convert_to_rid_set(get_equivalent_features(graphkb_conn, gene_name))
        row = {"name": gene_name}
        flagged = False
        for flag in gene_flags:
            # make smaller JSON to upload since all default to false already
            if equivalent.intersection(gene_flags[flag]):
                row[flag] = flagged = True
        if flagged:
            result.append(row)

    return result
