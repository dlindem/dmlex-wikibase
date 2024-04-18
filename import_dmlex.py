import json, re
from bots import xwbi


source_file = "ssc_out.json"

def dump_metadata(metadata):
    with open(f"dictionary_metadata/{source_file}", "w", encoding="utf-8") as metafile:
        json.dump(metadata, metafile, indent=2)

with open(f"dmlex_source/{source_file}", "r", encoding="utf-8") as sourcefile:
    source = json.load(sourcefile)

try:
    with open(f"dictionary_metadata/{source_file}", "r", encoding="utf-8") as metafile:
        metadata = json.load(metafile)
except:
    metadata = {'title': source['title'], 'uri': source['uri'], 'langCode': source['langCode']}

if 'langCode_wiki' in metadata and 'langCode_item' in metadata:
    langCode_wiki = metadata['langCode_wiki']
    langCode_item = metadata['langCode_item']
#else: # get language data from Wikibase
    # query = "select ?langCode ?langCode_wiki ?langCode_item where { "
    # query += f"?langCode_item xdp:P32 ?langCode; "
    #
    # bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=xwbi.config['mapping']['wikibase_sparql_prefixes'],
    #                                                  endpoint=xwbi.config['mapping']['wikibase_sparql_endpoint'])['results'][
    #     'bindings']
    # print(results)
if "dictionary_item" in metadata:
    dict_qid = metadata['dictionary_item'] # dict already exists on Wikibase
else: # create item describing dictionary
    labels =[{'lang': langCode_wiki, 'value': metadata['title']}]
    if langCode_wiki != "en":
        labels.append({'lang': 'en', 'value': metadata['title']})
    itemdata = {'qid': False, 'statements':[
        {'type': 'item', 'prop_nr': 'P5', 'value': 'Q100'}, # instance of Lexicographical resource
        {'type': 'monolingualtext', 'prop_nr': 'P6', 'value': metadata['title'], 'lang':langCode_wiki},
        {'type': 'url', 'prop_nr': 'P112', 'value': metadata['uri']},
    ], 'labels': labels}

    dict_qid = xwbi.itemwrite(itemdata)
    metadata['dictionary_item'] = dict_qid
    dump_metadata(metadata)

# process controlled values
controlled_value_groups = {'labelTags':'Q103'}

for cv in controlled_value_groups:
    if cv in source:
        if cv not in metadata:
            metadata[cv] = {}
        for valgrp in source[cv]:
            val = list(valgrp.values())[0]
            print(f"Will check value '{val}' of controlled value group '{cv}'...")
            if val not in metadata[cv]:
                labels = [{'lang': langCode_wiki, 'value': val}]
                if langCode_wiki != "en":
                    labels.append({'lang': 'en', 'value': val})
                itemdata = {'qid': False, 'statements':[
                    {'type': 'item', 'prop_nr': 'P5', 'value': controlled_value_groups[cv]},  # instance of Label Tag
                    {'type': 'item', 'prop_nr': 'P207', 'value': dict_qid}
                ], 'labels': labels}
                val_qid = xwbi.itemwrite(itemdata)
                metadata[cv][val] = val_qid
                dump_metadata(metadata)


