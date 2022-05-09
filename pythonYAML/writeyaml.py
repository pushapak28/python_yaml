import yaml

yamlcontent = """
-'manoharsha'
-'1231414'
-'data'
-'xyz'
-'kahsna'
"""
# yamlas = 123

data = yaml.safe_load(yamlcontent)
with open('manoharsha.yaml','w') as f:
    yaml.dump(yamlcontent,f)
    
print(open('manoharsha.yaml').read())