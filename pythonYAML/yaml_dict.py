import yaml

xyz = {
       100:{'name':'pushapak ','phone':'345'},
       4:{'name':'pushapak ','phone':'12345'}
      }


xyz1 = {1:"One", 2:"Two", 3:"Three", 5:"five", 6:"six"}

xyz2 = {'api_version': None,
            'kind': None,
            'metadata': {'annotations': None,
                         'cluster_name': None,
                        #  'creation_timestamp': datetime.datetime(2021, 10, 28, 11, 2, 10, tzinfo=tzutc()),
                         'deletion_grace_period_seconds': None,
                         'deletion_timestamp': None,
                         'finalizers': None,
                         'generate_name': None,
                         'generation': None,
                         'labels': None
            }
            #              'managed_fields': [{'api_version': 'v1',
            #                                  'fields_type': 'FieldsV1',
            #                                  'fields_v1': {'f:status': {'f:phase': {}}},
            #                                  'manager': 'kubectl-create',
            #                                  'operation': 'Update',
            #                                  'subresource': None,
            #                                 #  'time': datetime.datetime(2021, 10, 28, 11, 2, 10, tzinfo=tzutc())}],
            #              'name': 'test',
            #              'namespace': None,
            #              'owner_references': None,
            #              'resource_version': '4324345',
            #              'self_link': None,
            #              'uid': 'd8217333-2a20-4260-98ec-e1dac20c9153'},
            # 'spec': {'finalizers': ['kubernetes']},
            # 'status': {'conditions': None, 'phase': 'Active'}]
        }
xyz3 = {
  "kind": "APIVersions",
  "versions": [
    "v1"
  ],
  "serverAddressByClientCIDRs": [
    {
      "clientCIDR": "0.0.0.0/0",
      "serverAddress": "10.0.1.149:443"
    }
  ]
}
print(yaml.dump(xyz[100]))
      
# print(yaml.dump(xyz1))

# print(yaml.dump(xyz2))
# print(yaml.dump(xyz3))



# print(yaml.dump_all(dict))