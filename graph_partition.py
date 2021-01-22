import numpy as np
import os
from os import listdir
from os.path import isfile, join
from collections import defaultdict
import json
import matplotlib.pyplot as plt
import math
import argparse
import itertools
from itertools import count
import copy

import networkx as nx 
from networkx.algorithms.community.centrality import girvan_newman
from networkx.algorithms.community.quality import modularity
from networkx.algorithms.centrality import edge_betweenness_centrality
from networkx.algorithms.traversal.breadth_first_search import descendants_at_distance

from create_graph import create_nx_graph_Event_Only, create_nx_graph_Event_and_Argument
from generate_UoF_visualization_format import convert_to_UoF_format
from spectral_clustering import spectral_clustering

DISCOUNT = 0.5
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
    ],type='Temporal_Order', category = 'Temporal_Order')

    G1.add_nodes_from([
        (7,{'type': 'PER','category': 'Entity'})
    ])
    G1.add_edges_from([
        (3,7),
        (2,7)
    ],category = 'Argument')


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

def filter_partition(nx_graph, partition, if_keep_single_event_episode = False):
    '''
        filter out community that does not have at least two event nodes
    '''
    print('===== filter partition =====')
    print('original community number: ', len(partition))
    filtered_partition = []
    for community in partition:
        subgraph_view = nx_graph.subgraph(community)
        for e in subgraph_view.edges().data():
            if if_keep_single_event_episode:
                if G.nodes[e[0]]['category'] == 'Event' or G.nodes[e[1]]['category'] == 'Event':
                    filtered_partition.append(community)
                    break
            else:
                if e[2]['type'] == 'Temporal_Order':
                    filtered_partition.append(community)
                    break
    print('filtered community number: ', len(filtered_partition))
    print()
    
    # check filtered community:

    print('===== filtered out single event episodes: =====')
    for c in partition:
        if c not in filtered_partition:
            subgraph_view = nx_graph.subgraph(c)
            for n in subgraph_view.nodes().data():
                if n[1]['category'] == 'Event':
                    print(n[1]['type'])
    print()
    
    return filtered_partition

'''edge score function'''
def count_overlapping_arg(nx_graph,e1,e2):
    count = 0

    e1_nbs = []
    for e1_nb in nx_graph.neighbors(e1):
        e1_nbs.append(e1_nb)

    for e2_nb in nx_graph.neighbors(e2):
        if e2_nb in e1_nbs and nx_graph.nodes[e2_nb]['category'] == 'Entity':
            count += 1
    
    return count

def get_multihop_event_neighbor(nx_graph,n,hop = 1):
    neighbors = []
    for h in range(hop):
        d = h + 1
        all_neighbor_at_hop_h = descendants_at_distance(nx_graph,n,d)
        event_neighbor_at_hop_h = set()
        for nb in all_neighbor_at_hop_h:
            if nx_graph.nodes[nb]['category'] == 'Event':
                event_neighbor_at_hop_h.add(nb)
        # print(event_neighbor_at_hop_h)
        neighbors.append(event_neighbor_at_hop_h)
    return neighbors

def count_multihop_overlapping_arg(nx_graph,e1,e2,hop = 0):

    if hop == 0:
        return count_overlapping_arg(nx_graph,e1,e2)
    else:
        e1_neighbors = get_multihop_event_neighbor(nx_graph,e1,hop = hop)
        e2_neighbors = get_multihop_event_neighbor(nx_graph,e2,hop = hop)
        total_count = 0
        # hop = 0:
        total_count += count_overlapping_arg(nx_graph,e1,e2)
        # hop > 0:
        for h in range(hop):
            discount = pow(DISCOUNT,h+1)
            if e2_neighbors[h] != set():
                for e2_nb in e2_neighbors[h]:
                    if e2_nb != e1:
                        total_count += discount*count_overlapping_arg(nx_graph,e1,e2_nb)
            if e1_neighbors[h] != set():
                for e1_nb in e1_neighbors[h]:
                    if e1_nb != e2:
                        total_count += discount*count_overlapping_arg(nx_graph,e1_nb,e2)
        return total_count

