# Disease Example

In the following example, the user is trying to get all *equivalent* disease terms to the patient's
diagnosis. The patient has a diagnosis of "Breast Adenocarcinoma". Below is a diagram of a subset of
Disease Ontology and NCIt terms and their relationships. This is the default behaviour of the
[`get_term_tree()`](./../reference/graphkb/vocab/#get_term_tree) function.

```python
from graphkb.vocab import get_term_tree

matched_terms = get_term_tree(
    graphkb_conn,  # previously set up connection
    'breast adenocarcinoma',
    ontology_class= 'Disease'
)
```

![initial graph](../images/pori-disease-matching-1.png)

In the above diagram the "A" indicates an "alias" type relationship and the "S" indicates a `SubClassOf` type relationship.

## Match by Name

The first thing the algorithm does is find all Disease terms that exactly match the input term
(ignoring case)

![match by name](../images/pori-disease-matching-2.png)

The matched records (terms) are highlighted in blue. We can see it has matched both the Disease
Ontology and NCIt terms.

## Resolve Aliases

The next step is to resolve equivalent names of the current set of terms (the two terms matched
above). While in practice this will resolve many more relationship types, we have only shown
the `AliasOf` relationship here for simplicity. The following relationship types would be treated
identically in practice: `CrossReferenceOf`, `GeneralizationOf`, `DeprecatedBy`, and `Infers`.

![resolve aliases](../images/pori-disease-matching-3.png)

## Follow the Subclass Tree

The next step is to follow the subclass relationships. All the more specific subclasses of the
current set of terms is matched and all the less specific superclasses of the current set of terms
are matched. Although not shown for simplcity, `ElementOf` relationships are treated the same as
`SubClassOf` relationships by default.

![subclass tree](../images/pori-disease-matching-4.png)

## Resolve Final Aliases

Finally we expand the current set of terms by alias terms again to capture aliases of the more
general parent and more specific child terms expanded in the previous step.

![resolve aliases](../images/pori-disease-matching-5.png)

As we can see above we have collected all terms appropriately related to "Breast Carcinoma" while
excluding the thyroid carcinoma terms. Now we have a set of equivalent disease terms we can use
to find related statements or classify statements as matching or not matching the patient's disease.
