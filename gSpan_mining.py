# from mygspan_config import parser
# from mygspan_main import main
from gspan_mining.config import parser
from gspan_mining.main import main

def find_dataset_size(graph_dataset_file):
    max_count = 0
    with open(graph_dataset_file) as f:
        for line in f:
            if line.startswith('t'):
                count = int(line.strip().split(' ')[2])
                if count > max_count:
                    max_count = count
    return max_count+1


'''set hyperparameter'''
dataset_name = 'suicide_ied_train'
# dataset_name = 'suicide_ied_test'
# dataset_name = 'wiki_drone_strikes_test'
# dataset_name = 'wiki_ied_bombings_test'
# dataset_name = 'wiki_mass_car_bombings_test'
# dataset_name = 'mini_sample'
if_use_connected_component_dataset = False
if_use_largest_connected_component_dataset = False
if_directed = True
if_use_event_only = True
if_upperbound_mining_number = False

if if_use_event_only:
    case = '_event_only'
else:
    case = ''

if if_use_connected_component_dataset:
    if if_use_largest_connected_component_dataset:
        graph_dataset = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData_largest_connected_component/{dataset_name}_graphDataset_CC.data'
        output_path = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/mined_graphs_largest_connected_component/{dataset_name}_frequentSubgraphs_CC.data'
    else:
        graph_dataset = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData_connected_component/{dataset_name}_graphDataset_CC.data'
        output_path = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/mined_graphs_connected_component/{dataset_name}_frequentSubgraphs_CC.data'
else:
    if if_use_largest_connected_component_dataset:
        graph_dataset = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData{case}_largest_connected_component/{dataset_name}_graphDataset.data'
        output_path = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/mined_subgraphs{case}_largest_connected_component/{dataset_name}_frequentSubgraphs.data'
    else:
        graph_dataset = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graphData{case}/{dataset_name}_graphDataset.data'
        output_path = f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/mined_subgraphs{case}/{dataset_name}_frequentSubgraphs.data'

print()

dataset_size = find_dataset_size(graph_dataset)
print(f'start mining {dataset_name} ...')
print('dataset size: ', dataset_size)

min_support = int(dataset_size*0.5)
print('using min_sup: ', min_support)

upper_num_vertex = 5
print('using upper bound number of vertex: ', upper_num_vertex)
# max_subgraph = 50
# print('max mining number: ',max_subgraph)


if if_directed:
    print('using gspan directed')
    args_str = f'-s {min_support} -d True -u {upper_num_vertex} {graph_dataset}'
else:
    print('using gspan undirected')
    args_str = f'-s {min_support} -u {upper_num_vertex} {graph_dataset}'
        
FLAGS, _ = parser.parse_known_args(args=args_str.split())

'''run gspan'''
gs = main(FLAGS)
# print()
# print(f'found {len(gs._frequent_subgraphs)} frequent subgraphs')
# print('====== frequent subgraphs =======')
# print(gs._frequent_subgraphs)
# print('====== support =======')
# print(gs._report_df['support'].tolist())

print()
print('=============')
print()

print('dataset size: ', dataset_size)
print('using min_sup: ', min_support)
print(f'found {len(gs._frequent_subgraphs)} frequent subgraphs')
print(f'upper bound vertex: {upper_num_vertex}')
if len(gs._frequent_subgraphs) == 0:
    print('no frequent subgraph found, exit without writing result to file...')
    quit()
support_list = gs._report_df['support'].tolist()
with open(output_path,'w') as out:
    assert len(support_list) == len(gs._frequent_subgraphs)
    for fsg_i in range(len(gs._frequent_subgraphs)):
        fsg_dfscode = gs._frequent_subgraphs[fsg_i]
        node_label_dict = {}
        edge_tuple_strs = []
        for five_tuple in fsg_dfscode:
            frm, to, (vlb1, elb, vlb2) = five_tuple.frm, five_tuple.to, five_tuple.vevlb
            if frm not in node_label_dict:
                node_label_dict[frm] = vlb1
            if to not in node_label_dict:
                node_label_dict[to] = vlb2
            edge_str = f'({frm}, {to}, ({node_label_dict[frm]}, {elb}, {node_label_dict[to]}))'
            edge_tuple_strs.append(edge_str)
        graph_line = ''
        for edge_str in edge_tuple_strs:
            graph_line = graph_line + edge_str + ';'
        graph_line = graph_line + f' || support = {support_list[fsg_i]}'
        graph_line += '\n'
        out.write(graph_line)
