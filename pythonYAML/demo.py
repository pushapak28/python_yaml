import yaml

# tut = ""
with open(r'C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\tutorial.yaml')as f:
    tut = yaml.load(f,Loader=yaml.FullLoader)
    print(tut)

    