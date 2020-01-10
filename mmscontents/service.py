import mms_python_client as mms_client
from mms_python_client.rest import ApiException

def get_notebooks(url, project, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api_instance = mms_client.NotebooksControllerApi(mms_client.ApiClient(configuration))
    try:
        api_response = api_instance.get_all_notebooks(project, 'master')
        ret = {}
        for i in api_response.notebooks:
            ret[i['id']] = i
        return ret
    except ApiException as e:
        print("Exception when calling NotebooksControllerApi->get_all_notebooks: %s\n" % e)

def get_notebook(url, project, id, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api_instance = mms_client.NotebooksControllerApi(mms_client.ApiClient(configuration))
    try:
        api_response = api_instance.get_notebook(project, 'master', id)
        return api_response.notebooks[0]
    except ApiException as e:
        print("Exception when calling NotebooksControllerApi->get_notebook: %s\n" % e)

def save_notebook(url, project, notebook, token):
    configuration = mms_client.Configuration()
    configuration.host = url
    configuration.access_token = token
    api_instance = mms_client.NotebooksControllerApi(mms_client.ApiClient(configuration))
    try:
        r = mms_client.NotebooksRequest()
        r.notebooks = [notebook]
        api_response = api_instance.create_or_update_notebooks(project, 'master', notebooks_request=r)
        return api_response.notebooks[0]
    except ApiException as e:
        print("Exception when calling NotebooksControllerApi->create_or_update_notebooks: %s\n" % e)

def get_mms_token(url, username, password):
    configuration = mms_client.Configuration()
    configuration.host = url
    jwt_authentication_request = mms_client.JwtAuthenticationRequest()
    jwt_authentication_request.username = username
    jwt_authentication_request.password = password
    try:
        api_instance = mms_client.AuthenticationControllerApi(mms_client.ApiClient(configuration))
        api_response = api_instance.create_authentication_token(jwt_authentication_request=jwt_authentication_request)
        return api_response.token
    except ApiException as e:
        print("Exception when calling create_authentication_token: %s\n" % e)

