import yaml
# import pdb 

from yaml.loader import SafeLoader
# pdb.set_trace()
with open('C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\demo1.yaml', 'r') as f:
    data = list(yaml.load_all(f, Loader=SafeLoader))
    print(data)
    
    
    