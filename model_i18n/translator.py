import new
import copy

from django.conf import settings
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy as _

from model_i18n import managers
from model_i18n.options import ModelTranslation
from model_i18n.exceptions import AlreadyRegistered
from model_i18n.conf import CURRENT_LANGUAGES, CURRENT_LANGUAGE, \
                            ATTR_BACKUP_SUFFIX
from model_i18n.admin import setup_admin


__all__ = ['register', 'ModelTranslation']


class Translator(object):
    """
    Manages all the site's multilingual models.

    Every multilingual model must be registered to a global (single) instance
    of this class, so it can be properly set up (see `register` method bellow).
    This class should never be instantiated, use this module's API functions.
    """
    def __init__(self):
        self._registry = {} # model_class class -> translation_class instance

    def register(self, master_model, translation_class=None, **options):
        """
        Sets everything up for the given master model using a set of
        registration options (ModelTranslation attributes).
  
        If a translation class isn't given, it will use ModelTranslation (the
        default translation options). If keyword arguments are given -- e.g.,
        fields -- they'll overwrite the translation_class attributes.
        """
        if master_model in self._registry:
            raise AlreadyRegistered('The model "%s" has is already registered for translation' % master_model.__name__)
  
        # If not translation_class given use default options.
        if not translation_class:
            translation_class = ModelTranslation
        # If we got **options then dynamically construct a subclass of translation_class with those **options.
        if options:
            translation_class = type('%sTranslation' % master_model.__name__, (translation_class,), options)

        # Validate the translation_class (just in debug mode).
        if settings.DEBUG:
            from model_i18n.validation import validate
            validate(translation_class, master_model)

        opts = translation_class(master_model)

        # Set up master_model as a multilingual model using translation_class options
        translation_model = self.create_translation_model(master_model, opts)
        models.register_models(master_model._meta.app_label, translation_model)
        self.setup_master_model(master_model, translation_model) # This probably will become a class method soon.
        setup_admin(master_model, translation_model) # Setup django-admin support

        # Register the multilingual model and the used translation_class.
        self._registry[master_model] = opts


    def create_translation_model(self, master_model, opts):
        """
        Creates a model for storing `master_model`'s translations based on
        given registration options class.
        """
        attrs = {'__module__': master_model.__module__}

        class Meta:
            app_label = master_model._meta.app_label
            db_table = opts.db_table
        attrs['Meta'] = Meta

        class TranslationMeta:
            default_language = opts.default_language
            master_language = opts.master_language
            translatable_fields = opts.fields
            language_field_name = opts.language_field_name
            master_field_name = opts.master_field_name
            related_name = opts.related_name
        attrs['_transmeta'] = TranslationMeta

        # Common translation model fields
        common_fields = {
            # Translation language
            opts.language_field_name: models.CharField(db_index=True,
                verbose_name=_('language'), max_length=10,
                choices=settings.LANGUAGES),
            # Master instance FK
            opts.master_field_name: models.ForeignKey(master_model,
                verbose_name=_('master'), related_name=opts.related_name),
        }
        attrs.update(common_fields)

        # Add translatable fields
        model_name = master_model.__name__ + 'Translation'
        for field in master_model._meta.fields:
            if field.name not in opts.fields:
                continue
            if field.name in common_fields:
                raise ImproperlyConfigured, ('%s: %s field name "%s" conflicts '
                    'with the language or master FK common fields, try '
                    'changing language_field_name or master_field_name '
                    'ModelTranslation option.'
                    % (model_name, master_model.__name__, field.attname))
            newfield = copy.copy(field)
            newfield.primary_key = False
            newfield._unique = False # FIXME (unique_together)

            attrs[newfield.name] = newfield
        # setup i18n languages on master model for easier access
        master_model.i18n_languages = settings.LANGUAGES
        master_model.i18n_default_language = opts.master_language
        return type(model_name, (models.Model,), attrs)

    def setup_master_model(self, master_model, translation_model):
        """
        Sets up master model and its managers for working with translations:

        Master model:
            * master_model._translation_model: Translation model
            * master_model.switch_language: language switcher

        Managers:
            * See setup_manager
        """
        # Master model
        master_model._translation_model = translation_model
        master_model.switch_language = switch_language
        # Managers
        # FIXME: We probably should we add a translation option to ignore some
        # manager (so users can create non multilingual managers)
        # XXX: Not sure what to do with _meta.abtract_managers
        for c, fname, manager in master_model._meta.concrete_managers:
            self.setup_manager(manager) 

    def setup_manager(self, manager):
        """
        Patch for master model's managers.
            * model.objects.set_language: Sets the current language.
            * model.objects.get_query_set: All querysets are TransQuerySet types
        """
        # Backup get_query_set to use in translation get_query_set
        manager.get_query_set_orig = manager.get_query_set
        for method_name in ('get_query_set', 'set_language'):
            # Add translation method into the manager instance
            setattr(manager, method_name,
                new.instancemethod(getattr(managers, method_name), manager, manager.__class__))


def switch_language(instance, lang=None):
    """Here we overrides the default fields with their translated
    values. We keep the default if there's no value in the translated
    field or more than one language was requested.
        instance.switch_language('es')
            will load attribute values for 'es' language
        instance.switch_language()
            will load attribute values for master default language
    """
    current_languages = getattr(instance, CURRENT_LANGUAGES, None)
    current = getattr(instance, CURRENT_LANGUAGE, None)

    if current_languages: # any translation?
        trans_meta = instance._translation_model._transmeta
        fields = trans_meta.translatable_fields
        if not lang or lang == trans_meta.master_language: # use defaults
            for name in fields:
                value = getattr(instance, '_'.join((name, ATTR_BACKUP_SUFFIX)),
                                None)
                setattr(instance, name, value)
        elif lang in current_languages and lang != current: # swtich language
            for name in fields:
                value = getattr(instance, '_'.join((name, lang)), None)
                if value is not None: # Ignore None, means not translated
                    setattr(instance, name, value)
        setattr(instance, CURRENT_LANGUAGE, lang)


# Just one Translator instance is needed.
_translator = Translator()

## API

def register(model, translation_class=None, **options):
    """ Register and set up `model` as a multilingual model. """
    return _translator.register(model, translation_class, **options)