def calculate_single_edge_score(nx_graph,e1,e2, hop = 0, dataset_name = 'suicide_ied', conditional_prob_path = './conditional_probability_json_IED'):
    '''calculate s(e1->e2)'''
    # load p(e2|e1) score
    p_e2_given_e1_dict = json.load(open(conditional_prob_path + f'/{dataset_name}_conditional_prob.json'))
    e1_type = nx_graph.nodes[e1]['type']
    e2_type = nx_graph.nodes[e2]['type']
    
    if e1_type not in p_e2_given_e1_dict:
        print('Not Found: ',e1_type)
        p_e2_given_e1_score = 1
    else:
        if e2_type not in p_e2_given_e1_dict[e1_type]:
            print('Not Found: ', e2_type)
            p_e2_given_e1_score = 1
        else:
            p_e2_given_e1_score = p_e2_given_e1_dict[e1_type][e2_type]

    # calculate overlapping args
    # overlap_arg_count = count_overlapping_arg(nx_graph,e1,e2)
    overlap_arg_count = count_multihop_overlapping_arg(nx_graph,e1,e2, hop = hop)

    # spatial score
    #TODO
    spatial_score = 1

    # calculate score
    s = p_e2_given_e1_score * spatial_score * (1 + math.log(1 + overlap_arg_count))
    
    return s

def add_edge_scores(nx_graph, hop = 0, dataset_name = 'suicide_ied', conditional_prob_path = './conditional_probability_json_IED'):
    # print(f'using <{dataset_name}> conditional json ')
    for edge in nx_graph.edges().data():
        u = edge[0]
        v = edge[1]
        e_attr = edge[2]
        if e_attr['category'] == 'Temporal_Order':
            new_score = calculate_single_edge_score(nx_graph,u,v,hop = hop,dataset_name = dataset_name, conditional_prob_path = conditional_prob_path)
            nx_graph[u][v]['score'] = new_score
    return nx_graph

def most_valuable_edge_f(nx_graph, dataset_name = 'suicide_ied', conditional_prob_path = './conditional_probability_json_IED'):
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

def get_event_node_partition(nx_graph, partition):
    event_node_partition = []
    for community in partition:
        new_community = []
        for node_id in community:
            if nx_graph.nodes[node_id]['category'] == 'Event':
                new_community.append(node_id)
        event_node_partition.append(new_community)
    return event_node_partition

def add_event_node_group_attr(nx_graph, event_partition):
    for i in range(len(event_partition)):
        group_id = i+1
        community = event_partition[i]
        for node in community:
            nx_graph.nodes[node]['group'] = group_id
    return nx_graph

def add_node_group_attr(nx_graph, partition):
    return add_event_node_group_attr(nx_graph, partition)

def visualize_instance_graph(G, partition = None, save_path = 'partition_vis_temp.png'):
    """
        G: a networkx graph
    """
    num_nodes = G.number_of_nodes()

    pos = nx.spring_layout(G, k=1.0, iterations=50)

    plt.figure(figsize=(int(num_nodes*0.3), int(num_nodes*0.3)))

    # load partition info
    if partition is not None:
        add_event_node_group_attr(G, partition)

        groups = set(nx.get_node_attributes(G,'group').values())
        mapping = dict(zip(sorted(groups),count()))
        nodes = G.nodes()
        colors = [mapping[G.nodes[n]['group']] for n in nodes]
        
        pos = nx.multipartite_layout(G, subset_key = 'group', scale = 1)
        # pos = nx.nx_pydot.pydot_layout(G, prog="dot")
        
        # flat_episode_events = [item for sublist in partition for item in sublist]
        # single_nodes = [n for n in G.nodes() if n not in flat_episode_events ]
        # whole_partition = copy.deepcopy(partition)
        # whole_partition.append(single_nodes)
        # pos = nx.shell_layout(G, nlist = whole_partition)

        # pos = nx.kamada_kawai_layout(G, pos = pos, weight = 'score')
        # pos = nx.rescale_layout_dict(pos,scale = 1.5)
        # pos = nx.planar_layout(G)

        ec = nx.draw_networkx_edges(G, pos, alpha=0.2)
        nc = nx.draw_networkx_nodes(G, pos, alpha = 0.7, node_color=colors, node_size=500, cmap=plt.cm.jet)
        plt.colorbar(nc)
        plt.axis('off')


    else:
        nx.draw(G, pos, alpha = 0.5, arrowsize = 10, node_size = 200)
    
    node_labels = nx.get_node_attributes(G,'type')

    # use shorter type label:
    for key, value in node_labels.items():
        node_labels[key] = value.split('.')[1]

    nx.draw_networkx_labels(G, pos, labels = node_labels,font_size = 8)
    # edge_labels = nx.get_edge_attributes(G,'type')
    # nx.draw_networkx_edge_labels(G, pos, edge_labels)
    
    x_values, y_values = zip(*pos.values())
    x_max = max(x_values)
    x_min = min(x_values)
    x_margin = (x_max - x_min) * 0.25
    plt.xlim(x_min - x_margin, x_max + x_margin)
    
    plt.savefig(save_path, dpi = 250)
    print(f'saved visualization to {save_path}')

