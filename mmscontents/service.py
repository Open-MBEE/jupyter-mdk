import mms_python_client as mms_client
from mms_python_client.rest import ApiException

def getApiClient(url, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    return mms_client.ApiClient(configuration)

def get_orgs_with_jupyter_projects(url, token):
    api = mms_client.OrgsApi(getApiClient(url, token))
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
    api = mms_client.ProjectsApi(getApiClient(url, token))
    try:
        res = api.get_all_projects()
        ret = {}
        for p in res.projects:
            if p.schema == 'jupyter':
                ret[p.id] = p
        return ret
    except ApiException as e:
        print("Exception when calling ProjectsApi->get_all_projects: %s\n" % e)

def get_refs(url, project, token):
    api_instance = mms_client.RefsApi(getApiClient(url, token))
    try:
        api_response = api_instance.get_all_refs(project)
        ret = {}
        for i in api_response.refs:
            ret[i.id] = i
        return ret
    except ApiException as e:
        print("Exception when calling RefsApi->get_all_refs: %s\n" % e)

def get_notebooks(url, project, ref, token):
    api_instance = mms_client.NotebooksApi(getApiClient(url, token))
    try:
        api_response = api_instance.get_all_notebooks(project, ref)
        ret = {}
        for i in api_response.notebooks:
            ret[i['id']] = i
        return ret
    except ApiException as e:
        print("Exception when calling NotebooksApi->get_all_notebooks: %s\n" % e)

def get_notebook(url, project, ref, id, token):
    api_instance = mms_client.NotebooksApi(getApiClient(url, token))
    try:
        api_response = api_instance.get_notebook(project, ref, id)
        return api_response.notebooks[0]
    except ApiException as e:
        print("Exception when calling NotebooksApi->get_notebook: %s\n" % e)

def save_element(url, project, ref, element, token):
    api_instance = mms_client.ElementsApi(getApiClient(url, token))
    try:
        r = mms_client.ElementsRequest(elements=[element])
        api_response = api_instance.create_or_update_elements(project, ref, elements_request=r)
        return api_response.elements[0]
    except ApiException as e:
        print("Exception when calling NotebooksApi->create_or_update_notebooks: %s\n" % e)

def save_notebook(url, project, ref, notebook, token):
    api_instance = mms_client.NotebooksApi(getApiClient(url, token))
    try:
        r = mms_client.NotebooksRequest(notebooks=[notebook])
        api_response = api_instance.create_or_update_notebooks(project, ref, notebooks_request=r)
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

