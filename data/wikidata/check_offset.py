import json

# check example 1
page_data = json.load(open('/shared/nas/data/m1/wangz3/schema_composition/wikidata/wiki_page_data_sample/Centennial_Olympic_Park_bombing.json'))
article = page_data['article']

assert article[1009:1022] == '== Bombing =='
assert article[3545:3586] == '=== Richard Jewell falsely implicated ==='
assert article[9747:9767] == '== External links =='


# check example 2
page_data = json.load(open('/shared/nas/data/m1/wangz3/schema_composition/wikidata/wiki_page_data_sample/Boston_Marathon_bombing.json'))
article = page_data['article']

assert article[1894:1907] == '== Bombing =='
assert article[7827:7862] == '=== MIT shooting and carjacking ==='


