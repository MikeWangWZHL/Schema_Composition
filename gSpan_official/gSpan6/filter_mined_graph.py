import networkx as nx 
from networkx.algorithms import isomorphism
import argparse
import pickle
from tqdm import tqdm
"""get nx graphs from remapped_fp_file"""
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

"""set up node matcher and edge matcher"""
NODE_MATCHER_FUNC = isomorphism.categorical_node_match("type",None)
EDGE_MATCHER_FUNC = isomorphism.categorical_edge_match("type",None)


def is_subgraph(g,G):
    '''check if g is a subgraph of G'''
    dgmather = isomorphism.DiGraphMatcher(G,g,node_match = NODE_MATCHER_FUNC, edge_match = EDGE_MATCHER_FUNC)
    if dgmather.subgraph_is_isomorphic():
        return True
    else:
        return False

def sort_nx_graphs(nx_graphs, order = 'increasing'):
    if order == 'increasing':
        return sorted(nx_graphs, key = lambda g: g.number_of_nodes())
    elif order == 'decreasing':
        return sorted(nx_graphs, key = lambda g: g.number_of_nodes(), reverse = True)
    else:
        raise NotImplementedError

def filter_mined_nx_subgraphs(nx_subgraphs, save_path = None):
    '''filter out mined subgraphs by which is a subgrpah in other mined subgraphs'''
    sorted_nx_graphs = sort_nx_graphs(nx_subgraphs, order = 'increasing')
    filtered_nx_graphs = []

    for i in tqdm(range(len(sorted_nx_graphs)-1)):
        g = sorted_nx_graphs[i]
        filtered_nx_graphs.append(g)
        for j in range(i+1,len(sorted_nx_graphs)):
            G = sorted_nx_graphs[j]
            if is_subgraph(g,G):
                filtered_nx_graphs.pop()
                break
    if save_path is not None:
        write_graphs(filtered_nx_graphs, save_path)
        print('write graphs to :', save_path)

    return filtered_nx_graphs

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
    # parser = argparse.ArgumentParser(description='filter mined subgraphs')
    parser.add_argument('-i', '--input_fp_file', help='input remapped fp file path', required=True)
    parser.add_argument('-o', '--output_path', help='write filtered graphs in pickle format', required=False, default = "")

    args = vars(parser.parse_args())

    remapped_fp_path = args['input_fp_file']
    save_path = args['output_path']


    '''usage'''

    nx_subgraphs = get_subgraphs_nx(remapped_fp_path)
    print('original frequent subgraph number: ', len(nx_subgraphs))
    filtered_nx_subgraphs = filter_mined_nx_subgraphs(nx_subgraphs)
    print('filtered frequent subgraph number: ', len(filtered_nx_subgraphs))

    if save_path != "":
        write_graphs(filtered_nx_subgraphs,save_path)
    
    # load graphs 
        # loaded_graphs = load_graphs('/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/gSpan_official/gSpan6/test_save.pickle')
        # print(isinstance(loaded_graphs,list))
        # print(len(loaded_graphs))
        # print(loaded_graphs[0].nodes.data())
