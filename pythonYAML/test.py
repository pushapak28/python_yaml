# import pyyaml module
import yaml ,pdb
from yaml.loader import SafeLoader
# pdb.set_trace()
# Open the file and load the file
with open('C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\demo.yaml','r') as f:
    data = yaml.safe_load(f)
    print(data)