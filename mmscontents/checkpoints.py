from notebook.services.contents.checkpoints import GenericCheckpointsMixin, Checkpoints
import datetime

DUMMY_CREATED_DATE = datetime.datetime.fromtimestamp(86400)

class NoOpCheckpoints(GenericCheckpointsMixin, Checkpoints):    
    """requires the following methods:"""
    def create_file_checkpoint(self, content, format, path):
        """ -> checkpoint model
        [
            cast(remote_checkpoints.c.id, Unicode),
            remote_checkpoints.c.last_modified,
        ]"""
        return {'id': 'random', 'last_modified': DUMMY_CREATED_DATE}
    def create_notebook_checkpoint(self, nb, path):
        """ -> checkpoint model"""
        return {'id': 'random', 'last_modified': DUMMY_CREATED_DATE}
    def get_file_checkpoint(self, checkpoint_id, path):
        """ -> {'type': 'file', 'content': <str>, 'format': {'text', 'base64'}}"""
    def get_notebook_checkpoint(self, checkpoint_id, path):
        """ -> {'type': 'notebook', 'content': <output of nbformat.read>}"""
    def delete_checkpoint(self, checkpoint_id, path):
        """deletes a checkpoint for a file"""
    def list_checkpoints(self, path):
        """returns a list of checkpoint models for a given file,
        default just does one per file
        """
        return []
    def rename_checkpoint(self, checkpoint_id, old_path, new_path):
        """renames checkpoint from old path to new path"""