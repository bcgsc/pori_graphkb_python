"""
Functions which return Variants from GraphKB which match some input variant definition
"""
from typing import Dict, Iterable, List, Optional, Set, Union, cast

from . import GraphKBConnection
from .constants import (
    AMBIGUOUS_AA,
    INPUT_COPY_CATEGORIES,
    INPUT_EXPRESSION_CATEGORIES,
    POS_VARIANT_RETURN_PROPERTIES,
    STRUCTURAL_VARIANT_ALIASES,
    STRUCTURAL_VARIANT_SIZE_THRESHOLD,
    STRUCTURAL_VARIANT_TYPES,
    VARIANT_RETURN_PROPERTIES,
)
from .types import (
    BasicPosition,
    Ontology,
    ParsedVariant,
    PositionalVariant,
    Record,
    Variant,
)
from .util import (
    FeatureNotFoundError,
    convert_to_rid_list,
    logger,
    looks_like_rid,
    stringifyVariant,
)
from .vocab import get_equivalent_terms, get_term_tree, get_terms_set

FEATURES_CACHE: Set[str] = set()


def get_equivalent_features(
    conn: GraphKBConnection,
    gene_name: str,
    ignore_cache: bool = False,
    is_source_id: bool = False,
    source: str = "",
    source_id_version: str = "",
) -> List[Ontology]:
    """Match an equivalent list of features given some input feature name (or ID).

    Args:
        gene_name: the gene name to search features by
        ignore_cache (bool, optional): bypass the cache to always force a new request
        is_source_id: treat the gene_name as the gene ID from the source database (ex. ENSG001)
        source_id_version: the version of the source_id
        source: the name of the source database the gene definition is from (ex. ensembl)
    Returns:
        equivalent feature records

    Example:
        get_equivalent_features(conn, 'KRAS')

    Example:
        get_equivalent_features(conn, 'ENSG001', source='ensembl', is_source_id=True)

    Example:
        get_equivalent_features(conn, 'ENSG001', source='ensembl', source_id_version='1')

    Example:
        get_equivalent_features(conn, '#3:44')
    """
    if looks_like_rid(gene_name):
        return cast(
            List[Ontology],
            conn.query(
                {"target": [gene_name], "queryType": "similarTo"},
                ignore_cache=ignore_cache,
            ),
        )

    filters: List[Dict] = []
    if source:
        filters.append({"source": {"target": "Source", "filters": {"name": source}}})

    if gene_name.count(".") == 1 and gene_name.split(".")[-1].isnumeric():
        # eg. ENSG00000133703.11 or NM_033360.4
        logger.debug(
            f"Assuming {gene_name} has a .version_format - ignoring the version for equivalent features"
        )
        gene_name = gene_name.split(".")[0]

    if is_source_id or source_id_version:
        filters.append({"sourceId": gene_name})
        if source_id_version:
            filters.append(
                {
                    "OR": [
                        {"sourceIdVersion": source_id_version},
                        {"sourceIdVersion": None},
                    ]
                }
            )
    elif FEATURES_CACHE and gene_name.lower() not in FEATURES_CACHE and not ignore_cache:
        return []
    else:
        filters.append({"OR": [{"sourceId": gene_name}, {"name": gene_name}]})

    return cast(
        List[Ontology],
        conn.query(
            {
                "target": {"target": "Feature", "filters": filters},
                "queryType": "similarTo",
            },
            ignore_cache=ignore_cache,
        ),
    )


def cache_missing_features(conn: GraphKBConnection) -> None:
    """
    Create a cache of features that exist to avoid repeatedly querying
    for missing features
    """
    genes = cast(
        List[Ontology],
        conn.query(
            {
                "target": "Feature",
                "returnProperties": ["name", "sourceId"],
                "neighbors": 0,
            }
        ),
    )
    for gene in genes:
        if gene["name"]:
            FEATURES_CACHE.add(gene["name"].lower())
        if gene["sourceId"]:
            FEATURES_CACHE.add(gene["sourceId"].lower())


