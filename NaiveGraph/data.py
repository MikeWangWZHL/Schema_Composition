import networkx as nx 
from networkx.algorithms import isomorphism

def create_sample_graph_dataset_1():
    G1 = nx.DiGraph()
    G2 = nx.DiGraph()
    G3 = nx.DiGraph()

    G1.add_nodes_from([
        (0,{'label':'A'}),
        (1,{'label':'B'}),
        (2,{'label':'D'}),
        (3,{'label':'C'})
    ])
    G1.add_edges_from([
        (0,1),
        (1,2),
        (0,3),
        (3,2)
    ],label='a')

    G2.add_nodes_from([
        (0,{'label':'A'}),
        (1,{'label':'B'}),
        (2,{'label':'D'}),
    ])
    G2.add_edges_from([
        (0,1),
        (1,2)
    ],label='a')

    G3.add_nodes_from([
        (0,{'label':'A'}),
        (1,{'label':'C'}),
        (2,{'label':'D'}),
    ])

    G3.add_edges_from([
        (0,1),
        (1,2)
    ],label='a')

    return [G1,G2,G3]

def create_sample_graph_dataset_2():
    G1 = nx.DiGraph()
    G2 = nx.DiGraph()
    G3 = nx.DiGraph()

    G1.add_nodes_from([
        (0,{'label':'A'}),
        (1,{'label':'B'}),
        (2,{'label':'C'})
    ])
    G1.add_edges_from([
        (0,1),
        (1,2)
    ],label='a')
    G1.add_edges_from([(0,2)],label = 'b')

    G2.add_nodes_from([
        (0,{'label':'A'}),
        (2,{'label':'B'}),
        (1,{'label':'C'})
    ])
    G2.add_edges_from([
        (0,1),
        (2,1)
    ],label='a')

    G3.add_nodes_from([
        (0,{'label':'A'}),
        (1,{'label':'C'})
    ])

    G3.add_edges_from([
        (0,1)
    ],label='a')

    return [G1,G2,G3]