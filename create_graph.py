import networkx as nx 
import numpy as np
from data import *
import os
from os import listdir
from os.path import isfile, join
from networkx.algorithms import components 
from collections import defaultdict
import json

def create_nx_graph_Event_Only(input_dict):
    # only consider Event nodes and Temporal edges
    graph_g = Graph.from_dict(input_dict)
    graph_nx = nx.DiGraph(name = graph_g.schemas[0].at_id)
    nodes_list = []
    for step in graph_g.schemas[0].steps:
        nodes_list.append((step.at_id,step.at_type.split('/')[-1].strip()))
    edges_list = []
    for order in graph_g.schemas[0].order:
        edges_list.append((order.before, order.after))
    for node in nodes_list:
        graph_nx.add_node(node[0],type = node[1])
    graph_nx.add_edges_from(edges_list, type = 'Temporal_Order')
    
    return graph_nx

def create_nx_graph_Event_and_Argument(input_dict):
    # consider Event nodes and Arguments
    graph_g = Graph.from_dict(input_dict)
    graph_nx = nx.DiGraph(name = graph_g.schemas[0].at_id)

    # add event nodes and temporal edges
    event_nodes_list = []
    for step in graph_g.schemas[0].steps:
        event_nodes_list.append((step.at_id,step.at_type.split('/')[-1].strip()))
    event_edges_list = []
    for order in graph_g.schemas[0].order:
        event_edges_list.append((order.before, order.after))
    for node in event_nodes_list:
        graph_nx.add_node(node[0],type = node[1])
    graph_nx.add_edges_from(event_edges_list, type = 'Temporal_Order')
    
    # add entity nodes
    entity_nodes_list = []
    for entity in graph_g.schemas[0].entities:
        entity_nodes_list.append((entity.at_id,entity.entity_types.split('/')[-1].strip()))
    for node in entity_nodes_list:
        graph_nx.add_node(node[0],type = node[1])

    # add argument edges 
    argument_edges_list = []
    for step in graph_g.schemas[0].steps:
        event_node_id = step.at_id
        for arg in step.participants:
            entity_node_id = arg.values[0].entity
            role_type = arg.role.split('/')[-1].strip()
            argument_edges_list.append((event_node_id,entity_node_id,role_type))
    for arg_edge in argument_edges_list:
        u = arg_edge[0]
        v = arg_edge[1]
        arg_role_type = arg_edge[2]
        graph_nx.add_edge(u,v,type = arg_role_type)

    # add relation edges
    relation_edges_list = []
    for rel in graph_g.schemas[0].entity_relations:
        from_entity = rel.relation_subject
        to_entity = rel.relations.relation_object
        rel_type = rel.relations.relation_predicate.split('/')[-1].strip()
        relation_edges_list.append((from_entity,to_entity,rel_type))
    for rel_edge in relation_edges_list:
        u = rel_edge[0]
        v = rel_edge[1]
        rel_edge_type = rel_edge[2]
        graph_nx.add_edge(u,v,type = rel_edge_type) 

    return graph_nx

def convert_nxgraph_to_gspan_python_format(nx_graphs,output_path):
    
    with open(output_path, 'w') as f:
        for i in range(len(nx_graphs)):
            nx_graph = nx_graphs[i]
            # construct node lines and edge lines 
            node_lines = []
            edge_lines = []

            for node in nx_graph.nodes().data():
                node_type = node[1]['type']
                add_node_line = f'v {node[0]} {node_type}\n'
                node_lines.append(add_node_line)
            
            for edge in nx_graph.edges().data():
                edge_type = edge[2]['type']
                add_edge_line = f'e {edge[0]} {edge[1]} {edge_type}\n'
                edge_lines.append(add_edge_line)

            # write to file
            graph_index_line = f't # {i}\n'
            f.write(graph_index_line)
            for node_line in node_lines:
                f.write(node_line)
            for edge_line in edge_lines:
                f.write(edge_line)
        
        # write last line
        f.write('t # -1')