def match_category_variant(
    conn: GraphKBConnection,
    gene_name: str,
    category: str,
    root_exclude_term: str = "",
    gene_source: str = "",
    gene_is_source_id: bool = False,
    ignore_cache: bool = False,
) -> List[Variant]:
    """
    Returns a list of variants matching the input variant

    Args:
        conn (GraphKBConnection): the graphkb connection object
        gene_name (str): the name of the gene the variant is in reference to
        category (str): the variant category (ex. copy loss)
        gene_source: The source database the gene is defined by (ex. ensembl)
        gene_is_source_id: Indicates the gene name(s) input should be treated as sourceIds not names
    Raises:
        FeatureNotFoundError: The gene could not be found in GraphKB

    Returns:
        Array.<dict>: List of variant records from GraphKB which match the input
    """
    # disambiguate the gene to find all equivalent representations
    features = convert_to_rid_list(
        get_equivalent_features(
            conn,
            gene_name,
            source=gene_source,
            is_source_id=gene_is_source_id,
            ignore_cache=ignore_cache,
        )
    )

    if not features:
        raise FeatureNotFoundError(
            f"unable to find the gene ({gene_name}) or any equivalent representations"
        )

    # get the list of terms that we should match
    terms = convert_to_rid_list(
        get_term_tree(conn, category, root_exclude_term, ignore_cache=ignore_cache)
    )

    if not terms:
        raise ValueError(f"unable to find the term/category ({category}) or any equivalent")

    # find the variant list
    return cast(
        List[Variant],
        conn.query(
            {
                "target": {
                    "target": "CategoryVariant",
                    "filters": [
                        {"reference1": features, "operator": "IN"},
                        {"type": terms, "operator": "IN"},
                    ],
                },
                "queryType": "similarTo",
                "edges": [
                    "AliasOf",
                    "DeprecatedBy",
                    "CrossReferenceOf",
                    "GeneralizationOf",
                ],
                "treeEdges": ["Infers"],
                "returnProperties": VARIANT_RETURN_PROPERTIES,
            },
            ignore_cache=ignore_cache,
        ),
    )


def match_copy_variant(
    conn: GraphKBConnection,
    gene_name: str,
    category: str,
    drop_homozygous: bool = False,
    **kwargs,
) -> List[Variant]:
    """
    Returns a list of variants matching the input variant

    Args:
        conn (GraphKBConnection): the graphkb connection object
        gene_name (str): the name of the gene the variant is in reference to
        category (str): the variant category (ex. copy loss)
        drop_homozygous (bool): Drop homozygous matches from the result when true

    Raises:
        ValueError: The input copy category is not recognized

    Returns:
        List of variant records from GraphKB which match the input
    """
    if category not in INPUT_COPY_CATEGORIES.values():
        raise ValueError(f"not a valid copy variant input category ({category})")

    result = match_category_variant(
        conn, gene_name, category, root_exclude_term="structural variant", **kwargs
    )

    if drop_homozygous:
        return [row for row in result if row["zygosity"] != "homozygous"]
    return result


def match_expression_variant(
    conn: GraphKBConnection, gene_name: str, category: str, **kwargs
) -> List[Variant]:
    if category not in INPUT_EXPRESSION_CATEGORIES.values():
        raise ValueError(f"not a valid expression variant input category ({category})")

    return match_category_variant(
        conn, gene_name, category, root_exclude_term="biological", **kwargs
    )


def positions_overlap(
    pos_record: BasicPosition,
    range_start: BasicPosition,
    range_end: Optional[BasicPosition] = None,
) -> bool:
    """
    Check if 2 Position records from GraphKB indicate an overlap

    Note:
        null values indicate not-specified or any

    Args:
        pos_record (dict): the record to compare
        range_start (dict): the position record indicating the start of an uncertainty range
        range_end (dict, optional): the position record indicating the end of an uncertainty range

    Raises:
        NotImplementedError: if a cytoband type position is given

    Returns:
        bool: True if the positions overlap
    """
    if pos_record.get("@class", "") == "CytobandPosition":
        raise NotImplementedError(
            "Position comparison for cytoband coordinates is not yet implemented"
        )

    pos = pos_record.get("pos", None)
    if pos is None:
        return True

    start = range_start.get("pos", None)

    if range_end:
        end = range_end.get("pos", None)

        if start is not None and pos < start:
            return False
        if end is not None and pos > end:
            return False
        return True
    return start is None or pos == start


