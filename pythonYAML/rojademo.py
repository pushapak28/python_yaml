import yaml
import json
with open('C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\rojademo.yaml','r') as f:
  config = yaml.safe_load(f)
with open('roja1.json','w') as j:
  json.dump(config,j)
print("done")