# unit test:
# print('mini example: ')
# G = create_mini_example_graph_1()
# K = 1
# print(G.nodes().data())
# print(G.edges().data())
# print()
# print('========================================================')
# print(count_multihop_overlapping_arg(G,0,2,hop = 1))
# quit()

def bool_arg(bool_str):
    if bool_str in ['False', 'false', 'f', 'no', 'No', 'N']:
        return False
    else:
        return True

'''usage example'''
if __name__ == '__main__':
    '''set up arg parser'''
    parser = argparse.ArgumentParser(description='graph partition')
    parser.add_argument('-d', '--dataset_name', help='input dataset name', default = 'suicide_ied')
    parser.add_argument('-index', '--input_instance_index', help='input_instance_index', default = 0)
    parser.add_argument('-p', '--phase', help='train test dev', default = 'test')
    parser.add_argument('-hp', '--hop', help='number of hops considering when counting overlapping args', default = 0)
    parser.add_argument('-i','--input_dir',help = 'input json dataset directory', default = '.')
    parser.add_argument('-cd','--conditional_prob_dir',help = 'input conditional probability dir path', default = './conditional_probs/conditional_probability_json_IED')
    parser.add_argument('-keep','--if_keep_single_node_episode',help = 'if show single node episode', default = False)
    
    parser.add_argument('-par','--partition_method',help = 'choose from girvan_newman, spectral_clustering', default = 'girvan_newman')
    # parser.add_argument('-nc','--cluster_num',help = 'specify cluster number for spectral clustering', default = 2)
    # parser.add_argument('-mnc','--max_cluster_num',help = 'specify max cluster number for spectral clustering', default = 2)
    parser.add_argument('-o', '--output_graph_pickle_dir', help = 'specify output graph pickle object dir', default = '.')

    args = vars(parser.parse_args())

    '''set up hyperparameters'''
    # phase
    phase = args['phase'] # train, dev, test
    # output dir
    output_graph_dir = args['output_graph_pickle_dir']
    if not os.path.exists(output_graph_dir):
        os.makedirs(output_graph_dir)
    if not os.path.exists(join(output_graph_dir,'png')):
        os.makedirs(join(output_graph_dir,'png'))
    if not os.path.exists(join(output_graph_dir,'graph_objects')):
        os.makedirs(join(output_graph_dir,'graph_objects'))
    
    # using what partition method
    partition_method = args['partition_method']
    
    for dataset_name in ['suicide_ied','wiki_drone_strikes','wiki_mass_car_bombings','wiki_ied_bombings']:
        # input graph g objects json file:
        print(f'**************************************************')
        print(f'******** using dataset: {dataset_name} ***********')
        print(f'**************************************************')
        # dataset_name = args['dataset_name']
        dataset_file = f'{dataset_name}_{phase}' # suicide_ied_, wiki_drone_strikes_, wiki_mass_car_bombings_
        input_dir = args['input_dir']
        doc = f'{input_dir}/{phase}/{dataset_file}.json'
        # using conditional probability dir
        conditional_prob_dir = args['conditional_prob_dir']
        # using instance index:
        if args['input_instance_index'] == 'inf':
            instance_index = 'inf'
        else:
            instance_index = int(args['input_instance_index'])
        # episode filtering
        if_keep_single_event_episode = bool_arg(args['if_keep_single_node_episode'])
        # hops
        hop_num = int(args['hop'])
        
        # '''required for spectral_cluster'''
        # max_cluster_num = int(args['max_cluster_num'])

        print('======== config =========')
        print(f'using partiton method: {partition_method}\n')
        print(f'using dataset: {dataset_name}_{phase}, instance: {instance_index}\n')
        print(f'output path: ', output_graph_dir)
        
        '''load instance graph g objects'''
        g_dicts = []
        with open(doc) as f:
            for line in f:
                g_dicts.append(json.loads(line))
        print('total number of instances: ',len(g_dicts))
        
        if instance_index == 'inf':
            for instance_index in range(len(g_dicts)):
                '''create nx graph of the specified instance'''
                G = create_nx_graph_Event_and_Argument(g_dicts[instance_index])
                # G = create_nx_graph_Event_Only(g_dicts[0])
                print(f'  == instance {instance_index} ==')
                print("graph name: ", G.graph['name'])
                
                if partition_method == 'girvan_newman':
                    # stopping criteria, should be related to graph size:
                    node_number = G.number_of_nodes()
                    print('node_number: ', node_number)
                    K = int(node_number/4)
                    print(f'stop at {K}')

                elif partition_method == 'spectral_clustering':
                    node_number = G.number_of_nodes()
                    print('node_number: ', node_number)
                    max_cluster_num = int(node_number/4)
                    print('max cluster num: ', max_cluster_num)

                print(f'number of hops: {hop_num} with discount {DISCOUNT}\n')
                print("graph filtering criteria: if keep single event episode? ", if_keep_single_event_episode)
                print('=========================')
                # printing
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
                print('adding edge score ... ')
                add_edge_scores(G,hop = hop_num, dataset_name = dataset_name, conditional_prob_path = conditional_prob_dir)
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
                if partition_method == 'girvan_newman':
                    print('running girvan_newman ...')
                    partitions = partition_graph(G, most_valuable_edge_func = None, first_k = K, if_weighted = True)
                    
                elif partition_method == 'spectral_clustering':
                    print('running spectral_clustering ...')
                    partitions = []
                    for cluster_num in range(2, max_cluster_num):
                        partitions.append(spectral_clustering(G, weight_keyword = 'score', cluster_num = cluster_num, save_visualization_path = None))
                    
                partitions_with_modularity = []
                for partition in partitions:
                    # print('partition: ', partition)
                    # print('--------------')
                    # print('number of communities: ', len(partition))
                    this_partition_modularity = cal_modularity(G, list(partition), if_weighted = True)
                    # print('moduality: ', this_partition_modularity)
                    # print('--------------')
                    partitions_with_modularity.append((partition,this_partition_modularity))
                
                '''sort based on modularity score'''
                sorted_partitions_with_modularity = sorted(partitions_with_modularity, key = lambda p : p[1], reverse = True)
                # print('highest modularity partition: ', sorted_partitions_with_modularity[0][0])
                highest_score_cluster_num = len(sorted_partitions_with_modularity[0][0])
                print(f'\n\nhighest modularity partition community number: {highest_score_cluster_num}, modularity: {sorted_partitions_with_modularity[0][1]}')
                '''get highest moduality partition'''
                best_partition = sorted_partitions_with_modularity[0][0]

                '''filter parition'''
                filtered_best_partition = filter_partition(G,best_partition, if_keep_single_event_episode = if_keep_single_event_episode)
                
                
                '''save graph'''
                G_with_partition = add_node_group_attr(G, filtered_best_partition)
                save_object_path = join(join(output_graph_dir,'graph_objects'),f'{dataset_file}_{instance_index}.pickle')
                nx.write_gpickle(G_with_partition, save_object_path)

                '''visualize subgraphs'''
                # if if_keep_single_event_episode:
                #     visualize_partition(G, filtered_best_partition, save_path = f'./png/keepsingle_{dataset_name}_{phase}_{instance_index}_hop_{hop_num}_discount_{DISCOUNT}.png',if_show_edge_type = True)
                # else:
                #     visualize_partition(G, filtered_best_partition, save_path = f'./png/{dataset_name}_{phase}_{instance_index}_hop_{hop_num}_discount_{DISCOUNT}.png',if_show_edge_type = True)

                '''visualize instance graph with partition'''
                G_event_only = create_nx_graph_Event_Only(g_dicts[instance_index])
                filtered_best_event_partition = get_event_node_partition(G, filtered_best_partition)
                assert len(filtered_best_partition) == len(filtered_best_event_partition)
                if partition_method == 'girvan_newman':
                    visualize_instance_graph(G_event_only, partition = filtered_best_event_partition, save_path = f'{output_graph_dir}/png/{partition_method}_{dataset_name}_{phase}_{instance_index}_hop_{hop_num}_discount_{DISCOUNT}_cluster_{highest_score_cluster_num}.png')
                elif partition_method == 'spectral_clustering':
                    visualize_instance_graph(G_event_only, partition = filtered_best_event_partition, save_path = f'{output_graph_dir}/png/{partition_method}_{dataset_name}_{phase}_{instance_index}_hop_{hop_num}_discount_{DISCOUNT}_cluster_{highest_score_cluster_num}.png')
                
                '''convert to UoF format json'''
                # add_event_node_group_attr(G_event_only, filtered_best_event_partition)
                # convert_to_UoF_format(G_event_only, using_group = True, output_json_path = f'./vis_json_UoF/{partition_method}_UoF_json_{dataset_name}_{phase}_{instance_index}_cluster_{highest_score_cluster_num}.json')