def compare_positional_variants(
    reference_variant: Union[PositionalVariant, ParsedVariant],
    variant: Union[PositionalVariant, ParsedVariant],
    generic: bool = True,
) -> bool:
    """
    Compare 2 positional variant records from GraphKB to determine if they are equivalent

    Args:
        reference_variant: record used as a reference to be match to
        variant: record we are testing for a match to the reference
        generic (bool, optional): also include the more generic variants

    Returns:
        bool: True if the records are equivalent
    """

    # If specific vs more-generic variants are not to be considered as equivalent,
    # check if their stringify representation match and return True or False right away.
    if not generic:
        # Reference(s) will not be included in the string repr. since the variant has been
        # pre-filtered to match any equivalent features.
        # Templated sequences will also not be included in the string repr. since
        # it's unnecessary and not always available.
        reference_variant_str: str = stringifyVariant(
            reference_variant,
            withRef=False,
            withRefSeq=False,
        )
        variant_str: str = stringifyVariant(
            variant,
            withRef=False,
            withRefSeq=False,
        )
        return reference_variant_str == variant_str

    # For break1, check if positions are overlaping between the variant and the reference.
    # Continue only if True.
    if not positions_overlap(
        cast(BasicPosition, reference_variant["break1Start"]),
        cast(BasicPosition, variant["break1Start"]),
        None if "break1End" not in variant else cast(BasicPosition, variant["break1End"]),
    ):
        return False

    # For break2, check if positions are overlaping between the variant and the reference.
    # Continue only if True or no break2.
    if reference_variant.get("break2Start"):
        if not variant.get("break2Start"):
            return False
        if not positions_overlap(
            cast(BasicPosition, reference_variant["break2Start"]),
            cast(BasicPosition, variant["break2Start"]),
            None if "break2End" not in variant else cast(BasicPosition, variant["break2End"]),
        ):
            return False

    # If both variants have untemplated sequence,
    # check for size and content.
    if (
        reference_variant.get("untemplatedSeq", None) is not None
        and variant.get("untemplatedSeq", None) is not None
    ):
        if (
            reference_variant.get("untemplatedSeqSize", None) is not None
            and variant.get("untemplatedSeqSize", None) is not None
        ):
            if reference_variant["untemplatedSeqSize"] != variant["untemplatedSeqSize"]:
                return False

        if (
            variant["untemplatedSeq"] is not None
            and reference_variant["untemplatedSeq"] is not None
        ):
            if (
                variant["untemplatedSeq"] not in AMBIGUOUS_AA
                and reference_variant["untemplatedSeq"] not in AMBIGUOUS_AA
            ):
                if variant["untemplatedSeq"].lower() != reference_variant["untemplatedSeq"].lower():
                    return False
            elif len(reference_variant["untemplatedSeq"]) != len(variant["untemplatedSeq"]):
                return False

    # If both variants have a reference sequence,
    # check if they are the same.
    if (
        reference_variant.get("refSeq", None) is not None
        and variant.get("refSeq", None) is not None
    ):
        if (
            variant["refSeq"] not in AMBIGUOUS_AA
            and reference_variant["refSeq"] not in AMBIGUOUS_AA
        ):
            if variant["refSeq"].lower() != reference_variant["refSeq"].lower():  # type: ignore
                return False
        elif len(reference_variant["refSeq"]) != len(variant["refSeq"]):  # type: ignore
            return False

    return True


