import datetime
import mimetypes
import nbformat
import uuid

from notebook.services.contents.manager import ContentsManager
from notebook.services.contents.filecheckpoints import GenericFileCheckpoints

from tornado.web import HTTPError

from mmscontents.service import get_notebooks, save_notebook, get_mms_token
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
        id = path.rsplit('/', 1)[-1].split('.')[0]
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
            for i in get_notebooks(self.mms_url, self.mms_project, self._mms_token):
                nmodel = base_model('/' + i + '.ipynb')
                nmodel.update(
                    type="notebook",
                    format="json",
                    last_modified=DUMMY_CREATED_DATE,
                    created=DUMMY_CREATED_DATE
                )
                content.append(nmodel)
            model.update(content=content)
        return model

    def _notebook_model_from_path(self, path, content=False, format=None):
        print('?notebook from path ' + path + ' ' + str(content))
        model = base_model(path)
        model.update(
            last_modified=DUMMY_CREATED_DATE,
            created=DUMMY_CREATED_DATE,
            type='notebook'
        )
        if content:
            if not self.file_exists(path):
                self.no_such_entity(path)
            id = path.rsplit('/', 1)[-1].split('.')[0]
            #file_content = json.dumps(get_notebooks(mms_url, mms_project)[id])
            #nb_content = nb_format.reads(file_content, as_version=nbformat.NO_CONVERT)
            #self.mark_trusted_cells(nb_content, path)
            nb_content = nbformat.from_dict(move_id_to_metadata(get_notebooks(self.mms_url, self.mms_project, self._mms_token)[id]))
            model.update(
                content=nb_content,
                format='json'
            )
            #self.validate_notebook_model(model)
        return model

    def _file_model_from_path(self, path, content=False, format=None):
        model = base_model(path)
        model['type'] = 'file'
        if content:
            if not self.file_exists(path):
                self.no_such_entity(path)
            file_content = get_notebooks(self.mms_url, self.mms_project, self._mms_token)[path]
            model["format"] = format or "text"
            model["content"] = file_content
            model["mimetype"] = mimetypes.guess_type(path)[0] or "text/plain"
            if format == "base64":
                model["format"] = format or "base64"
                from base64 import b64decode
                model["content"] = b64decode(content)
        return model

    def save(self, model, path): #TODO doesn't work for creating new notebooks or cells
        # (name vs id in path, it'll create a new notebook but with different path), 
        # for new cells it'll keep adding new ids since ids doesn't go back to frontend
        # may need frontend extensions to add these ids as they're created
        print('?save ' + path)
        notebook = add_mms_id(model['content'])
        print(notebook)
        save_notebook(self.mms_url, self.mms_project, notebook, self._mms_token)
        return self.get(path, type='notebook', content=False)

    def delete_file(self, path):
        pass

    def rename_file(self, old_path, new_path):
        pass

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
    notebook['metadata']['mms'] = {'id': notebook['id']}
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