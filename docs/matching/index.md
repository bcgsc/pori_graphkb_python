# Ontology Algorithm

The matching algorithm implemented by this adaptor heavily uses the Graph Structure of GraphKB
to resolve aliases, generalisms, etc. The default behaviour of this algorithm is described below
and shown in the related examples. This is primarily accomplished via the `similarTo` query type
provided by the GraphKB API.

## Definitions

The entire knowledge base is defined as the graph

$$
G = (V, E)
$$

Below, subsets of Edges by their `@class` attribute are denoted as follows

$$
E_{<class>} = \{e: e \in E, e.class = \text{<class>} \}
$$

The edges are divided into two main groups for expansion: equivalency ($E_{eq}$)
and directional/tree ($E_{dir}$) edges

$$
\begin{align*}
    E_{eq} & = \{e: e \in E_{GeneralizationOf} \cup E_{AliasOf} \cup E_{CrossReferenceOf} \cup E_{DeprecatedBy} \cup E_{Infers} \}\\
    E_{dir} & = \{e: e \in E_{SubClassOf} \cup E_{ElementOf} \}
\end{align*}
$$

!!! Note "Edge Groups are Configurable"
    These are the default division of Edges. However, classes used for equivalent and tree edges
    can be configured in the query body of similarTo type
    queries sent to GraphKB

The target class (T) is used to define the subgraph by the subset of vertices which belong to a
the vertex class given as the target of the query (ex. Disease)

$$
\begin{align*}
    V_t = & \{v: v \in V, v.class = \text{t} \} \\
    G_t = & (V_t,  E) \\
\end{align*}
$$

which are used to define the corresponding subgraphs. Note that the equivalency subgraph
is undirected as edges are added for both directions

$$
\begin{align*}
    G_{eq} = & (V_t, \{uv: \{(u, v), (v, u)\} \cap E_{eq} \neq \emptyset\}) \\
    G_{dir} = & (V_t, \{uv: (u, v) \in E_{dir}\}) \\
\end{align*}
$$

## Match by Name

Matching begins with a subset of vertices which are selected by their name attribute

$$
\begin{equation}
V_{m} = \{v: v \in V(G_{t}), v.name = x\}
\end{equation}
$$

## Resolve Aliases

Next, equivalency edges ($E_{eq}$) are followed bidirectionally from the name matched set of vertices
($V_{m}$) to a specified depth ($n$) using a breadth first search. This is defined as the set
of walks, $W$ on the equivalency subgraph ($G_{eq}$).

$$
\begin{equation}
    W_{r} = \{(v_0, v_1, v_2, ..., v_n): (v_{j - 1}, v_{j}) \in E(G_{eq}), v_j \in V_{m} \}
\end{equation}
$$

## Follow the Directional Edges

The directional/tree edges are followed next. Unlike the equivalency edges, directionality is important here.
First we collect the vertices that are ancestors of the alias-resolved vertices.

$$
\begin{equation}
    W_{a} = \{(v_0, v_1, v_2, ..., v_{k}): (v_{j}, v_{j - 1}) \in E(G_{dir})  , v_j \in V(W_r) \cup V_{m} \}
\end{equation}
$$

Next we do the same for the descendants

$$
\begin{equation}
    W_{d} = \{(v_0, v_1, v_2, ..., v_{k}): (v_{j-1}, v_{j}) \in E(G_{dir}), v_j \in V(W_r) \cup V_{m} \}
\end{equation}
$$

## Resolve Final Aliases

Finally we repeat the equivalency expansion on the union of the ancestor and descendant vertices

$$
\begin{equation}
    W_{f} = \{(v_0, v_1, v_2, ..., v_n): (v_{j-1}, v_{j}) \in E(G_{eq}), v_j \in V(W_{a} \cup W_{d} \cup W_{r}) \cup V_{m} \}
\end{equation}
$$

The set of vertices returned by the matching algorithm is the total union of all vertices returned
by the above equations (Includes any vertices which may have been singlets in the matching subgraphs)

$$
V(W_{f} \cup W_{d} \cup W_{a} \cup W_{r}) \cup V_{m}
$$