def structural_type_screening(
    conn: GraphKBConnection,
    parsed: ParsedVariant,
    updateStructuralTypes=False,
) -> bool:
    """
    [KBDEV-1056]; updated in [KBDEV-1133]
    Given a parsed variant notation, returns a boolean for whether or not a variant is structural

    Args:
        conn (GraphKBConnection): the graphkb connection object
        parsed (ParsedVariant): the variant notation parsed as a dictionary by the API
        updateStructuralTypes (boolean): if True the API is queried for an updated list
                                         of terms, otherwise an hard-coded list is used

    Returns:
        True | False

    Example:
        # ambiguous structural type; False IF length < threshold (50)
        structural_type_screening(conn, {
                'type': 'deletion',
                'break1Start': {'pos': 1},
                'break2Start': {'pos': 5},
            }) -> False

    Example:
        # ambiguous structural type; True IF length >= threshold (50)
        structural_type_screening(conn, {
                'type': 'deletion',
                'break1Start': {'pos': 1},
                'break2Start': {'pos': 50},
            }) -> True

    Example:
        # unambiguous structural type
        structural_type_screening(conn, {'type': 'fusion'}) -> True

    Example:
        # unambiguous non-structural type
        structural_type_screening(conn, {'type': 'substitution'}) -> False
    """
    structuralVariantTypes = STRUCTURAL_VARIANT_TYPES
    threshold = STRUCTURAL_VARIANT_SIZE_THRESHOLD

    # Will use either hardcoded type list or an updated list from the API
    if updateStructuralTypes:
        rids = list(get_terms_set(conn, ["structural variant"]))
        records = conn.get_records_by_id(rids)
        structuralVariantTypes = [el["name"] for el in records]

    # Unambiguous non-structural variation type
    if parsed["type"] not in structuralVariantTypes:
        return False

    # Unambiguous structural variation type
    if parsed["type"] in ["fusion", "translocation"]:
        return True
    if parsed.get("reference2", None):
        return True
    prefix = parsed.get("prefix", "g")
    if prefix == "y":  # Assuming all variations using cytoband coordiantes meet the size threshold
        return True

    # When size cannot be determined: exonic and intronic coordinates
    # e.g. "MET:e.14del" meaning "Any deletion occuring at the 14th exon"
    if prefix in ["e", "i"]:  # Assuming they don't meet the size threshold
        return False

    # When size is given
    if parsed.get("untemplatedSeqSize", 0) >= threshold:
        return True

    # When size needs to be computed from positions
    pos_start = parsed.get("break1Start", {}).get("pos", 1)
    pos_end = parsed.get("break2Start", {}).get("pos", pos_start)
    pos_size = 1
    if prefix == "p":
        pos_size = 3
    if ((pos_end - pos_start) + 1) * pos_size >= threshold:
        return True

    # Default
    return False


def structural_type_adjustment(
    conn: GraphKBConnection,
    parsed: ParsedVariant,
    variant_types_details: List[Ontology],
    updateTypeList: Optional[bool] = False,
) -> List[Ontology]:
    """
    Given a variant and a list of Vocabuilary records (variant's types), the variant get
    screened for meeting structural criterias. If not a structural variant, then we
    remove potential structural variant terms/aliases from the list before returning it.

    Args:
        conn (GraphKBConnection): the graphkb connection object
        parsed (ParsedVariant): variant parsed as a dictionary
        variant_types_details (Iterable[Record]): List of Vocabulary records as variant's type
        updateTypeList (bool): Whether or not getting an up-to-date type list with an
                               API call, or use the hard-coded one

    Returns:
        A filtered Vocabuilary records list

    Note:
        If a structural variant, the list is returned as-is, without removing
        small variant terms/aliases since since we still want to match them.
    """
    # Screening type for discrepancies regarding structural variants
    if not structural_type_screening(conn, parsed, updateTypeList):
        # get structural type aliases
        structural_types = (
            map(
                lambda x: x["name"],
                get_equivalent_terms(conn, "structural variant"),
            )
            if updateTypeList
            else STRUCTURAL_VARIANT_ALIASES
        )
        # filters out potential structural type aliases
        return list(
            filter(
                lambda x: False if x["name"] in structural_types else True,
                variant_types_details,
            )
        )
    return variant_types_details


