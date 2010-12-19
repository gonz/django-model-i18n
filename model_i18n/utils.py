from django.conf import settings


def get_default_language():
    """ Gets default project language from settings.TRANSLATIONS_DEFAULT_LANGUAGE
    if defined, or uses LANGUAGE_CODE
    """
    return getattr(settings, 'TRANSLATIONS_DEFAULT_LANGUAGE', None) or \
           getattr(settings, 'LANGUAGE_CODE', None)


def get_translation_opts(model):
    """ Returns model translation options """
    return model._translation_model._transmeta


def get_translation_opt(model, opt_name):
    """ Returns the value of an option on model translation options """
    return getattr(get_translation_opts(model), opt_name)


def get_master_language(model):
    """ Returns model master language defined, if any """
    return get_translation_opt(model, 'master_language')


def get_default_language(model):
    """ Returns model default language defined, if any """
    return get_translation_opt(model, 'default_language')


try:
    # importlib support (from Python 2.7) added on r10088
    # post 1.0
    from django.utils.importlib import import_module
except ImportError:
    import_module = __import__
