# Ontology Algorithm

The matching algorithm implemented by this adaptor heavily uses the Graph Structure of GraphKB
to resolve aliases, generalisms, etc. The default behaviour of this algorithm is described below
and shown in the related examples. This is primarily accomplished via the `similarTo` query type
provided by the GraphKB API.

## Definitions

The entire knowledge base is defined as the graph, $G = (V, E)$. For any given query let the
subgraph of $G$ containing only vertices of the class type specified in the query (ex. Disease)
be, $V_t$.

All edges between these vertices are then categorized into two disjoint sets: synonym-like
($E_{syn}$) or inheritance-like ($E_{inh}$). By default the synonym-like edges are:
GeneralizationOf, AliasOf, CrossReferenceOf, DeprecatedBy, and Infers. Whereas the
inheritance-like edges are: SubClassOf, and ElementOf.

!!! Note "Edge Groups are Configurable"
    These are the default division of Edges. However, classes used the edge sets
    can be configured in the query body of similarTo type
    queries sent to GraphKB

Synonym-like edges are treated as undirected and therefore the set of synonym-like edges used for
the following steps can be written

$$
\begin{equation}
    E_{bsyn} = \{uv: \{(u, v), (v, u)\} \cap E_{syn} \neq \emptyset\}
\end{equation}
$$

Disease matching on the following graph will be used as a running example

![disease matching](../images/pori-disease-matching-1.png)

## Match by Name

Let the set of vertices (from $V_t$) where the name attribute is an exact match to the input query
name be $V_m$.

![disease matching](../images/pori-disease-matching-2.png)

## Resolve Aliases

Follow synonym-like edges from the set of name-matched vertices

$$
\begin{equation}
    V_{syn} = \{v: v_0 \rightarrow v, v_0 \in V_{m}, (v_{j - 1}, v_{j}) \in E_{bsyn}\} \cup V_m
\end{equation}
$$

![disease matching](../images/pori-disease-matching-3.png)

## Follow the Inheritance-like Edges

The inheritance-like edges are followed next. Unlike the synonym-like edges, directionality is important here.
We collect the set of vertices from all paths were at least one member of the path belongs to a
previously collected vertex.

$$
\begin{equation}
    V_{inh} = \{v: v_0 \rightarrow v, \vert V(v_0 \rightarrow v) \cap V_{syn} \vert > 0, (v_{j - 1}, v_{j}) \in E_{inh} \} \cup V_{syn}
\end{equation}
$$

![disease matching](../images/pori-disease-matching-4.png)

## Resolve Final Aliases

Finally, we repeat the synonym-like expansion

$$
\begin{equation}
    V_{f} = \{v: v_0 \rightarrow v, v_0 \in V_{inh}, (v_{j - 1}, v_{j}) \in E_{bsyn}\} \cup V_{inh}
\end{equation}
$$

![disease matching](../images/pori-disease-matching-5.png)

## Bounding

Note that the above Graph Traversals are bounded by input parameters to specify a maximum depth.