def category_variant_similarTo(
    conn: GraphKBConnection,
    features: List[str],
    variant_types_details: Iterable[Record],
    secondary_features: Optional[List[str]] = None,
    ignore_cache: Optional[bool] = False,
) -> List[Variant]:
    """
    Given some filters options (types and references), returns a list of matching
    category variants.

    Args:
        conn (GraphKBConnection): the graphkb connection object
        features (List[str]): List of RIDs to filters reference1 for
        variant_types_details (Iterable[Record]): List of Vocabulary records as variant's type
        ignore_cache (bool): Whether or not the connection object cache should be ignore
                             when querying the graphkb API
        secondary_features (List[str]): List of RIDs to filters reference2 for

    Returns:
        A list of Variant records matching the filters options

    Note:
        Since CategoryVariants aren't linked together with similarity "edges" (AliasOf, etc.),
        a "similarTo" queryType is not required.
          
        Also, on a "similarTo" queryType, a query with "treeEdges" = ["Infers"] could be
        detrimental since some PositionalVariants infers CategoryVariants (a PositionalVariant
        could be matched to an incompatible PositionalVariant through Infers edges to a common
        CategoryVariant).
        e.g. (BCR,ABL1):fusion(r.2030,r.461) --Infers--> BCR and ABL1 fusion
             (BCR,ABL1):fusion(r.3458,r.635) --Infers--> BCR and ABL1 fusion
    """
    return conn.query(
        {
            "target": "CategoryVariant",
            "filters": {
                "AND": [
                    {"reference1": features},
                    {"type": convert_to_rid_list(variant_types_details)},
                    {"reference2": secondary_features},
                ]
            },
        },
        ignore_cache=ignore_cache,
    )


