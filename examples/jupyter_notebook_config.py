#goes under ~/.jupyter/
from mmscontents import MMSContentsManager

c = get_config()

# Tell Jupyter to use MMSContentsManager for all storage.
c.NotebookApp.contents_manager_class = MMSContentsManager
c.MMSContentsManager.mms_url = 'https://mms.openmbee.org'
c.MMSContentsManager.mms_project = 'bb'
c.MMSContentsManager.mms_username = 'dummy'
c.MMSContentsManager.mms_password = 'dummy'
