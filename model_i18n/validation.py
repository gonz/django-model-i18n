from django.db import models
from django.core.exceptions import ImproperlyConfigured

# Helpers

def check_isseq(cls, label, obj):
    """ Check if obj is a sequence """
    if not isinstance(obj, (list, tuple)):
        raise ImproperlyConfigured('"%s.%s" must be a list or tuple.' % (cls.__name__, label))


def check_fields(cls, model, opts, label, fields):
    """ Checks that fields listed on fields refers to valid model
    fields on model parameter """
    model_fields = [f.name for f in opts.fields]
    for field in fields:
        if not field in model_fields:
            raise ImproperlyConfigured('"%s.%s" refers to field "%s" that is missing in model "%s".'
                                       % (cls.__name__, label, field, model.__name__))

# Option validators

def validate_fields(cls, model):
    """ Validates model fields """
    opts = model._meta
    if hasattr(cls, 'fields'):
        check_isseq(cls, 'fields', cls.fields)
        check_fields(cls, model, opts, 'fields', cls.fields)
        if len(cls.fields) > len(set(cls.fields)):
            raise ImproperlyConfigured('There are duplicate field(s) in %s.fields' % cls.__name__)
    else:
        raise ImproperlyConfigured('%s.fields is a is a required attribute.' % cls.__name__)


# Global validator

def validate(cls, model):
    """ Validates if model is well configured """
    # Before we can introspect models, they need to be fully loaded so that
    # inter-relations are set up correctly. We force that here.
    models.get_apps()

    # Call each option validation
    validate_fields(cls, model)