def match_positional_variant(
    conn: GraphKBConnection,
    variant_string: str,
    reference1: Optional[str] = None,
    reference2: Optional[str] = None,
    gene_is_source_id: bool = False,
    gene_source: str = "",
    ignore_cache: bool = False,
    updateTypeList: bool = False,
    delinsSpecialHandling: bool = True,
) -> List[Variant]:
    """
    Given the HGVS+ representation of some positional variant, parse it and match it to
    annotations in GraphKB

    Args:
        conn (GraphKBConnection): the graphkb connection object
        variant_string (str): the HGVS+ annotation string
        reference1 (str): Explicitly specify the first reference link record (gene1)
        reference2 (str): Explicitly specify the second reference link record (gene2)
        gene_is_source_id (bool): Indicates the gene name(s) input should be treated
                                  as sourceIds not names
        gene_source (str): The source database the gene is defined by (ex. ensembl)
        ignore_cache (bool): Whether or not the connection object cache should be ignore
                             when querying the graphkb API
        updateTypeList (bool): Whether or not getting an up-to-date type list with an
                               API call, or use the hard-coded one
        delinsSpecialHandling (bool): Whether or not delins will be treated appart to be
                                      also matched to more specific deletion and insertion

    Raises:
        NotImplementedError: thrown for uncertain position input (ranges)
        FeatureNotFoundError: One of the genes does not exist in GraphKB
        ValueError: the gene names were given both in the variant_string and explicitly

    Returns:
        A list of matched statement records

    Example:
        match_positional_variant(conn, '(EWSR1,FLI1):fusion(e.1,e.2)')

    Example:
        match_positional_variant(conn, 'fusion(e.1,e.2)', 'EWSR1', 'FLI1')

    Example:
        match_positional_variant(conn, 'fusion(e.1,e.2)', '#3:4', '#4:5')

    Example:
        match_positional_variant(conn, 'fusion(e.1,e.2)', '123', '456', gene_is_source_id=True, gene_source='entrez gene')

    Example:
        match_positional_variant(conn, 'KRAS:p.G12D')

    Example:
        match_positional_variant(conn, 'p.G12D', 'KRAS')
    """
    # 1. ORIGINAL VARIANT
    ###########################################################################

    # A) PARSING
    # Parsing the variant representation using the GraphKB Parser
    parsed = conn.parse(variant_string, not (reference1 or reference2))

    if "break1End" in parsed or "break2End" in parsed:  # uncertain position
        raise NotImplementedError(
            f"Matching does not support uncertain positions ({variant_string}) as input"
        )
    if reference2 and not reference1:
        raise ValueError("cannot specify reference2 without reference1")

    # B) FEATURES
    # PRIMARY FEATURES
    if reference1:
        gene1 = reference1
        if "reference1" in parsed:
            raise ValueError(
                "Cannot specify reference1 explicitly as well as in the variant notation"
            )
    else:
        gene1 = parsed["reference1"]

    # Get equivalent features
    gene1_features = get_equivalent_features(
        conn,
        gene1,
        source=gene_source,
        is_source_id=gene_is_source_id,
        ignore_cache=ignore_cache,
    )
    features = convert_to_rid_list(gene1_features)

    if not features:
        raise FeatureNotFoundError(
            f"unable to find the gene ({gene1}) or any equivalent representations"
        )

    # SECONDARY FEATURES
    secondary_features = None

    gene2: Optional[str] = None
    if reference2:
        gene2 = reference2
        if "reference2" in parsed:
            raise ValueError(
                "Cannot specify reference2 explicitly as well as in the variant notation"
            )
        elif "reference1" in parsed:
            raise ValueError(
                "variant notation cannot contain features when explicit features are given"
            )
    elif (
        "reference2" in parsed
        and parsed.get("reference2", "?") != "?"
        and parsed["reference2"] is not None
    ):
        gene2 = parsed["reference2"]

    if gene2:
        # Get equivalent features
        gene2_features = get_equivalent_features(
            conn,
            gene2,
            source=gene_source,
            is_source_id=gene_is_source_id,
            ignore_cache=ignore_cache,
        )
        secondary_features = convert_to_rid_list(gene2_features)
        if not secondary_features:
            raise FeatureNotFoundError(
                f"unable to find the gene ({gene2}) or any equivalent representations"
            )

    # C) TYPES
    # Get equivalent (i.e. same or more generic) variant types
    variant_types_details = get_equivalent_terms(
        conn,
        parsed["type"],
        # root_exclude_term="mutation" if secondary_features else "",
        ignore_cache=ignore_cache,
    )

    # Adjustment for structural variants [KBDEV-1056]
    variant_types_details = structural_type_adjustment(
        conn,
        parsed,
        variant_types_details,
        updateTypeList,
    )

    # Delins (indel) handling [KBDEV-1133]
    # Matching delins to also the more specific terms (i.e. deletion, insertion, ...)
    if parsed["type"] == "indel" and delinsSpecialHandling:
        variant_types_details.extend(
            filter(
                lambda x: False if x["name"] == "indel" else True,  # remove duplicated term
                get_term_tree(
                    conn,
                    "indel",
                    include_superclasses=False,  # term and chlidren terms only
                ),
            )
        )


    # 2. MATCHING
    ###########################################################################

    matches: List[Record] = []


    # 2.1 
    ###########################################################################

    # D) SELECTING ALL MATCHING POSITIONAL VARIANTS, REGARDLESS OF POSITIONS
    # Matching based on features, coord. sys. and types only.
    # Note: The coordinate systems (genomic, cds, protein, etc.) need to be same
    # for the parsed variant and any other positional variants to match.
    # Variants from diff. coord. sys. can be linked in the database with Infers edges.
    all_pv_matches = cast(
        List[Record],
        conn.query(
            {
                "target": "PositionalVariant",
                "filters": [
                    {"reference1": features},
                    {"reference2": secondary_features},
                    {"break1Start.@class": parsed["break1Start"]["@class"]},
                    {"type": convert_to_rid_list(variant_types_details)},
                ]
            },
            ignore_cache=ignore_cache,
        ),
    )
    
    # E) FILTERING OUT MISMATCHED POSITIONS
    # Populate two seperated lists:
    # - 1st list (similar + more generic matches): a first one for ...
    # - 2nd list (similar matches only): one for ...
    filtered_similarAndGeneric: List[Record] = []
    filtered_similarOnly: List[Record] = []
    
    for record in all_pv_matches:
        if compare_positional_variants(
            reference_variant=parsed,
            variant=cast(PositionalVariant, record),
            generic=True,
        ):
            filtered_similarAndGeneric.append(record)
            if compare_positional_variants(
                reference_variant=parsed,
                variant=cast(PositionalVariant, record),
                generic=False,  # Similar variants only
            ):
                filtered_similarOnly.append(record)


    # 2.2 EXPANDING MATCHES WITH VARIANTS LINKED TO FILTERED POSITIONAL VARIANTS
    ###########################################################################

    # F) FOLLOWING EDGES ON THE VARIANT TREE
    # Starting with similar matches only, and expanding to linked PositionalVariant
    # e.g. NRAS:p.Q61K  <--Infers-- chr1:g.115256530G>T
    if filtered_similarOnly:
        pv_similarOnly_matches = conn.query(
            {
                "target": convert_to_rid_list(filtered_similarOnly),
                "queryType": "similarTo",
                "edges": [
                    "AliasOf",
                    "DeprecatedBy",
                    "CrossReferenceOf",
                    "GeneralizationOf",
                ],
                "treeEdges": ["Infers"],
                "returnProperties": POS_VARIANT_RETURN_PROPERTIES,
            },
            ignore_cache=ignore_cache,
        )
        # Extending matches with newly matched variants
        matches.extend(pv_similarOnly_matches)
        # TODO: Extending types with ones from newly matched variants


    # 2.3 EXPANDING MATCHES WITH VARIANTS LINKED TO CATEGORY VARIANTS
    ###########################################################################
    # note: There is no edges in-between CategoryVariants,
    #       only incomming Infers edges from a handfull of PositionalVariant

    # G) MATCHING ON BOTH REFERENCES
    # (whether or not there is secondary features)
    # e.g. "BRAF:c...del" MATCHING "BRAF deletion"
    # e.g. "(BRAF,AKAP9):fusion(...)" MATCHING "BRAF and AKAP9 fusion"
    matches.extend(
        category_variant_similarTo(
            conn,
            features,
            variant_types_details,
            secondary_features,
            ignore_cache,
        )
    )

    # H) MATCHING ON EVERY COMBINATION OF REFERENCES
    if secondary_features:
        # a) matching on inverted reference1 and reference2
        # e.g. "(BRAF,AKAP9):fusion(...)" MATCHING "AKAP9 and BRAF fusion"
        matches.extend(
            category_variant_similarTo(
                conn,
                features = secondary_features,
                variant_types_details = variant_types_details,
                secondary_features = features,
                ignore_cache = ignore_cache,
            )
        )
        # b) matching on reference1 = primary features, without reference2
        # e.g. "(BRAF,AKAP9):fusion(...)" MATCHING "BRAF fusion"
        matches.extend(
            category_variant_similarTo(
                conn,
                features,
                variant_types_details,
                secondary_features = None,
                ignore_cache = ignore_cache,
            )
        )
        # c) matching on reference1 = secondary features, without reference2
        # e.g. "(BRAF,AKAP9):fusion(...)" MATCHING "AKAP9 fusion"
        matches.extend(
            category_variant_similarTo(
                conn,
                features = secondary_features,
                variant_types_details = variant_types_details,
                secondary_features = None,
                ignore_cache = ignore_cache,
            )
        )


    # 2.3 EXPANDING MATCHES WITH LINKED CATEGORY VARIANTS
    ###########################################################################

    # I) FOLLOWING EDGES ON THE VARIANT TREE, FROM MATCHING SIMILAR & GENERIC PVs

    if filtered_similarAndGeneric:
        pv_similarAndGeneric_matches = conn.query(
            {
                "target": convert_to_rid_list(filtered_similarAndGeneric),
                "queryType": "descendants",
                "edges": [],
                "returnProperties": POS_VARIANT_RETURN_PROPERTIES,
            },
            ignore_cache=ignore_cache,
        )
        matches.extend(pv_similarAndGeneric_matches)


    # 3. REFORMATTING MATCHES
    ###########################################################################

    result: Dict[str, Variant] = {}

    # Reformating matches while discarding duplicates
    for row in matches:
        result[row["@rid"]] = cast(Variant, row)

    return list(result.values())
