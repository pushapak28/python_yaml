from pydoc import doc
import yaml

with open('C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\multi_doc.yaml','r') as x:
      doc = yaml.safe_load_all(x)
      # doc1 = yaml.safe_load(x)
      # print(doc)
      for i in doc:
         print(i)
    
          