import mms_python_client as mms_client
from mms_python_client.rest import ApiException

def get_orgs_with_jupyter_projects(url, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api = mms_client.OrgsApi(mms_client.ApiClient(configuration))
    try:
        res = {}
        orgs = api.get_all_orgs().orgs
        orgsDict = {}
        for o in orgs:
            orgsDict[o.id] = o
        projectsMap = get_jupyter_projects(url, token)
        for pid in projectsMap:
            orgId = projectsMap[pid].org_id
            if orgId in orgsDict:
                res[orgId] = orgsDict[orgId]
        return res
    except ApiException as e:
        print("Exception when calling OrgsApi->get_all_orgs: %s\n" % e)

def get_jupyter_projects(url, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api = mms_client.ProjectsApi(mms_client.ApiClient(configuration))
    try:
        res = api.get_all_projects()
        ret = {}
        for p in res.projects:
            if p.schema == 'jupyter':
                ret[p.id] = p
        return ret
    except ApiException as e:
        print("Exception when calling ProjectsApi->get_all_projects: %s\n" % e)

def get_notebooks(url, project, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api_instance = mms_client.NotebooksApi(mms_client.ApiClient(configuration))
    try:
        api_response = api_instance.get_all_notebooks(project, 'master')
        ret = {}
        for i in api_response.notebooks:
            ret[i['id']] = i
        return ret
    except ApiException as e:
        print("Exception when calling NotebooksApi->get_all_notebooks: %s\n" % e)

def get_notebook(url, project, id, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api_instance = mms_client.NotebooksApi(mms_client.ApiClient(configuration))
    try:
        api_response = api_instance.get_notebook(project, 'master', id)
        return api_response.notebooks[0]
    except ApiException as e:
        print("Exception when calling NotebooksApi->get_notebook: %s\n" % e)

def save_element(url, project, element, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api_instance = mms_client.ElementsApi(mms_client.ApiClient(configuration))
    try:
        r = mms_client.ElementsRequest(elements=[element])
        api_response = api_instance.create_or_update_elements(project, 'master', elements_request=r)
        return api_response.elements[0]
    except ApiException as e:
        print("Exception when calling NotebooksApi->create_or_update_notebooks: %s\n" % e)

def save_notebook(url, project, notebook, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api_instance = mms_client.NotebooksApi(mms_client.ApiClient(configuration))
    try:
        r = mms_client.NotebooksRequest(notebooks=[notebook])
        api_response = api_instance.create_or_update_notebooks(project, 'master', notebooks_request=r)
        return api_response.notebooks[0]
    except ApiException as e:
        print("Exception when calling NotebooksApi->create_or_update_notebooks: %s\n" % e)

def get_mms_token(url, username, password):
    print('?get_mms_token ' + url + ' ' + username)
    configuration = mms_client.Configuration()
    configuration.host = url
    jwt_authentication_request = mms_client.JwtAuthenticationRequest(username, password)
    try:
        api_instance = mms_client.AuthApi(mms_client.ApiClient(configuration))
        api_response = api_instance.create_authentication_token(jwt_authentication_request=jwt_authentication_request)
        return api_response.token
    except ApiException as e:
        print("Exception when calling create_authentication_token: %s\n" % e)

