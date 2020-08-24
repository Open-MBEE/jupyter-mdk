import datetime
import mimetypes
import nbformat
import uuid

from notebook.services.contents.manager import ContentsManager
from notebook.services.contents.filecheckpoints import GenericFileCheckpoints

from tornado.web import HTTPError

import mmscontents.service as service
from mmscontents.checkpoints import NoOpCheckpoints
from traitlets import Unicode
from traitlets import default

DUMMY_CREATED_DATE = datetime.datetime.fromtimestamp(86400)
NBFORMAT_VERSION = 4


class MMSContentsManager(ContentsManager):

    mms_url = Unicode("http://localhost:8080", help="MMS endpoint").tag(config=True, env="JPYNB_MMS_URL")
    mms_username = Unicode("dummy", help="MMS username").tag(config=True, env="JPNYB_MMS_USERNAME")
    mms_password = Unicode("dummy", help="MMS password").tag(config=True, env="JPNYB_MMS_PASSWORD")
    _mms_token = ""
    _mms_projects = {}
    _mms_orgs = {}
    
    def __init__(self, *args, **kwargs):
        super(MMSContentsManager, self).__init__(*args, **kwargs)
        self._mms_token = service.get_mms_token(self.mms_url, self.mms_username, self.mms_password)
        self._mms_orgs = service.get_orgs_with_jupyter_projects(self.mms_url, self._mms_token)
        self._mms_projects = service.get_jupyter_projects(self.mms_url, self._mms_token)

    def dir_exists(self, path):
        print('?dir exists ' + path)
        realpath = get_normalized_path(path)
        if realpath == '':
            return True
        paths = realpath.split('/')
        if (len(paths) > 3) or (len(paths) >= 1 and paths[0] not in self._mms_orgs) or \
                (len(paths) >= 2 and paths[1] not in self._mms_projects) or \
                (len(paths) == 3 and paths[2] not in service.get_refs(self.mms_url, paths[1], self._mms_token)):
            return False
        return True

    def is_hidden(self, path):
        return False

    def file_exists(self, path=''):
        print('?file exists ' + path)
        realpath = get_normalized_path(path)
        if len(realpath.split('/')) <= 3:
            return False
        ids = get_ids_from_path(realpath)
        return ids[3] in service.get_notebooks(self.mms_url, ids[1], ids[2], self._mms_token)

    def get(self, path, content=True, type=None, format=None):
        print('?get ' + path + ' ' + str(content) + ' ' + str(type) + ' ' + str(format))
        realpath = get_normalized_path(path)
        if type is None:
            type = self._guess_type(realpath)
        func = {
                'directory': self._directory_model_from_path,
                'notebook': self._notebook_model_from_path,
                'file': self._file_model_from_path,
        }[type]
        res = func(path=realpath, content=content, format=format)
        return res

    def _directory_model_from_path(self, path, content=False, format=None):
        print('?dir model from path ' + path + ' ' + str(content))
        if content:
            if not self.dir_exists(path):
                self._no_such_entity(path)
        model = None
        ids = get_ids_from_path(path)
        if path == '' or path == '/': #orgs
            contents = []
            for id, org in self._mms_orgs.items():
                contents.append(directory_model(org.name, '/' + id, org, None))
            model = directory_model('', '/', None, contents)
        elif len(ids) == 1: #projects under an org
            contents = []
            for id, proj in self._mms_projects.items():
                if proj.org_id == ids[0]:
                    contents.append(directory_model(proj.name, '/' + ids[0] + '/' + id, proj, None))
            org = self._mms_orgs[ids[0]]
            model = directory_model(org.name, '/' + ids[0], org, contents)
        elif len(ids) == 2: #refs under a project
            contents = []
            for id, ref in service.get_refs(self.mms_url, ids[1], self._mms_token).items():
                contents.append(directory_model(ref.name, '/' + ids[0] + '/' + ids[1] + '/' + id, ref, None))
            project = self._mms_projects[ids[1]]
            model = directory_model(project.name, '/' + ids[0] + '/' + ids[1], project, contents)
        elif len(ids) == 3: #notebooks under a ref
            contents = []
            for id, n in service.get_notebooks(self.mms_url, ids[1], ids[2], self._mms_token).items():
                name = id + '.ipynb'
                if 'mms' in n['metadata'] and 'name' in n['metadata']['mms']:
                    name = n['metadata']['mms']['name']
                contents.append(notebook_model(name, '/' + ids[0] + '/' + ids[1] + '/' + ids[2] + '/' + id + '.ipynb', n, None))
            refs = service.get_refs(self.mms_url, ids[1], self._mms_token)
            ref = refs[ids[2]]
            model = directory_model(ref.name, '/' + ids[0] + '/' + ids[1] + '/' + ids[2], ref, contents)
        return model

    def _notebook_model_from_path(self, path, content=False, format=None):
        print('?notebook from path ' + path + ' ' + str(content))
        if not self.file_exists(path):
            self._no_such_entity(path)

        ids = get_ids_from_path(path)
        notebook = service.get_notebooks(self.mms_url, ids[1], ids[2], self._mms_token)[ids[3]] #worksaround for get_notebook not working
        name = ids[3] + '.ipynb'
        if 'mms' in notebook['metadata'] and 'name' in notebook['metadata']['mms']:
            name = notebook['metadata']['mms']['name']
        model = notebook_model(name, '/' + ids[0] + '/' + ids[1] + '/' + ids[2] + '/' + ids[3] + '.ipynb', notebook, None)
        if content:    
            #file_content = json.dumps(get_notebooks(mms_url, mms_project)[id])
            #nb_content = nb_format.reads(file_content, as_version=nbformat.NO_CONVERT)
            #self.mark_trusted_cells(nb_content, path)
            nb_content = nbformat.from_dict(move_id_to_metadata(notebook))
            model.update(
                content = nb_content,
                format = 'json'
            )
            #self.validate_notebook_model(model)
        return model

    def _file_model_from_path(self, path, content=False, format=None):
        print('?file from path ' + path + ' ' + str(content) + ' ' + str(format))
        model = self._notebook_model_from_path(path, content, format)
        model['type'] = 'file'
        if content:
            model["mimetype"] = "application/x-ipynb+json"
        return model

    def save(self, model, path): 
        # for new cells it'll keep adding new ids and cell elements since ids doesn't go back to frontend
        # may need frontend extensions to add these ids as they're created
        print('?save ' + path + ' ' + str(model))
        realpath = get_normalized_path(path)
        ids = get_ids_from_path(realpath)
        if len(ids) <= 3:
            self._do_error("cannot create here", 400)
        if model['type'] != 'notebook':
            self._do_error("cannot create non notebooks", 400)
        notebook = add_mms_id(model['content'], ids[3])
        if 'name' not in notebook['metadata']['mms']:
            notebook['metadata']['mms']['name'] = 'Untitled.ipynb'
        print('notebook_to_save: ' + str(notebook))
        notebook = service.save_notebook(self.mms_url, ids[1], ids[2], notebook, self._mms_token)
        ret = {
            "name": notebook['metadata']['mms']['name'],
            "path": '/' + ids[0] + '/' + ids[1] + '/' + ids[2] + '/' + notebook['id'] + '.ipynb',
            "writable": True,
            "last_modified": string_to_date(notebook['_modified']),
            "created": string_to_date(notebook['_created']),
            "content": None,
            "format": None,
            "mimetype": None,
            'type': 'notebook'
        }
        return ret
        #return self.get(path, type='notebook', content=False)

    def delete_file(self, path):
        pass

    def rename_file(self, old_path, new_path):
        # the passed in path is using the name and not the actual path with id
        print("?rename " + old_path + " " + new_path)
        real_old_path = get_normalized_path(old_path)
        real_new_path = get_normalized_path(new_path)
        old_ids = get_ids_from_path(real_old_path)
        new_ids = get_ids_from_path(real_new_path)
        if len(old_ids) != 4 or len(new_ids) != 4:
            self._do_error('cannot rename non notebooks', 400)
        old_name = old_ids[3] + '.ipynb'
        new_name = new_ids[3] + '.ipynb'

        notebooks = service.get_notebooks(self.mms_url, old_ids[1], old_ids[2], self._mms_token)
        #find notebook with the old name....
        notebook = None
        for id, n in notebooks.items():
            if 'mms' in n['metadata'] and 'name' in n['metadata']['mms'] and n['metadata']['mms']['name'] == old_name:
                notebook = n
                break

        if 'metadata' not in notebook:
            notebook['metadata'] = {}
        if 'mms' not in notebook['metadata']:
            notebook['metadata']['mms'] = {}
        notebook['metadata']['mms']['name'] = new_name
        notebook['metadata']['mms']['id'] = notebook['id']

        to_save = {'id': notebook['id'], 'metadata': notebook['metadata']}
        notebook = service.save_element(self.mms_url, old_ids[1], old_ids[2], to_save, self._mms_token)
        ret = notebook_model(new_name, '/' + old_ids[0] + '/' + old_ids[1] + '/' + old_ids[2] + '/' + notebook['id'] + '.ipynb', notebook, None)
        #return ret

    def _guess_type(self, path):
        print('?guess type ' + path)
        if len(path.split('/')) <= 3:
            return 'directory'
        return 'notebook'

    def _do_error(self, msg, code=500):
        raise HTTPError(code, msg)

    def _no_such_entity(self, path):
        self._do_error("No such entity: [{path}]".format(path=path), 404)

    @default('checkpoints_class')
    def _default_checkpoints_class(self):
        return GenericFileCheckpoints #NoOpCheckpoints

