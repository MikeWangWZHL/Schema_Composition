import sklearn
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.cluster import SpectralClustering
from collections import defaultdict

from create_graph import create_nx_graph_Event_Only, create_nx_graph_Event_and_Argument

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


def spectral_clustering(G, weight_keyword = 'score', cluster_num = 2, save_visualization_path = None, show_all_nodes = False):
    '''Matrix creation'''
    # TODO edge score becomes entries in the adj matrix
    adj_matrix = nx.to_numpy_matrix(G, weight = 'score') #Converts graph to an adj matrix with adj_matrix[i][j] represents weight between node i,j.
    node_list = list(G.nodes()) #returns a list of nodes with index mapping with the a 

    '''Spectral Clustering'''
    clusters = SpectralClustering(affinity = 'precomputed', assign_labels="discretize", random_state=0, n_clusters = cluster_num).fit_predict(adj_matrix)
    
    '''vis only event nodes'''
    plt.rcParams["figure.figsize"] = (int(0.5*len(node_list)),int(0.5*len(node_list)))

    if not show_all_nodes:
        event_nodes_id_plus_type_list = []
        event_clusters = []
        count_dict = defaultdict(int)
        for i in range(len(node_list)):
            n_id = node_list[i]
            if G.nodes[n_id]['category'] == 'Event':
                node_type_abbr = G.nodes[n_id]['type'].split('.')[1]
                node_str = node_type_abbr + '_' + str(count_dict[node_type_abbr])
                event_nodes_id_plus_type_list.append(node_str)
                event_clusters.append(clusters[i])
                count_dict[node_type_abbr] += 1
        plt.scatter(event_nodes_id_plus_type_list,event_clusters,s = 20*len(event_nodes_id_plus_type_list),c=event_clusters, cmap='viridis')
    else:
        plt.scatter(node_list,clusters,c=clusters, s=50, cmap='viridis')

    if save_visualization_path is not None:
        print('save clustering scatter at :', save_visualization_path)
        plt.savefig(save_visualization_path)
    
    '''return partition'''
    assert len(node_list) == len(clusters)
    community_dict = defaultdict(list)
    for i in range(len(node_list)):
        node_id = node_list[i]
        cluster_id = clusters[i]
        community_dict[cluster_id].append(node_id)

    return [c for c in community_dict.values()]

if __name__ == '__main__':
    
    '''Graph creation and initialization'''
    G = create_mini_example_graph_1()
    
    partition = spectral_clustering(G, cluster_num = 3)
    print(partition)

