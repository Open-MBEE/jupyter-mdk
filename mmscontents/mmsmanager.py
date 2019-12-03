import datetime
import mimetypes

from nbformat import reads
from notebook.services.contents.manager import ContentsManager
from tornado.web import HTTPError

from mmscontents.service import get_notebooks

DUMMY_CREATED_DATE = datetime.datetime.fromtimestamp(86400)
NBFORMAT_VERSION = 4


class MMSContentsManager(ContentsManager):
    def dir_exists(self, path):
        if path == '':
            return True
        return False

    def is_hidden(self, path):
        return False

    def file_exists(self, path=''):
        if path == '':
            return False
        return path in get_notebooks()

    def get(self, path, content=True, type=None, format=None):
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
        model = base_directory_model(path)
        if content:
            if not self.dir_exists(path):
                self.no_such_entity(path)
        return model

    def _notebook_model_from_path(self, path, content=False, format=None):
        model = base_model(path)
        model['type'] = 'notebook'
        if content:
            if not self.file_exists(path):
                self.no_such_entity(path)
            file_content = get_notebooks()[path]
            nb_content = reads(file_content, as_version=NBFORMAT_VERSION)
            self.mark_trusted_cells(nb_content, path)
            model['format'] = 'json'
            model['content'] = nb_content
            self.validate_notebook_model(model)
        return model

    def _file_model_from_path(self, path, content=False, format=None):
        model = base_model(path)
        model['type'] = 'file'
        if content:
            if not self.file_exists(path):
                self.no_such_entity(path)
            file_content = get_notebooks()[path]
            model["format"] = format or "text"
            model["content"] = file_content
            model["mimetype"] = mimetypes.guess_type(path)[0] or "text/plain"
            if format == "base64":
                model["format"] = format or "base64"
                from base64 import b64decode
                model["content"] = b64decode(content)
        return model

    def save(self, model, path):
        pass

    def delete_file(self, path):
        pass

    def rename_file(self, old_path, new_path):
        pass

    def guess_type(self, path):
        if path == '':
            return 'directory'
        return 'notebook'

    def do_error(self, msg, code=500):
        raise HTTPError(code, msg)

    def no_such_entity(self, path):
        self.do_error("No such entity: [{path}]".format(path=path), 404)

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
        created=DUMMY_CREATED_DATE,)
    return model