def convert_nxgraph_to_gspan_official_format(nx_graphs, output_dir_path, dataset_name = 'temp'):
    node_type_to_index = {}
    edge_type_to_index = {}

    dataset_output_name = dataset_name + '_graphDataset_gspan_official.data'
    output_dataset_path = join(output_dir_path,dataset_output_name)

    with open(output_dataset_path, 'w') as f:
        for i in range(len(nx_graphs)):
            node_id_to_index = {}
            
            nx_graph = nx_graphs[i]
            # construct node lines and edge lines 
            node_lines = []
            edge_lines = []

            for node in nx_graph.nodes().data():
                node_type = node[1]['type']

                if node_type not in node_type_to_index:
                    node_type_to_index[node_type] = len(node_type_to_index)
                node_type_idx = node_type_to_index[node_type]

                assert node[0] not in node_id_to_index
                node_id_to_index[node[0]] = len(node_id_to_index)

                add_node_line = f'v {node_id_to_index[node[0]]} {node_type_idx}\n'
                node_lines.append(add_node_line)
            
            for edge in nx_graph.edges().data():

                edge_type = edge[2]['type']

                if edge_type not in edge_type_to_index:
                    edge_type_to_index[edge_type] = len(edge_type_to_index)
                edge_type_idx = edge_type_to_index[edge_type]

                add_edge_line = f'e {node_id_to_index[edge[0]]} {node_id_to_index[edge[1]]} {edge_type_idx}\n'
                edge_lines.append(add_edge_line)

            # write to file
            graph_index_line = f't # {i}\n'
            f.write(graph_index_line)
            for node_line in node_lines:
                f.write(node_line)
            for edge_line in edge_lines:
                f.write(edge_line)

    index_to_node_type = {value:key for key,value in node_type_to_index.items()}
    index_to_edge_type = {value:key for key,value in edge_type_to_index.items()}

    output_node_type_dict_path = join(output_dir_path,f'{dataset_name}_node_type_index_dict.json')
    output_edge_type_dict_path = join(output_dir_path,f'{dataset_name}_edge_type_index_dict.json')
    output_type_frequency_dict_path = join(output_dir_path,f'{dataset_name}_type_frequency_dict.json')

    with open(output_node_type_dict_path, 'w') as out_node_dict:
        json.dump(index_to_node_type, out_node_dict,indent=4)

    with open(output_edge_type_dict_path, 'w') as out_edge_dict:
        json.dump(index_to_edge_type, out_edge_dict,indent=4)

    # write type frequency dict
    type_fre_dict = check_event_type_frequency(nx_graphs)
    with open(output_type_frequency_dict_path, 'w') as out_fre_dict:
        json.dump(type_fre_dict, out_fre_dict,indent=4)
    

def check_event_type_frequency(nx_g_dataset):
    count_dict = defaultdict(int)
    for nx_g in nx_g_dataset:
        type_set = set()
        for node in nx_g.nodes.data():
            type_set.add(node[1]["type"])
        # print('==============================')
        # print(type_set)
        # print('==============================')
        for t in type_set:
            count_dict[t] += 1
    # print(count_dict)
    frequent_dict = {}
    for key,value in count_dict.items():
        assert key not in frequent_dict
        frequent_dict[key] = value/len(nx_g_dataset)
    # print(frequent_dict)
    return frequent_dict



def get_connected_components(G):
    S = [G.subgraph(c).copy() for c in nx.weakly_connected_components(G)]
    return S

def get_connected_component_dataset(nx_g_dataset):
    CCs = []
    for nx_g in nx_g_dataset:
        CC = get_connected_components(nx_g)
        for cc in CC:
            CCs.append(cc)
    return CCs

def get_largest_connected_component_dataset(nx_g_dataset):
    CCs = []
    for nx_g in nx_g_dataset:
        largest_cc = max(nx.weakly_connected_components(nx_g), key=len)
        CCs.append(nx_g.subgraph(largest_cc).copy())
    return CCs

