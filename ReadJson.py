import json

def printJson(saida):
    with open(saida, 'r') as f:
        json_data = json.load(f)
        for j in json_data['return']:
            print(j)