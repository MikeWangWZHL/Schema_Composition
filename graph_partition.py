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

'''generate mini example'''
def create_mini_example_graph_1():
    G1 = nx.DiGraph()

    G1.add_nodes_from([
        (0,{'type':'A','category':'Event'}),
        (1,{'type':'B','category':'Event'}),
        (2,{'type':'D','category':'Event'}),
        (3,{'type':'C','category':'Event'}),
        (4,{'type':'E','category':'Event'}),
        (5,{'type':'F','category':'Event'}),
        (6,{'type':'G','category':'Event'})
    ])
    G1.add_edges_from([
        (0,1),
        (1,2),
        (0,3),
        (3,2),
        (2,4),
        (4,6),
        (4,5),
        (6,5)
    ],type='Temporal_Order')

    G1.add_nodes_from([
        (7,{'type': 'PER','category': 'Entity'})
    ])
    G1.add_edges_from([
        (3,7),
        (2,7)
    ])


    return G1


'''graph partition'''
def cal_modularity(nx_graph, partition, if_weighted = True):
    if if_weighted:
        return modularity(nx_graph, partition, weight = 'score')
    else:
        return modularity(nx_graph, partition)

def partition_graph(nx_graph, most_valuable_edge_func = None, first_k = 1, if_weighted = True):
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
            if if_weighted:
                betweenness = edge_betweenness_centrality(G, weight = 'score')
            else:
                betweenness = edge_betweenness_centrality(G)

            current_highest_edge = max(betweenness, key=betweenness.get)

            # check if it is an event->event temporal edge, if not keep searching for the highest score temperal edge   
            while G.get_edge_data(*current_highest_edge)['type'] != 'Temporal_Order':
                del betweenness[current_highest_edge]
            
                # handle edge case that the current community has no Temporal Edge
                if betweenness == {}:
                    original_betweenness = edge_betweenness_centrality(G)
                    return max(original_betweenness, key=original_betweenness.get)
                
                current_highest_edge = max(betweenness, key=betweenness.get)

            # print('pick highest betweenness score edge: ', current_highest_edge)
            return current_highest_edge
 
    comp = girvan_newman(nx_graph, most_valuable_edge = most_valuable_edge_func)
    partitions = []
    for communities in itertools.islice(comp, first_k):
        partitions.append(tuple(sorted(c) for c in communities))
    return partitions

def filter_partition(nx_graph, partition):
    '''
        filter out community that does not have at least two event nodes
    '''
    print('===== filter partition =====')
    print('original community number: ', len(partition))
    filtered_partition = []
    for community in partition:
        subgraph_view = nx_graph.subgraph(community)
        for e in subgraph_view.edges().data():
            if e[2]['type'] == 'Temporal_Order':
                filtered_partition.append(community)
                break

    print('filtered community number: ', len(filtered_partition))
    print()
    return filtered_partition

'''edge score function'''
# TODO add multi-hop overlapping arg calculation
def count_overlapping_arg(nx_graph,e1,e2):
    count = 0

    e1_nbs = []
    for e1_nb in nx_graph.neighbors(e1):
        e1_nbs.append(e1_nb)

    for e2_nb in nx_graph.neighbors(e2):
        if e2_nb in e1_nbs and nx_graph.nodes[e2_nb]['category'] == 'Entity':
            count += 1
    
    return count
       
def calculate_single_edge_score(nx_graph,e1,e2, dataset_name = 'suicide_ied', conditional_prob_path = './conditional_probability_json'):
    '''calculate s(e1->e2)'''
    # load p(e2|e1) score
    p_e2_given_e1_dict = json.load(open(conditional_prob_path + f'/{dataset_name}_conditional_prob.json'))
    e1_type = nx_graph.nodes[e1]['type']
    e2_type = nx_graph.nodes[e2]['type']
    
    p_e2_given_e1_score = p_e2_given_e1_dict[e1_type][e2_type]

    # calculate overlapping args
    overlap_arg_count = count_overlapping_arg(nx_graph,e1,e2)

    # spatial score
    #TODO
    spatial_score = 1

    # calculate score
    s = p_e2_given_e1_score * spatial_score * (1 + math.log(1 + overlap_arg_count))
    
    return s

