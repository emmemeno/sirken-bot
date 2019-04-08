import json

with open("resources/timers.json") as f:
    json_obj = json.load(f)
entities = {}
entity = dict()

for i in json_obj:
    entity = {i: {"tod": json_obj[i]["tod"],
                         "pop": json_obj[i]["pop"],
                         "signed_tod": json_obj[i]["signed"],
                         "accuracy": json_obj[i]["accuracy"]
                        }
                     }
    entities.update(entity)

print(entities)

with open("resources/timers.json", 'w') as outfile:
    json.dump(entities, outfile, indent=2)

print("JSON PATCHED!")