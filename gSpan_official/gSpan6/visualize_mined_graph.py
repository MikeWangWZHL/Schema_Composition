import json
import os
import argparse
import networkx as nx 
import numpy as np
from os import listdir
from os.path import isfile, join
from networkx.algorithms import components 
from collections import defaultdict
import matplotlib.pyplot as plt
import math
from filter_mined_graph import filter_mined_nx_subgraphs
import pickle

def get_single_subgraph_nx(frequent_subgraph_lines):
    '''
        create graph from gSpan data format
    '''
    graph_id = frequent_subgraph_lines[0].strip().split(' ')[2]
    support = frequent_subgraph_lines[0].strip().split(' ')[4]
    graph_nx = nx.DiGraph(name = graph_id)

    for line in frequent_subgraph_lines[1:]:
        if line.startswith('v'):
            parsed_line = line.strip().split(' ')
            node_id = parsed_line[1]
            node_type = parsed_line[2]
            graph_nx.add_node(node_id,type = node_type)

        elif line.startswith('e'):
            parsed_line = line.strip().split(' ')
            node_from = parsed_line[1]
            node_to = parsed_line[2]
            edge_type = parsed_line[3]
            graph_nx.add_edge(node_from,node_to,type=edge_type)
    
    return graph_nx
            
def get_subgraphs_nx(remapped_fp_file):
    fsg_lines_list = []
    fsg_lines = []
    with open(remapped_fp_file) as f:
        for line in f:
            if line == '\n' and fsg_lines != []:
                fsg_lines_list.append(fsg_lines)
                fsg_lines = []
            else:
                fsg_lines.append(line)
    
    nx_subgraphs = []
    for fsg_ls in fsg_lines_list:
        nx_subgraphs.append(get_single_subgraph_nx(fsg_ls))

    return nx_subgraphs

def graphData_to_nx_single(graphData_single_lines):
    graph_id = graphData_single_lines[0].strip().split(' ')[2]
    graph_nx = nx.DiGraph(name = graph_id)

    for line in graphData_single_lines[1:]:
        if line.startswith('v'):
            parsed_line = line.strip().split(' ')
            node_id = parsed_line[1]
            node_type = parsed_line[2]
            graph_nx.add_node(node_id,type = node_type)

        elif line.startswith('e'):
            parsed_line = line.strip().split(' ')
            node_from = parsed_line[1]
            node_to = parsed_line[2]
            edge_type = parsed_line[3]
            graph_nx.add_edge(node_from,node_to,type=edge_type)
    
    return graph_nx

def graphData_to_nx(graphData_file):
    g_lines_list = []
    g_lines = []
    with open(graphData_file) as f:
        for line in f:
            if line.startswith('t') and g_lines != []:
                g_lines_list.append(g_lines)
                g_lines = []
                g_lines.append(line)
            else:
                g_lines.append(line)
        if g_lines != []:
            g_lines_list.append(g_lines)
    nx_subgraphs = []
    for g_ls in g_lines_list:
        nx_subgraphs.append(graphData_to_nx_single(g_ls))

    return nx_subgraphs

def draw_subgraphs(nx_subgraphs, save_path, if_show_edge_type = False, show_max = None):
    if show_max is None:
        nrows = int(math.sqrt(len(nx_subgraphs)))+1
    else:
        nrows = int(math.sqrt(int(show_max)))+1

    fig, axes = plt.subplots(nrows=nrows, ncols=nrows, figsize = (5*nrows,5*nrows))
    fig.tight_layout()
    ax = axes.flatten()

    for i in range(nrows*nrows):
        if i < len(nx_subgraphs):
            
            # nx.draw(nx_subgraphs[i], ax=ax[i], node_size = 5)
            # draw_single_subgraph(nx_subgraphs[i], ax[i])
            G = nx_subgraphs[i]
            pos = nx.spring_layout(G)
            # pos = nx.shell_layout(G)
            nx.draw(G, pos, ax = ax[i], alpha = 0.7, arrowsize = 12)
            node_labels = nx.get_node_attributes(G,'type')
            nx.draw_networkx_labels(G, pos, ax = ax[i],labels = node_labels,font_size = 10)
            if if_show_edge_type:
                edge_labels = nx.get_edge_attributes(G,'type')
                nx.draw_networkx_edge_labels(G, pos,edge_labels,ax = ax[i],font_size = 10)
            
            ax[i].set_xlim([1.5*x for x in ax[i].get_xlim()])
            ax[i].set_ylim([1.5*y for y in ax[i].get_ylim()])
            # ax[i].set_xlim(0,10)

        ax[i].set_axis_off()
    fig.savefig(save_path)
    print(f'saved visualization to {save_path}')

