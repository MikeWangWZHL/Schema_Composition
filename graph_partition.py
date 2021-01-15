import numpy as np
import os
from os import listdir
from os.path import isfile, join
from collections import defaultdict
import json
import matplotlib.pyplot as plt
import math

import networkx as nx 
from networkx.algorithms.community.centrality import girvan_newman
from networkx.algorithms.community.quality import modularity
from networkx.algorithms.centrality import edge_betweenness_centrality
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
    ],type='Temporal_Order')

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
    # if not using custom edge score criteria
    if most_valuable_edge_func is None:

        def most_valuable_edge_func(G):
            betweenness = edge_betweenness_centrality(G)
            current_highest_edge = max(betweenness, key=betweenness.get)

            # check if it is an event->event temporal edge, if not keep searching for the highest score temperal edge   
            while G.get_edge_data(*current_highest_edge)['type'] != 'Temporal_Order':
                del betweenness[current_highest_edge]
            
                # handle edge case that the current community has on Temporal Edge
                if betweenness == {}:
                    original_betweenness = edge_betweenness_centrality(G)
                    return max(original_betweenness, key=original_betweenness.get)
                
                current_highest_edge = max(betweenness, key=betweenness.get)

            ## print('pick highest betweenness score edge: ', current_highest_edge)
            return current_highest_edge
 

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

def draw_subgraphs(nx_subgraphs, save_path, if_show_edge_type = True, show_max = None):
    if show_max is None:
        nrows = int(math.sqrt(len(nx_subgraphs)))+1
    else:
        nrows = int(math.sqrt(int(show_max)))+1

    fig, axes = plt.subplots(nrows=nrows, ncols=nrows, figsize = (8*nrows,8*nrows))
    fig.tight_layout()
    ax = axes.flatten()

    for i in range(nrows*nrows):
        if i < len(nx_subgraphs):
            
            # nx.draw(nx_subgraphs[i], ax=ax[i], node_size = 5)
            # draw_single_subgraph(nx_subgraphs[i], ax[i])
            G = nx_subgraphs[i]

            pos = nx.circular_layout(G)
            # pos = nx.spring_layout(G)
            # pos = nx.rescale_layout_dict(pos, scale = 3)
            # pos = nx.shell_layout(G)
            nx.draw(G, pos, ax = ax[i], alpha = 0.7, arrowsize = 8, node_size = 400)
            node_labels = nx.get_node_attributes(G,'type')
            nx.draw_networkx_labels(G, pos, ax = ax[i],labels = node_labels,font_size = 8)
            if if_show_edge_type:
                edge_labels = nx.get_edge_attributes(G,'type')
                nx.draw_networkx_edge_labels(G, pos,edge_labels,ax = ax[i],font_size = 6)
            
            ax[i].set_xlim([1.5*x for x in ax[i].get_xlim()])
            ax[i].set_ylim([1.5*y for y in ax[i].get_ylim()])
            # ax[i].set_xlim(0,10)

        ax[i].set_axis_off()
    fig.savefig(save_path)
    print(f'saved visualization to {save_path}')

def visualize_partition(nx_graph, partition, save_path = 'temp.png', if_show_edge_type = False, show_max = None):
    partition_subgraphs = []
    for community in partition:
        partition_subgraphs.append(nx_graph.subgraph(community))
    draw_subgraphs(partition_subgraphs, save_path, if_show_edge_type, show_max)


'''example test'''
if __name__ == '__main__':

    # stopping criteria 
    K = 30

    doc = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/test/suicide_ied_test.json'
    g_dicts = []
    with open(doc) as f:
        for line in f:
            g_dicts.append(json.loads(line))
    G = create_nx_graph_Event_and_Argument(g_dicts[0])
    # G = create_nx_graph_Event_Only(g_dicts[0])
    print()
    print("graph name: ", G.graph)
    print()
    print('Nodes: ', G.nodes().data())
    print()
    print('Edges: ',G.edges().data())
    print()
    print('========================================================')



    # print('mini example: ')
    # G = create_mini_example_graph_1()
    # print(G.nodes().data())
    # print(G.edges().data())
    # print()
    # print('========================================================')
    
    print('edge betweenness: ', edge_betweenness_centrality(G))
    print()

    partitions = partition_graph(G, most_valuable_edge_func = None, first_k = K)
    partitions_with_modularity = []
    for partition in partitions:
        # print('partition: ', partition)
        print('number of communities: ', len(partition))
        print()
        this_partition_modularity = cal_modularity(G, list(partition))
        print('moduality: ', this_partition_modularity)
        print('--------------')
        partitions_with_modularity.append((partition,this_partition_modularity))

    sorted_partitions_with_modularity = sorted(partitions_with_modularity, key = lambda p : p[1], reverse = True)
    print('highest modularity partition: ', sorted_partitions_with_modularity[0][0])
    print(f'\n\nhighest modularity partition community number: {len(sorted_partitions_with_modularity[0][0])}, modularity: {sorted_partitions_with_modularity[0][1]}')
    
    best_partition = sorted_partitions_with_modularity[0][0]
    print()
    visualize_partition(G, best_partition)

