import json, re, time
from bots import xwbi


source_file = "ssc_out.json"

def dump_controldata(controldata):
    with open(f"dmlex_controldata/{source_file}", "w", encoding="utf-8") as metafile:
        json.dump(controldata, metafile, indent=2)

with open(f"dmlex_source/{source_file}", "r", encoding="utf-8") as sourcefile:
    source = json.load(sourcefile)

try:
    with open(f"dmlex_controldata/{source_file}", "r", encoding="utf-8") as metafile:
        controldata = json.load(metafile)
except:
    controldata = {'title': source['title'], 'uri': source['uri'], 'langCode': source['langCode']}

if 'langCode_wiki' in controldata and 'langCode_item' in controldata:
    langCode_wiki = controldata['langCode_wiki']
    langCode_item = controldata['langCode_item']
#else: # get language data from Wikibase
    # query = "select ?langCode ?langCode_wiki ?langCode_item where { "
    # query += f"?langCode_item xdp:P32 ?langCode; "
    #
    # bindings = xwbi.wbi_helpers.execute_sparql_query(query=query, prefix=xwbi.config['mapping']['wikibase_sparql_prefixes'],
    #                                                  endpoint=xwbi.config['mapping']['wikibase_sparql_endpoint'])['results'][
    #     'bindings']
    # print(results)
if "dictionary_item" in controldata:
    dict_qid = controldata['dictionary_item'] # dict already exists on Wikibase
else: # create item describing dictionary
    labels =[{'lang': langCode_wiki, 'value': controldata['title']}]
    if langCode_wiki != "en":
        labels.append({'lang': 'en', 'value': controldata['title']})
    itemdata = {'qid': False, 'statements':[
        {'type': 'item', 'prop_nr': 'P5', 'value': 'Q100'}, # instance of Lexicographical resource
        {'type': 'monolingualtext', 'prop_nr': 'P6', 'value': controldata['title'], 'lang':langCode_wiki},
        {'type': 'url', 'prop_nr': 'P112', 'value': controldata['uri']},
    ], 'labels': labels}

    dict_qid = xwbi.itemwrite(itemdata)
    controldata['dictionary_item'] = dict_qid
    dump_controldata(controldata)

# process controlled values
controlled_value_groups = {'labelTags':'Q103'}

for cv in controlled_value_groups:
    if cv in source:
        if cv not in controldata:
            controldata[cv] = {}
        for valgrp in source[cv]:
            val = list(valgrp.values())[0]
            print(f"Will check value '{val}' of controlled value group '{cv}'...")
            if val not in controldata[cv]:
                labels = [{'lang': langCode_wiki, 'value': val}]
                if langCode_wiki != "en":
                    labels.append({'lang': 'en', 'value': val})
                itemdata = {'qid': False, 'statements':[
                    {'type': 'item', 'prop_nr': 'P5', 'value': controlled_value_groups[cv]},  # instance of Label Tag
                    {'type': 'item', 'prop_nr': 'P207', 'value': dict_qid}
                ], 'labels': labels}
                val_qid = xwbi.itemwrite(itemdata)
                controldata[cv][val] = val_qid
                dump_controldata(controldata)

# process entries
for entry in source['entries']:
    if 'entries' not in controldata:
        controldata['entries'] = {}

    if 'partsOfSpeech' in entry:
        pos_item = controldata['partOfSpeechTags'][entry['partsOfSpeech'][0]]
    else:
        pos_item = "Q108" # pos 'undefined'

    if entry['id'] in controldata['entries']:
        print(f"Entry '{entry['id']}' is already on Wikibase as {controldata['entries'][entry['id']]}")
        lexeme = xwbi.wbi.lexeme.get(entity_id=controldata['entries'][entry['id']])
        #continue
    else:
        lexeme = xwbi.wbi.lexeme.new(language=langCode_item, lexical_category=pos_item)

    lexeme.lemmas.set(language=langCode_wiki, value=entry['headword'])
    claim = xwbi.Item(prop_nr="P207", value=dict_qid)
    lexeme.claims.add(claim)
    claim = xwbi.String(prop_nr="P186", value=entry['id'])
    lexeme.claims.add(claim)

    if 'senses' in entry:
        for sense in entry['senses']:
            lexeme_sense = xwbi.Sense()
            if 'labels' in sense:
                for label in sense['labels']:
                    label_qualifiers = xwbi.Qualifiers()
                    if label in controldata['labelTags']:
                        label_item = controldata['labelTags'][label]
                        qualifier = xwbi.Item(prop_nr="P203", value=label_item)
                        label_qualifiers.add(qualifier)
                    claim = xwbi.String(prop_nr="P197", value=label, qualifiers=label_qualifiers)
                    lexeme_sense.claims.add(claim)
            if 'definitions' in sense:
                gloss = ""
                for definition in sense['definitions']:
                    if gloss != "":
                        gloss += " / "
                    claim = xwbi.String(prop_nr="P209", value=definition['text'])
                    lexeme_sense.claims.add(claim, action_if_exists=xwbi.ActionIfExists.APPEND_OR_REPLACE)
                    gloss += definition['text']
                lexeme_sense.glosses.set(language=langCode_wiki, value=gloss)
            if 'examples' in sense:
                for example in sense['examples']:
                    claim = xwbi.String(prop_nr="P208", value=example['text'])
                    lexeme_sense.claims.add(claim, action_if_exists=xwbi.ActionIfExists.APPEND_OR_REPLACE)
            lexeme.senses.add(lexeme_sense)

    lexeme.write(clear=True)
    controldata['entries'][entry['id']] = lexeme.id
    dump_controldata(controldata)
    print(f"Finished processing entry '{entry['id']}', now on Wikibase as '{lexeme.id}'.")
    time.sleep(1)





