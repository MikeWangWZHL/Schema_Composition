import json
import re

def parse_wiki_list_get_events(input_markup):
    lines = []
    with open(input_markup) as doc:
        for line in doc:
            lines.append(line)
    title_set = set()
    for i in range(len(lines)):
        line = lines[i]
        if line.startswith('|-'):
            event_title_line = lines[i+1]
            found_title_links = re.findall('\[\[.*?\]\]',event_title_line)
            if found_title_links != []:
                for title in found_title_links:
                    if '|' in title:
                        title = title.split('|')[-1]
                    title = title.replace('[[','')
                    title = title.replace(']]','')
                    re.sub("\(.*\)", "",title)
                    title_set.add(title.strip())
    return title_set

if __name__ == '__main__':
    input_markup = '/shared/nas/data/m1/wangz3/schema_composition/wikidata/Disease_Outbreak/list_of_epidemics_markup.txt'
    titles = parse_wiki_list_get_events(input_markup)
    print(f'found {len(titles)} pages')
    # for t in titles:
    #     print(t)
    json.dump(list(titles),open('Epidemics_page_titles.json','w',  encoding = 'utf-8'),indent = 4, sort_keys=True,)