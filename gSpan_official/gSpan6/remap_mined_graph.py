import json
import os
import argparse
import networkx as nx 
import numpy as np
from os import listdir
from os.path import isfile, join
from networkx.algorithms import components 
from collections import defaultdict


def map_index_to_type(original_fp_path, output_remapped_fp_path,node_type_dict_json, edge_type_dict_json):
    index_to_node_type = json.load(open(node_type_dict_json))
    index_to_edge_type = json.load(open(edge_type_dict_json))
    
    with open(output_remapped_fp_path,'w') as out:
        with open(original_fp_path) as f:
            for line in f:
                if line.startswith('t'):
                    out.write(line)
                elif line.startswith('v'):
                    parsed_node_line = line.strip().split(' ')
                    node_type = index_to_node_type[parsed_node_line[2]]
                    new_node_line = f'v {parsed_node_line[1]} {node_type}\n'
                    out.write(new_node_line)

                elif line.startswith('e'):
                    parsed_edge_line = line.strip().split(' ')
                    edge_type = index_to_edge_type[parsed_edge_line[3]]
                    new_edge_line = f'e {parsed_edge_line[1]} {parsed_edge_line[2]} {edge_type}\n'
                    out.write(new_edge_line)
                else:
                    out.write('\n')



parser = argparse.ArgumentParser(description='Remap gSpan official format index to node/edge types')
parser.add_argument('-ifp', '--input_fp_file', help='input_fp_file', required=True)
parser.add_argument('-in', '--input_node_map_json', help='input_node_map_json', required=True)
parser.add_argument('-ie', '--input_edge_map_json', help='input_edge_map_json', required=True)
# parser.add_argument('-o', '--output_path', help='Output folder path', required=True)

args = vars(parser.parse_args())


original_fp_path = args['input_fp_file']
node_type_dict_json = args['input_node_map_json']
edge_type_dict_json = args['input_edge_map_json']
out_path = original_fp_path[:-3] + '.remapped.fp'
# original_fp_path = '/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/gSpan_official/gSpan6/graphData_event_only/suicide_ied_train/suicide_ied_train_graphDataset_gspan_official.data.fp'
# node_type_dict_json = '/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/gSpan_official/gSpan6/graphData_event_only/suicide_ied_train/suicide_ied_train_node_type_index_dict.json'
# edge_type_dict_json = '/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/gSpan_official/gSpan6/graphData_event_only/suicide_ied_train/suicide_ied_train_edge_type_index_dict.json'
# out_path = '/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/gSpan_official/gSpan6/graphData_event_only/suicide_ied_train/mined_fp_remapped.fp'

map_index_to_type(original_fp_path,out_path,node_type_dict_json,edge_type_dict_json)