def add_edge_scores(nx_graph, dataset_name = 'suicide_ied', conditional_prob_path = './conditional_probability_json'):
    for edge in nx_graph.edges().data():
        u = edge[0]
        v = edge[1]
        e_attr = edge[2]
        if e_attr['category'] == 'Temporal_Order':
            new_score = calculate_single_edge_score(nx_graph,u,v,dataset_name = dataset_name, conditional_prob_path = conditional_prob_path)
            nx_graph[u][v]['score'] = new_score
    return nx_graph

def most_valuable_edge_f(nx_graph, dataset_name = 'suicide_ied', conditional_prob_path = './conditional_probability_json'):
    '''
        Parameters:
        ----------
        nx_graph : a networkx graph

        Returns:
        ----------
        an edge with highest inter-episode score
    '''
    # TODO
    

'''visualization'''
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
            nx.draw(G, pos, ax = ax[i], alpha = 0.7, arrowsize = 10, node_size = 400)
            node_labels = nx.get_node_attributes(G,'type')
            nx.draw_networkx_labels(G, pos, ax = ax[i],labels = node_labels,font_size = 10)
            if if_show_edge_type:
                edge_labels = nx.get_edge_attributes(G,'type')
                nx.draw_networkx_edge_labels(G, pos,edge_labels,ax = ax[i],font_size = 8)
            
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


'''usage example'''
if __name__ == '__main__':

    '''set up hyperparameters'''
    # stopping criteria, run:
    K = 30
    # input graph g objects json file:
    doc = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/test/suicide_ied_test.json'
    # using instance index:
    instance_index = 0

    '''load instance graph g objects'''
    g_dicts = []
    with open(doc) as f:
        for line in f:
            g_dicts.append(json.loads(line))
    
    '''create nx graph of the specified instance'''
    G = create_nx_graph_Event_and_Argument(g_dicts[instance_index])
    # G = create_nx_graph_Event_Only(g_dicts[0])
    
    print('using instance: ', instance_index)
    print()
    print("graph name: ", G.graph)
    # print()
    # print('edge betweenness: ', edge_betweenness_centrality(G))
    # print()

    # print('Nodes: ', G.nodes().data())
    # print()
    # print('Edges: ',G.edges().data())
    # print()
    # print('========================================================')
    
    # print('mini example: ')
    # G = create_mini_example_graph_1()
    # K = 1
    # print(G.nodes().data())
    # print(G.edges().data())
    # print()
    # print('========================================================')
    
    '''calculate and add edge scores as weight'''
    add_edge_scores(G, dataset_name = 'suicide_ied', conditional_prob_path = './conditional_probability_json')
    ## check scores
        # score_list = []
        # for e in G.edges().data():
        #     if e[2]['category'] == 'Temporal_Order':
        #         # print(G.nodes[e[0]]['type'],G.nodes[e[1]]['type'],e[2]['score'])
        #         score_list.append((G.nodes[e[0]]['type'],G.nodes[e[1]]['type'],e[2]['score']))
        # score_list.sort(reverse = True, key = lambda a: a[2])
        # for s in score_list:
        #     print(s)

    '''do partition'''
    partitions = partition_graph(G, most_valuable_edge_func = None, first_k = K, if_weighted = True)
    # print('vis full graph: ')
    # visualize_partition(G, [G.nodes()], save_path = 'full_G_temp.png')
    partitions_with_modularity = []
    for partition in partitions:
        # print('partition: ', partition)
        print('number of communities: ', len(partition))
        print()
        this_partition_modularity = cal_modularity(G, list(partition), if_weighted = True)
        print('moduality: ', this_partition_modularity)
        print('--------------')
        partitions_with_modularity.append((partition,this_partition_modularity))
    
    '''sort based on modularity score'''
    sorted_partitions_with_modularity = sorted(partitions_with_modularity, key = lambda p : p[1], reverse = True)
    print('highest modularity partition: ', sorted_partitions_with_modularity[0][0])
    print(f'\n\nhighest modularity partition community number: {len(sorted_partitions_with_modularity[0][0])}, modularity: {sorted_partitions_with_modularity[0][1]}')
    
    '''visualize highest partition'''
    best_partition = sorted_partitions_with_modularity[0][0]
    print()
    '''filter parition'''
    filtered_best = filter_partition(G,best_partition)
    '''visualize'''
    visualize_partition(G, best_partition, save_path = 'before_filtering_weighted_temp.png',if_show_edge_type = True)
    visualize_partition(G, filtered_best, save_path = 'after_filtering_weighted_temp.png',if_show_edge_type = True)