'''unit test'''
# doc = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/test/suicide_ied_test.json'
# g_dicts = []
# with open(doc) as f:
#     for line in f:
#         g_dicts.append(json.loads(line))
# sample_g = create_nx_graph_Event_and_Argument(g_dicts[3])
# # sample_g = create_nx_graph_Event_Only(g_dicts[0])
# print()
# print("graph name: ", sample_g.graph)
# print()
# print('Nodes: ', sample_g.nodes().data())
# print()
# print('Edges: ',sample_g.edges().data())
# print()

# cycles = []
# try:
#     cycles = nx.find_cycle(G, orientation="original")
# except:
#     print('found no cycles')
#     pass

# print('cycle numbers: ', len(list(cycles)))
# # CC = get_connected_components(sample_g)
# # print('number of CC: ', len(CC))
# quit()


'''main functions'''
def create_graph_dataset_gspan_python():

    train_path = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/train'
    test_path = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/test'
    train_docs = [f for f in listdir(train_path) if isfile(join(train_path, f))]
    test_docs = [f for f in listdir(test_path) if isfile(join(test_path, f))]
    train_docs.sort()
    test_docs.sort()

    '''set config'''
    # using_doc = test_docs
    # using_path = test_path
    using_doc = train_docs
    using_path = train_path
    if_use_event_only = True
    if_use_connected_component_dataset = False
    if_use_largest_connected_component_dataset = False

    for i in range(len(using_doc)):
        print('==================================================')
        print(f'using graph dataset: {using_doc[i]} ...')
        

        # load train graph gs
        input_graphs_path_train = join(using_path,using_doc[i])
        input_graph_dicts_train = []
        with open(input_graphs_path_train) as f:
            for line in f:
                input_graph_dicts_train.append(json.loads(line))

        # unit test: 
        # sample_g = create_nx_graph_Event_Only(input_graph_dicts_train[0])
        # sample_g = create_nx_graph_Event_and_Argument(input_graph_dicts_train[0])
        # print()
        # print("graph name: ", sample_g.graph)
        # print()
        # print('Nodes: ', sample_g.nodes().data())
        # print()
        # print('Edges: ',sample_g.edges().data())
        # print()
        nx_graph_dataset = []
        for g_dict in input_graph_dicts_train:
            if if_use_event_only:
                nx_g = create_nx_graph_Event_Only(g_dict)
            else:
                nx_g = create_nx_graph_Event_and_Argument(g_dict)
            nx_graph_dataset.append(nx_g)
        print(f'original dataset size: {len(nx_graph_dataset)}')
        dataset_name = using_doc[i].split('.json')[0].strip()
        
        if if_use_event_only:
            case = '_event_only'
        else:
            case = ''

        if if_use_connected_component_dataset:
            if if_use_largest_connected_component_dataset:
                nx_graph_dataset_CC = get_largest_connected_component_dataset(nx_graph_dataset)
                print(f'largest connected component dataset size: {len(nx_graph_dataset_CC)}') 
                convert_nxgraph_to_gspan_python_format(nx_graph_dataset_CC, f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData_largest_connected_component/{dataset_name}_graphDataset_CC.data')

            else:
                nx_graph_dataset_CC = get_connected_component_dataset(nx_graph_dataset)
                print(f'connected component dataset size: {len(nx_graph_dataset_CC)}') 
                convert_nxgraph_to_gspan_python_format(nx_graph_dataset_CC, f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData_connected_component/{dataset_name}_graphDataset_CC.data')
        else:
            if if_use_largest_connected_component_dataset:
                nx_graph_dataset_CC = get_largest_connected_component_dataset(nx_graph_dataset)
                print(f'largest connected component event only dataset size: {len(nx_graph_dataset_CC)}') 
                convert_nxgraph_to_gspan_python_format(nx_graph_dataset_CC, f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData{case}_largest_connected_component/{dataset_name}_graphDataset.data')
            else:
                convert_nxgraph_to_gspan_python_format(nx_graph_dataset, f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData{case}/{dataset_name}_graphDataset.data')

        



        # g1 = create_nx_graph(merged_train_input_g)
        # print('train node number: ',g1.number_of_nodes())
        # print('train edge number: ',g1.number_of_edges())
        
        # g2 = create_nx_graph(merged_test_input_g)
        # print('test node number: ',g2.number_of_nodes())
        # print('test edge number: ',g2.number_of_edges())
        # # print(g1.nodes.data())
        # time_limit = 10
        # result = nx.graph_edit_distance(g1,g2,node_match = node_match_fn, timeout = time_limit)
        # print(f'approximated GED with time limit {time_limit}: ', result)

def create_graph_dataset_gspan_official(dataset_case = 'train'):

    train_path = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/train'
    test_path = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/test'
    train_docs = [f for f in listdir(train_path) if isfile(join(train_path, f))]
    test_docs = [f for f in listdir(test_path) if isfile(join(test_path, f))]
    train_docs.sort()
    test_docs.sort()

    '''set config'''
    if dataset_case == 'train':
        using_doc = train_docs
        using_path = train_path
    else:
        using_doc = test_docs
        using_path = test_path

    if_use_event_only = True
    if_use_connected_component_dataset = False
    if_use_largest_connected_component_dataset = False

    for i in range(len(using_doc)):
        print('==================================================')
        print(f'using graph dataset: {using_doc[i]} ...')
        

        # load train graph gs
        input_graphs_path_train = join(using_path,using_doc[i])
        input_graph_dicts_train = []
        with open(input_graphs_path_train) as f:
            for line in f:
                input_graph_dicts_train.append(json.loads(line))

        # unit test: 
        # sample_g = create_nx_graph_Event_Only(input_graph_dicts_train[0])
        # sample_g = create_nx_graph_Event_and_Argument(input_graph_dicts_train[0])
        # print()
        # print("graph name: ", sample_g.graph)
        # print()
        # print('Nodes: ', sample_g.nodes().data())
        # print()
        # print('Edges: ',sample_g.edges().data())
        # print()

        nx_graph_dataset = []
        for g_dict in input_graph_dicts_train:
            if if_use_event_only:
                nx_g = create_nx_graph_Event_Only(g_dict)
            else:
                nx_g = create_nx_graph_Event_and_Argument(g_dict)
            
            nx_graph_dataset.append(nx_g)
        

        print(f'original dataset size: {len(nx_graph_dataset)}')


        dataset_name = using_doc[i].split('.json')[0].strip()
        
        if if_use_event_only:
            case = '_event_only'
        else:
            case = ''

        if if_use_connected_component_dataset:
            print('not implemented!')
            # if if_use_largest_connected_component_dataset:
            #     nx_graph_dataset_CC = get_largest_connected_component_dataset(nx_graph_dataset)
            #     print(f'largest connected component dataset size: {len(nx_graph_dataset_CC)}') 
            #     convert_nxgraph_to_gspan_official_format(nx_graph_dataset_CC, f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData_largest_connected_component/{dataset_name}_graphDataset_CC.data')

            # else:
            #     nx_graph_dataset_CC = get_connected_component_dataset(nx_graph_dataset)
            #     print(f'connected component dataset size: {len(nx_graph_dataset_CC)}') 
            #     convert_nxgraph_to_gspan_official_format(nx_graph_dataset_CC, f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData_connected_component/{dataset_name}_graphDataset_CC.data')
        else:
            if if_use_largest_connected_component_dataset:
                print('not implemented')
                # nx_graph_dataset_CC = get_largest_connected_component_dataset(nx_graph_dataset)
                # print(f'largest connected component event only dataset size: {len(nx_graph_dataset_CC)}') 
                # convert_nxgraph_to_gspan_official_format(nx_graph_dataset_CC, f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData{case}_largest_connected_component/{dataset_name}_graphDataset.data')
            else:
                rootpath = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/gSpan_official/gSpan6/graphData{case}'
                dataset_subpath = join(rootpath,dataset_name)
                if not os.path.isdir(dataset_subpath):
                    os.mkdir(dataset_subpath)
                convert_nxgraph_to_gspan_official_format(nx_graph_dataset, dataset_subpath, dataset_name = dataset_name)



'''usage'''
print('call create graph func in gspan official format... ')
create_graph_dataset_gspan_official(dataset_case = 'test')
