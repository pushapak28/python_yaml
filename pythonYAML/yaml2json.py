from textwrap import indent
import yaml
import json 

# with open('C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\demo2.yaml','r') as f:
with open('C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\multi_doc.yaml','r') as f:
    configure = yaml.safe_load_all(f)
    
with open('xyz.json','w') as j :
    json.dump(configure,j)
    
print("completed")  
# output = yaml.dump(json.load(open('roja.json','r')),indent=2)
# print(output)
