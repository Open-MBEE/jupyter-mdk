# Jupyter Model Development Kit (MDK)

[![Download](https://img.shields.io/pypi/v/jupyter-mdk)](https://pypi.org/project/jupyter-mdk/)

The Jupyter MDK will allow a dramatic expansion of the capabilities of interactive View creation, by allowing seamless integration with the [MMS](https://github.com/Open-MBEE/mms) along with leveraging collaborative Jupyter sessions.

It’s the vision that by utilising MMS’s element based storage and versioning scheme with Jupyter notebooks and Python REST client libraries that can be used within a notebook, the Jupyter MDK can provide a more interactive and powerful way to construct Views while keeping the narrative oriented presentation of View Editor.

# Quickstart

## Prerequisites

*   [JupyterLab](https://jupyterlab.readthedocs.io/en/stable/index.html) or [Jupyter Notebook](https://jupyter.readthedocs.io/en/latest/index.html)
    * Will be automatically installed below if not already available.
*   [pip](https://pip.pypa.io/en/stable/)
*   [Model Management System (MMS)](https://github.com/Open-MBEE/mms)

## Installation

1.  Install the latest [jupyter-mdk PyPi package](https://pypi.org/project/jupyter-mdk/) and its dependencies with `pip install jupyter-mdk`

2.  Locate your [Jupyter config file](https://jupyter-notebook.readthedocs.io/en/stable/config.html) or generate one with `jupyter notebook --generate-config` that defaults to `~/.jupyter`.

3.  Add configuration for MMS integration, e.g.

    ```python
    from mmscontents import MMSContentsManager

    c = get_config()

    # Tell Jupyter to use MMSContentsManager for all storage.
    c.NotebookApp.contents_manager_class = MMSContentsManager
    c.MMSContentsManager.mms_url = 'https://mms.yourcompany.com'
    c.MMSContentsManager.mms_project = '<project_id>'
    c.MMSContentsManager.mms_username = '<username>'
    c.MMSContentsManager.mms_password = '<password>'
    ```

4.  Run Jupyter as you normally would, e.g. `jupyter notebook`

5.  Test installation by creating a new notebook and saving. The notebook should *not* be in the local filesystem but instead accessible via MMS's REST API, e.g. `https://mms.yourcompany.com/projects/<project_id>/refs/master/notebooks`, to any user who has been granted access to the project both through MMS and Jupyter clients with Jupyter MDK similarly configured.