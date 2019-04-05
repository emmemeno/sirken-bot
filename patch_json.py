import json

with open("resources/p99merbs_test.json") as f:
    json_obj = json.load(f)
entities = {}
entity = dict()
tag = list()
tods_and_pops = {}
entity_timers = dict()

for i in json_obj:
    entity = {i: {
                "alias": json_obj[i]["alias"],
                "respawn_time": json_obj[i]["respawn_time"],
                "plus_minus": json_obj[i]["plus_minus"],
                "recurring": json_obj[i]["recurring"],
                "tag": tag
                }
            }
    print(entity)
    entities.update(entity)
    entity_timers = {i: {"tod": json_obj[i]["tod"],
                         "pop": json_obj[i]["pop"],
                         "signed": json_obj[i]["signed"],
                         "accuracy": json_obj[i]["accuracy"]
                        }
                     }
    tods_and_pops.update(entity_timers)

with open("resources/entities.json", 'w') as outfile:
    json.dump(entities, outfile, indent=2)

with open("resources/timers.json", 'w') as outfile:
    json.dump(tods_and_pops, outfile, indent=2)