def move_id_to_metadata(notebook):
    if 'mms' not in notebook['metadata']:
        notebook['metadata']['mms'] = {}
    notebook['metadata']['mms']['id'] = notebook['id']
    for i in notebook['cells']:
        i['metadata']['mms'] = {'id': i['id']}
    return notebook

def add_mms_id(notebook, namepath=None):
    if 'mms' not in notebook['metadata']:
        notebook['metadata']['mms'] = {'id': str(uuid.uuid4())}
        if namepath is not None:
            notebook['metadata']['mms']['name'] = namepath + '.ipynb'
    notebook['id'] = notebook['metadata']['mms']['id']
    for i in notebook['cells']:
        if 'mms' not in i['metadata']:
            i['metadata']['mms'] = {'id': str(uuid.uuid4())}
        i['id'] = i['metadata']['mms']['id']
    return notebook

def get_ids_from_path(path):
    paths = path.split('/')
    if len(paths) > 3:
        paths[3] = paths[3].rsplit('.', 1)[0]
    return paths

def string_to_date(s):
    if s is None:
        return DUMMY_CREATED_DATE
    s = s[:-5] + '000' + s[-5:]
    return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f%z')

def get_normalized_path(path):
    return path.strip('/')

def base_model(name, path, type, contents):
    model = {
        "name": name,
        "path": path,
        "writable": True,
        "last_modified": DUMMY_CREATED_DATE,
        "created": DUMMY_CREATED_DATE,
        "content": contents,
        "format": 'json',
        "mimetype": None,
        'type': type
    }
    if contents is None:
        model['format'] = None
    return model

def directory_model(name, path, ob, contents):
    model = base_model(name, path, 'directory', contents)
    if ob is not None:
        model.update(
            last_modified = string_to_date(ob.modified),
            created = string_to_date(ob.created)
        )
    return model

def notebook_model(name, path, ob, contents):
    model = base_model(name, path, 'notebook', contents)
    if ob is not None:
        model.update(
            last_modified = string_to_date(ob['_modified']),
            created = string_to_date(ob['_created'])
        )
    return model
