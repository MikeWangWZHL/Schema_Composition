import json
from create_graph import create_nx_graph_Event_Only, create_nx_graph_Event_and_Argument
from collections import defaultdict

def load_dataset(dataset_train_path):
    nx_dataset = []
    with open(dataset_train_path) as f:
        for line in f:
            g_dict = json.loads(line)
            nx_dataset.append(create_nx_graph_Event_Only(g_dict))
    print(f'loaded {len(nx_dataset)} instance graphs...\n')
    return nx_dataset

def calculate_p_e2_given_e1(nx_dataset):
    e2_start_with_e1 = defaultdict(lambda: defaultdict(int))
    for G in nx_dataset:
        for e1,e2,value in G.edges.data():
            e1_type = G.nodes[e1]['type']
            e2_type = G.nodes[e2]['type']
            e2_start_with_e1[e1_type][e2_type] += 1

    p_e2_given_e1 = defaultdict(lambda: defaultdict(float))
    for e1,e1_dict in e2_start_with_e1.items():
        total_edge_number_starts_with_e1 = 0
        for value in e1_dict.values():
            total_edge_number_starts_with_e1 += value
        for key,value in e1_dict.items():
            p_e2_given_e1[e1][key] = value/total_edge_number_starts_with_e1

    return p_e2_given_e1

# dataset_train_path = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/train/suicide_ied_train.json'
# nx_dataset = load_dataset(dataset_train_path)
# # calcuate_p_e1()
# # calcuate_p_e1_to_e2(nx_dataset)
# calculate_p_e2_given_e1(nx_dataset)

if __name__ == '__main__':
    outpath = '/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/conditional_probability_json'
    dataset_path = '/shared/nas/data/m1/wangz3/schema_induction/data/Kairos/Kairos_system_data/IED_splited_like_LDC/train'

    '''set dataset name'''
    # suicide_ied_train.json, wiki_drone_strikes_train.json, wiki_ied_bombings_train.json, wiki_mass_car_bombings_train.json
    dataset_names = ['suicide_ied','wiki_drone_strikes','wiki_ied_bombings','wiki_mass_car_bombings']

    for name in dataset_names:
        print(f'creating conditional probability for {name}...')
        dataset_train_path = dataset_path + f'/{name}_train.json'
        output_json_path = outpath + f'/{name}_conditional_prob.json'
        
        nx_dataset = load_dataset(dataset_train_path)
        p_e2_given_e1 = calculate_p_e2_given_e1(nx_dataset)
        with open(output_json_path, 'w') as o:
            json.dump(p_e2_given_e1, o, indent=4)
            print(f'output to {output_json_path}...')
            print()
