import json
from bots import xwbi

lexeme = xwbi.wbi.lexeme.get(entity_id="L45")

for sense in lexeme.senses.get_json():
    print(f"{sense}")