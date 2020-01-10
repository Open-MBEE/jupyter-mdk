from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

def search_project(projectid):
    client = Elasticsearch(hosts=['localhost'],
            use_ssl=True)

    s = Search(using=client, index=projectid + '_node') \
        .filter('term', **{'_inRefIds': 'master'}) \
        .query("match", source="Jake VanderPlas")  

    response = s.execute()
    res = []
    for hit in response:
        res.append(hit.to_dict())
    return res

print(search_project('bb'))