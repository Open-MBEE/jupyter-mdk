import datetime
import mimetypes
import nbformat
import uuid

from notebook.services.contents.manager import ContentsManager
from notebook.services.contents.filecheckpoints import GenericFileCheckpoints

from tornado.web import HTTPError

from mmscontents.service import get_notebooks, get_notebook, save_notebook, get_mms_token
from traitlets import Unicode

DUMMY_CREATED_DATE = datetime.datetime.fromtimestamp(86400)
NBFORMAT_VERSION = 4


class MMSContentsManager(ContentsManager):

    mms_url = Unicode("https://mms.openmbee.org", help="MMS endpoint").tag(config=True, env="JPYNB_MMS_URL")
    mms_project = Unicode("a", help="MMS project id").tag(config=True, env="JPYNB_MMS_PROJECT_ID")
    mms_username = Unicode("dummy", help="MMS username").tag(config=True, env="JPNYB_MMS_USERNAME")
    mms_password = Unicode("dummy", help="MMS password").tag(config=True, env="JPNYB_MMS_PASSWORD")
    _mms_token = ""
    
    def __init__(self, *args, **kwargs):
        super(MMSContentsManager, self).__init__(*args, **kwargs)
        self._mms_token = get_mms_token(self.mms_url, self.mms_username, self.mms_password)

    def dir_exists(self, path):
        print('?dir exists ' + path)
        if path == '' or path == '/':
            return True
        return False

    def is_hidden(self, path):
        return False

    def file_exists(self, path=''):
        print('?file exists ' + path)
        if path == '' or path == '/':
            return False
        id = get_id_from_path(path)
        return id in get_notebooks(self.mms_url, self.mms_project, self._mms_token)

    def get(self, path, content=True, type=None, format=None):
        print('?get ' + path + ' ' + str(content) + ' ' + str(type) + ' ' + str(format))
        if type is None:
            type = self.guess_type(path)
        try:
            func = {
                'directory': self._get_directory,
                'notebook': self._get_notebook,
                'file': self._get_file,
            }[type]
        except KeyError:
            raise ValueError("Unknown type passed: '{}'".format(type))
        return func(path=path, content=content, format=format)

    def _get_directory(self, path, content=True, format=None):
        return self._directory_model_from_path(path, content=content)

    def _get_notebook(self, path, content=True, format=None):
        return self._notebook_model_from_path(path, content=content, format=format)

    def _get_file(self, path, content=True, format=None):
        return self._file_model_from_path(path, content=content, format=format)

    def _directory_model_from_path(self, path, content=False):
        print('?dir model from path ' + path + ' ' + str(content))
        model = base_directory_model(path)
        if content:
            if not self.dir_exists(path):
                self.no_such_entity(path)
        if path == '' or path == '/':
            content = []
            for id, n in get_notebooks(self.mms_url, self.mms_project, self._mms_token).items():
                name = id + '.ipynb'
                if 'mms' in n['metadata'] and 'name' in n['metadata']['mms']:
                    name = n['metadata']['mms']['name']
                nmodel = base_model(name)
                nmodel.update(
                    name=name,
                    type="notebook",
                    format="json",
                    last_modified=string_to_date(n['_modified']),
                    created=string_to_date(n['_created']),
                    path=id + '.ipynb'
                )
                content.append(nmodel)
            model.update(content=content)
        return model

    def _notebook_model_from_path(self, path, content=False, format=None):
        print('?notebook from path ' + path + ' ' + str(content))
        if not self.file_exists(path):
            self.no_such_entity(path)

        id = get_id_from_path(path)
        notebook = get_notebook(self.mms_url, self.mms_project, id, self._mms_token)
        name = id + '.ipynb'
        if 'mms' in notebook['metadata'] and 'name' in notebook['metadata']['mms']:
            name = notebook['metadata']['mms']['name']
        model = base_model(path)
        model.update(
            last_modified=string_to_date(notebook['_modified']),
            created=string_to_date(notebook['_created']),
            type='notebook',
            name=name
        )
        if content:    
            #file_content = json.dumps(get_notebooks(mms_url, mms_project)[id])
            #nb_content = nb_format.reads(file_content, as_version=nbformat.NO_CONVERT)
            #self.mark_trusted_cells(nb_content, path)
            nb_content = nbformat.from_dict(move_id_to_metadata(notebook))
            model.update(
                content=nb_content,
                format='json'
            )
            #self.validate_notebook_model(model)
        return model

    def _file_model_from_path(self, path, content=False, format=None):
        print('?file from path ' + path + ' ' + str(content) + ' ' + str(format))
        model = self._notebook_model_from_path(path, content, format)
        model['type'] = 'file'
        if content:
            model["mimetype"] = "application/json"
        return model

    def save(self, model, path): 
        # for new cells it'll keep adding new ids and cell elements since ids doesn't go back to frontend
        # may need frontend extensions to add these ids as they're created
        print('?save ' + path + ' ' + str(model))
        notebook = add_mms_id(model['content'])
        if 'name' not in notebook['metadata']['mms']:
            notebook['metadata']['mms']['name'] = 'Untitled.ipynb'
        print('notebook_to_save: ' + str(notebook))
        notebook = save_notebook(self.mms_url, self.mms_project, notebook, self._mms_token)
        ret = base_model(path)
        ret.update(
            path=notebook['id'] + '.ipynb',
            last_modified=string_to_date(notebook['_modified']),
            created=string_to_date(notebook['_created']),
            type='notebook',
            name=notebook['metadata']['mms']['name']
        )
        return ret
        #return self.get(path, type='notebook', content=False)

    def delete_file(self, path):
        pass

    def rename_file(self, old_path, new_path):
        #jupyter is treating name as the path...so this won't work
        print("?rename " + old_path + " " + new_path)
        id = get_id_from_path(old_path)
        notebook = get_notebook(self.mms_url, self.mms_project, id, self._mms_token)
        new_name = new_path.rsplit('/', 1)[-1]
        if 'metadata' not in notebook:
            notebook['metadata'] = {}
        if 'mms' not in notebook['metadata']:
            notebook['metadata']['mms'] = {'id': notebook['id']}
        notebook['metadata']['mms']['name'] = new_name
        to_save = {'id': notebook['id'], 'metadata': notebook['metadata']}
        notebook = save_notebook(self.mms_url, self.mms_project, to_save, self._mms_token)
        ret = base_model(old_path)
        ret.update(
            name=new_name,
            last_modified=string_to_date(notebook['_modified']),
            created=string_to_date(notebook['_created']),
            type='notebook'
        )
        return ret

    def guess_type(self, path):
        print('?guess type ' + path)
        if path == '' or path == '/':
            return 'directory'
        return 'notebook'

    def do_error(self, msg, code=500):
        raise HTTPError(code, msg)

    def no_such_entity(self, path):
        self.do_error("No such entity: [{path}]".format(path=path), 404)

    def _checkpoints_class_default(self):
        return GenericFileCheckpoints

