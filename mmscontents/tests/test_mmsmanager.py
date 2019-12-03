from unittest import TestCase
from unittest.mock import patch, Mock

# from notebook.services.contents.tests.test_manager import TestContentsManager
from nbformat.reader import NotJSONError
from tornado.web import HTTPError

from mmscontents.mmsmanager import MMSContentsManager


class TestMMSContentsManager(TestCase):
    def setUp(self):
        self.contents_manager = MMSContentsManager()

    def test_root_dir_exists(self):
        self.assertTrue(self.contents_manager.dir_exists(''))

    def test_non_root_dir_does_not_exist(self):
        self.assertFalse(self.contents_manager.dir_exists('foo'))

    def test_root_dir_is_not_hidden(self):
        self.assertFalse(self.contents_manager.is_hidden(''))

    @patch('mmscontents.mmsmanager.get_notebooks')
    def test_file_exists(self, mock_get_notebooks):
        mock_get_notebooks.return_value = {'foo': 'bar'}

        self.assertTrue(self.contents_manager.file_exists('foo'))
        self.assertFalse(self.contents_manager.file_exists('bar'))

        self.assertFalse(self.contents_manager.file_exists(''))

    @patch('mmscontents.mmsmanager.get_notebooks')
    def test_get(self, mock_get_notebooks):
        mock_get_notebooks.return_value = {'foo': 'bar', 'empty': '{"cells":[]}'}

        self.assertIsNotNone(self.contents_manager.get('empty'))
        self.assertIsNotNone(self.contents_manager.get('empty', type='notebook'))
        self.assertIsNotNone(self.contents_manager.get('foo', type='file'))
        self.assertIsNotNone(self.contents_manager.get(''))

        with self.assertRaises(NotJSONError):
            self.contents_manager.get('foo')
        with self.assertRaises(HTTPError):
            self.contents_manager.get('bar')
        with self.assertRaises(HTTPError):
            self.contents_manager.get('invalid_dir/', type='directory')
