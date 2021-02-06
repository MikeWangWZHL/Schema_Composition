import json
from glob import glob
import os

def write_articles_rsd(input_dir, output_dir):
    fs = glob(f'{input_dir}/*')
    print(fs)
    for f in fs:
        page_data = json.load(open(f))
        article = page_data['article']
        title = page_data['title'].replace(' ','_')
        with open(os.path.join(output_dir,f'{title}.rsd.txt'),'w') as o:
            o.write(article)

def write_section_offset_json(input_dir, case, output_dir):
    print('case: ',case)
    fs = glob(f'{input_dir}/*')
    offset_dict = {}
    for f in fs:
        page_data = json.load(open(f))
        article = page_data['article']
        title = page_data['title'].replace(' ','_')
        sections = page_data['sections']
        assert title not in offset_dict
        offset_dict[title] = sections
    with open(os.path.join(output_dir,f'{case}_offset.json'),'w') as o:
        json.dump(offset_dict,o,indent = 4)

if __name__ == '__main__':
    senarios = ['wiki_backpack_bombings','wiki_drone_strikes','wiki_ied_bombings','wiki_mass_car_bombings','wiki_suicide_bombings']
    section_offset_json_dir = '/shared/nas/data/m1/wangz3/schema_composition/wikidata/section_offests_lookup_jsons'

    for case in senarios:    
        input_dir = f'/shared/nas/data/m1/wangz3/schema_composition/wikidata/article_page_data/{case}' 
        output_dir = f'/shared/nas/data/m1/wangz3/schema_composition/wikidata/wiki_article_rsd/{case}_rsd' 

        if not os.path.exists(output_dir):
            print('=======================')
            print(f'making dir {case}_rsd')
            print('=======================')
            os.makedirs(output_dir)
        write_articles_rsd(input_dir,output_dir)
        write_section_offset_json(input_dir,case,section_offset_json_dir)