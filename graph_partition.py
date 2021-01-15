import numpy as np
import os
from os import listdir
from os.path import isfile, join
from collections import defaultdict
import json

import networkx as nx 
from networkx.algorithms.community.centrality import girvan_newman
from networkx.algorithms.community.quality import modularity
import itertools

from create_graph import create_nx_graph_Event_Only, create_nx_graph_Event_and_Argument


def create_mini_example_graph_1():
    G1 = nx.DiGraph()

    G1.add_nodes_from([
        (0,{'type':'A'}),
        (1,{'type':'B'}),
        (2,{'type':'D'}),
        (3,{'type':'C'}),
        (4,{'type':'E'}),
        (5,{'type':'F'}),
        (6,{'type':'G'})
    ])
    G1.add_edges_from([
        (0,1),
        (1,2),
        (0,3),
        (3,2),
        (2,4),
        (4,5),
        (6,5)
    ],type='a')

    return G1

def cal_modularity(nx_graph, partition):
    return modularity(nx_graph, partition)

def partition_graph(nx_graph, most_valuable_edge_func = None, first_k = 1):
    '''
        Parameters:
        ----------
        nx_graph : a networkx graph
        most_valuable_edge_func : a function returns a highest score edge given a networkx graph
        first_k : return first k steps of partitions

        Returns:
        ----------
        a List of partitions
    '''
    comp = girvan_newman(nx_graph, most_valuable_edge = most_valuable_edge_func)
    partitions = []
    for communities in itertools.islice(comp, first_k):
        partitions.append(tuple(sorted(c) for c in communities))
    return partitions

def most_valuable_edge_f(nx_graph):
    '''
        Parameters:
        ----------
        nx_graph : a networkx graph

        Returns:
        ----------
        an edge with highest inter-episode score
    '''
    # TODO
    pass



'''example test'''
doc = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/test/suicide_ied_test.json'
g_dicts = []
with open(doc) as f:
    for line in f:
        g_dicts.append(json.loads(line))
# sample_g = create_nx_graph_Event_and_Argument(g_dicts[0])
sample_g = create_nx_graph_Event_Only(g_dicts[0])
print()
print("graph name: ", sample_g.graph)
print()
print('Nodes: ', sample_g.nodes().data())
print()
print('Edges: ',sample_g.edges().data())
print()
print('========================================================')



print('mini example: ')
G = create_mini_example_graph_1()
print(G.nodes().data())
print(G.edges().data())
print()
print('========================================================')
partitions = partition_graph(G, most_valuable_edge_func = None, first_k = 2)
for partition in partitions:
    print('partition: ', partition)
    print()
    print('moduality: ', cal_modularity(G, list(partition)))
    print('--------------')
# print('partitions: ', partitions)


