from os.path import dirname

from model_i18n.utils import import_module


def autodiscover(module_name='translations'):
    """
    Auto-discover translations.py files in installed app's directories, fail
    silently if not present. This forces an import on them to register any
    translation bits they may want.

    Based on django's contrib.admin autodiscover().
    """
    import imp
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        # For each app, we need to look for `module_name` in that app's
        # package. We can't use os.path here -- recall that modules may be
        # imported different ways (think zip files) -- so we need to get
        # the app's __path__ and look for translation.py on that path.

        # Step 1: find out the app's __path__ Import errors here will (and
        # should) bubble up, but a missing __path__ (which is legal, but weird)
        # fails silently. Try with dirname of module file if __path__ attribute
        # is not present.
        app_module = import_module(app)
        if hasattr(app_module, '__path__'):
            app_path = app_module.__path__
        else:
            app_path = dirname(app_module.__file__)

        # Step 2: use imp.find_module to find the app's `module_name`. For some
        # reason imp.find_module raises ImportError if the app can't be found
        # but doesn't actually try to import the module. So skip this app if
        # its `module_name` doesn't exist
        try:
            imp.find_module(module_name, app_path)
        except ImportError, e:
            continue

        # Step 3: import the app's translation file. If this has errors we want them
        # to bubble up.
        import_module('.'.join([app, module_name]))
