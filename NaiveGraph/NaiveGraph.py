import networkx as nx 
from networkx.algorithms import isomorphism

# create some graph dataset as example for testing
from data import create_sample_graph_dataset_1, create_sample_graph_dataset_2

"""set up node matcher and edge matcher"""
NODE_MATCHER_FUNC = isomorphism.categorical_node_match("label",None)
EDGE_MATCHER_FUNC = isomorphism.categorical_edge_match("label",None)

"""set up min support"""
MIN_SUP = 3


def is_frequent(g,D,min_sup):
    '''check if a candidate graph g is frequent in dataset D'''
    count = 0
    for G in D:
        dgmather = isomorphism.DiGraphMatcher(G,g,node_match = NODE_MATCHER_FUNC, edge_match = EDGE_MATCHER_FUNC)
        if dgmather.subgraph_is_isomorphic():
            count += 1
    if count >= min_sup:
        return True
    else:
        return False

def is_equal(G1,G2):
    '''check if two DiGraph are isomorphism'''
    dgmather = isomorphism.DiGraphMatcher(G1,G2,node_match = NODE_MATCHER_FUNC, edge_match = EDGE_MATCHER_FUNC)
    return dgmather.is_isomorphic()

def if_exist(g,S):
    '''check if g's isomorphism already exist in S'''
    for existing_g in S:
        if is_equal(g,existing_g):
            return True
    return False

def get_candidates(g,D,min_sup):
    candidate_new_gs = []
    for G in D:
        dgmather = isomorphism.DiGraphMatcher(G,g,node_match = NODE_MATCHER_FUNC, edge_match = EDGE_MATCHER_FUNC)

        for mapping in dgmather.subgraph_isomorphisms_iter():

            cand_edges_tuples = [] # store candidates in format eg: [((0,1,{'label':'a'}),case = "add new node",new_node_attr), ... ]

            for e in G.out_edges(nbunch = mapping.keys(),data=True):
                if e[1] not in mapping:
                    case = "add new node"
                    new_node_attr = G.nodes[e[1]]
                    cand_edges_tuples.append((e,case,new_node_attr))
                else:
                    if not g.has_edge(mapping[e[0]],mapping[e[1]]):
                        case = "add new edge"
                        cand_edges_tuples.append((e,case))
            for cand_edge_tuple in cand_edges_tuples:
                # expend g for every possible edge e
                if cand_edge_tuple[1] == 'add new node':
                    e = cand_edge_tuple[0]
                    new_node_attribute = cand_edge_tuple[2]

                    new_g = g.copy()
                    new_node_id = 'g_' + str(e[1])
                    new_g.add_nodes_from([(new_node_id,new_node_attribute)])
                    new_g.add_edges_from([(mapping[e[0]],new_node_id,e[2])])
                else:
                    e = cand_edge_tuple[0]
                    new_g = g.copy()
                    new_g.add_edges_from([(mapping[e[0]],mapping[e[1]],e[2])])
                
                # check if the expended new_g is frequent               
                if is_frequent(new_g,D,min_sup):  
                    # check if already added its isomorphism into candidate gs
                    if not if_exist(new_g,candidate_new_gs):
                        candidate_new_gs.append(new_g)

    return candidate_new_gs

def find_single_node_frequent_gs(D,min_sup):
    frequent_single_node_gs = []
    
    for G in D:
        for node in G.nodes().data():
            node_id = node[0]
            new_node_id = 'g_' + str(node_id)
    
            g = nx.DiGraph()
            g.add_nodes_from([(new_node_id,node[1])])
    
            if is_frequent(g,D,min_sup):
                if not if_exist(g,frequent_single_node_gs):
                    frequent_single_node_gs.append(g)

    return frequent_single_node_gs

'''Naive Graph Algorithm'''
def naive_graph_recursive(g,D,min_sup,S):
    '''naive graph recursive part'''
    if if_exist(g,S):
        return
    else:
        S.append(g)
    
    cand_gs = get_candidates(g,D,min_sup)
    for cg in cand_gs:
        naive_graph_recursive(cg,D,min_sup,S)
    return

def naive_graph_main(D,min_sup):
    '''naive graph main function'''
    S = []
    single_node_g = find_single_node_frequent_gs(D,min_sup)
    for sg in single_node_g:
        naive_graph_recursive(sg,D,min_sup,S)
    return S


""" test """
# D = create_sample_graph_dataset_1()
D = create_sample_graph_dataset_2()
print('======= Graph dataset =======')
for G in D:
    print("Nodes: ", G.nodes().data())
    print("Edges: ", G.edges().data())
    print('================')
print('=============================')

# sample subgraph g
    # g = nx.DiGraph()
    # g.add_nodes_from([
    #     ('g_0',{'label':'A'}),
    #     ('g_1',{'label':'B'})
    # ])
    # g.add_edges_from([
    #     ('g_0','g_1')
    # ],label = 'a')
    # print('candidate subgraph g:')
    # print("Nodes: ", g.nodes().data())
    # print("Edges: ", g.edges().data())
    # print('=============================')
    # print()



"""set up DiGraphMatcher"""
print(f"using min support: {MIN_SUP}\n")

# unit tests:
    # dgmather = isomorphism.DiGraphMatcher(D[0],g,node_match = NODE_MATCHER_FUNC, edge_match = EDGE_MATCHER_FUNC)
    # print('is subgraph? ', dgmather.subgraph_is_isomorphic())
    # print()
    # print('all subgraph mapping: ')
    # for subgraph in dgmather.subgraph_isomorphisms_iter():
    #     print(subgraph)
    # print()

    # print('is g frequent? ', is_frequent(g,D,MIN_SUP))
    # print()

    # for cand_g in get_candidates(g,D,MIN_SUP):
        
    #     print('****** cand g ******')
    #     print("Nodes: ", cand_g.nodes().data())
    #     print("Edges: ", cand_g.edges().data())
    # print()

    # for sg in find_single_node_frequent_gs(D,MIN_SUP):
    #     print('****** frequent single node g ******')
    #     print("Nodes: ", sg.nodes().data())
    # print()

FSGs = naive_graph_main(D,MIN_SUP)
print(f'found {len(FSGs)} frequent subgraphs')
for fsg in FSGs:
    print('****** frequent subgraph ******')
    print("Nodes: ", fsg.nodes().data())
    print("Edges: ", fsg.edges().data())
print()

# for edge in D[0].out_edges(nbunch = dicts.keys(),data=True):
#     print(edge)
# G1_other = nx.DiGraph()
# G1_other.add_nodes_from([
#         (1,{'label':'A'}),
#         (2,{'label':'B'}),
#         (3,{'label':'D'}),
#         (4,{'label':'C'})
#     ])
# G1_other.add_edges_from([
#         (1,2),
#         (2,3),
#         (1,4),
#         (4,3)
#     ],label='a')
# tempmatcher = isomorphism.DiGraphMatcher(D[0],G1_other,node_match = NODE_MATCHER_FUNC, edge_match = EDGE_MATCHER_FUNC)
# print(tempmatcher.is_isomorphic())