def base_model(path):
    return {
        "name": path.rsplit('/', 1)[-1],
        "path": path,
        "writable": True,
        "last_modified": None,
        "created": None,
        "content": None,
        "format": None,
        "mimetype": None,
    }

def base_directory_model(path):
    model = base_model(path)
    model.update(
        type="directory",
        last_modified=DUMMY_CREATED_DATE,
        created=DUMMY_CREATED_DATE,
        format="json",
        content=[])
    return model

def move_id_to_metadata(notebook):
    if 'mms' not in notebook['metadata']:
        notebook['metadata']['mms'] = {}
    notebook['metadata']['mms']['id']: notebook['id']
    for i in notebook['cells']:
        i['metadata']['mms'] = {'id': i['id']}
    return notebook

def add_mms_id(notebook):
    if 'mms' not in notebook['metadata']:
        notebook['metadata']['mms'] = {'id': str(uuid.uuid4())}
    notebook['id'] = notebook['metadata']['mms']['id']
    for i in notebook['cells']:
        if 'mms' not in i['metadata']:
            i['metadata']['mms'] = {'id': str(uuid.uuid4())}
        i['id'] = i['metadata']['mms']['id']
    return notebook

def get_id_from_path(path):
    return path.rsplit('/', 1)[-1].split('.')[0]

def string_to_date(s):
    s = s[:-5] + '000' + s[-5:]
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f%z')
