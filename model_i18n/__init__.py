import inspect

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from model_i18n import patches
from model_i18n.utils import import_module


VERSION = (0, 1, 0, 'alpha', 0)

def get_version():
    """ Returns application version """
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    if VERSION[3:] == ('alpha', 0):
        version = '%s pre-alpha' % version
    else:
        if VERSION[3] != 'final':
            version = '%s %s %s' % (version, VERSION[3], VERSION[4])
    return version


def _load_conf(*args, **kwargs):
    """  Ensures the configuration module gets imported when importing model_i18n. """
    # This is an idea from haystack app. We need to run the code that
    # follows only once, no matter how many times the main module is imported.
    # We'll look through the stack to see if we appear anywhere and simply
    # return if we do, allowing the original call to finish.
    stack = inspect.stack()
    for stack_info in stack[1:]:
        if '_load_conf' in stack_info[3]:
            return

    if not hasattr(settings, 'MODEL_I18N_CONF'):
        raise ImproperlyConfigured('You must define the MODEL_I18N_CONF setting, it should be a python module path string, for example "myproject.i18n_conf"')
    if not hasattr(settings, 'MODEL_I18N_MASTER_LANGUAGE'):
        raise ImproperlyConfigured('You must define the MODEL_I18N_MASTER_LANGUAGE setting.')

    # Import config module
    import_module(settings.MODEL_I18N_CONF)

_load_conf()
