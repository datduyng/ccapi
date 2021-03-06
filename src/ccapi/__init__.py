# imports - standard imports
import os.path as osp

# imports - module imports
from ccapi.__attr__     import (
    __name__,
    __version__,
    __author__
)
from ccapi.api          import Client
from ccapi.constant     import PATH
from ccapi.model        import *
from ccapi.core.config  import Configuration
from ccapi._compat      import iterkeys

def load_model(name, *args, **kwargs):
    if not name in iterkeys(PATH["MODELS"]):
        raise ValueError("Model %s not found." % name)
    else:
        path = PATH["MODELS"][name]

    client = kwargs.get("client", Client())
    model  = client.read(path)

    return model