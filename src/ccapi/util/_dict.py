# imports - standard imports
import collections

# imports - compatibility imports
from ccapi._compat import zip

def merge_dict(*args):
    merged = dict()

    for arg in args:
        copy = arg.copy()
        merged.update(copy)

    return merged

def dict_from_list(keys, values):
    return dict(zip(keys, values))

def autodict():
    _autodict = collections.defaultdict(autodict)
    return _autodict