import json


CONFIG = {
    'MOUNTS': ['/media'],
    'DESTINATIONS': ['/tmp/autodl'],
}


with open('config.json', 'r') as fp:
    CONFIG.update(json.load(fp))
