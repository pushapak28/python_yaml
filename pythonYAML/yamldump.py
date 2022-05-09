import yaml

user_details = {'UserName': 'Pushapak',
                'Password': 'star123*',
                'phone': 3256,
                'AccessKeys': ['EmployeeTable',
                               'SoftwaresList',
                               'HardwareList']}

with open('C:\\Users\\epalpus\\Documents\\Python\\pythonYAML\\demo1.yaml', 'w') as f:
    data = yaml.dump(user_details, f, sort_keys=False, default_flow_style=False)
    print("######", data)