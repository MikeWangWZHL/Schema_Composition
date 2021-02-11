from os import listdir
from os.path import isfile, join

def count_community_from_doc_list(input_docs_dir):
    graph_objects_files = [f for f in listdir(input_docs_dir) if isfile(join(input_docs_dir, f))]
    count = 0
    for f in graph_objects_files:
        if f.endswith('.pickle'):
            count += int(f.split('.')[0].split('_')[-1])
    print('instance graph count: ', len(graph_objects_files)-1)
    return count

'''usage'''
total_count = 0
for phase in ['test','train','dev']:
    
    count = count_community_from_doc_list(f'/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graph_data_with_partition/{phase}')
    
    print(f'{phase}:{count}')
    total_count += count

print(f'total_count: ', total_count)  

print(count_community_from_doc_list('/shared/nas/data/m1/wangz3/schema_composition/Schema_Composition/graph_data_with_partition/quizlet_4/graph_objects'))