def draw_single_subgraph(G, ax, save_path = None):
    # f = plt.figure()

    pos = nx.spring_layout(G)
    
    nx.draw(G, pos, ax = ax)
    
    node_labels = nx.get_node_attributes(G,'type')
    nx.draw_networkx_labels(G, pos, labels = node_labels)
    edge_labels = nx.get_edge_attributes(G,'type')
    nx.draw_networkx_edge_labels(G, pos, edge_labels)
    
    if save_path is not None:
        x_values, y_values = zip(*pos.values())
        x_max = max(x_values)
        x_min = min(x_values)
        x_margin = (x_max - x_min) * 0.25
        plt.xlim(x_min - x_margin, x_max + x_margin)
        
        plt.savefig(save_path)
        print(f'saved visualization to {save_path}')

def write_graphs(nx_subgraphs, output_pickle_path):
    # Dump List of graphs
    with open(output_pickle_path, 'wb') as f:
        pickle.dump(nx_subgraphs, f)


def load_graphs(input_pickle_path):
    # Load List of graphs
    with open(input_pickle_path, 'rb') as f:
        return pickle.load(f)

'''arg parser'''
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='visualize remapped gSpan official frequent subgraphs')
    parser.add_argument('-i', '--input_fp_file', help='input remapped fp file path', default = None)
    parser.add_argument('-ig', '--input_graph_pickle', help='input remapped fp file path', default = None)
    
    parser.add_argument('-o', '--output_path', help='output visualization path', required=True)
    parser.add_argument('-og', '--output_graph_pickle_path', help='output_graph_pickle_path', default = None)
    parser.add_argument('-fil', '--if_filter', help='if filter subgraphs', default = True)
    parser.add_argument('-max', '--show_max', help='show max number of subgraphs', default = -1)

    args = vars(parser.parse_args())
    
    input_graph_pickle = args['input_graph_pickle']
    if_filter = args['if_filter']
    remapped_fp_path = args['input_fp_file']
    save_path = args['output_path']
    output_graph_pickle_path = args['output_graph_pickle_path']
    show_max = args['show_max']
    

    if input_graph_pickle is None and remapped_fp_path is None:
        print('ERROR: no input file!!!!')
        quit()

    '''usage'''
    if input_graph_pickle is not None:
        print('read from pickle ... ')
        nx_subgraphs = load_graphs(input_graph_pickle)
    else:
        nx_subgraphs = get_subgraphs_nx(remapped_fp_path)

    if if_filter and input_graph_pickle is None:
        nx_filtered_subgraphs = filter_mined_nx_subgraphs(nx_subgraphs, save_path = output_graph_pickle_path)
    # test converting correctness:
    # nx_gs = graphData_to_nx(remapped_fp_path)
    # print('dataset size: ',len(nx_gs))
    # for g in nx_gs:
    #     print(len(list(nx.simple_cycles(g))))
    # print('early quit ...')
    # quit()
    if show_max is not None:
        print(f'showing only {show_max} graphs')
    if if_filter and input_graph_pickle is None:
        print()
        print('number of filtered subgraphs: ', len(nx_filtered_subgraphs))
        print()
        draw_subgraphs(nx_filtered_subgraphs, save_path, show_max = show_max)
    else:
        print()
        print('number of subgraphs: ', len(nx_subgraphs))
        print()
        draw_subgraphs(nx_subgraphs, save_path, show_max = show_max)
        # draw_single_subgraph(nx_subgraphs[120], save_path)