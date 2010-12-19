from django.conf import settings

from model_i18n.conf import DEFAULT_LANGUAGE_FIELD_NAME, RELATED_NAME, \
                            DEFAULT_MASTER_FIELD_NAME, TRANSLATION_TABLE_SUFFIX


class ModelTranslation(object):
    """ Translation model options
    Available options so far:

        - fields [list or tuple]
            List of field names that must be translatable

        - default_language [string]
            Default language used to retrieve translations from database
              * active
                  Current active language from django.utils.translation.get_language()
              * master
                  Master defined language (see master_language)
              * language code
                  Any valid language code

        - master_language [string]
            The language of the master model content, overrides
            MODEL_I18N_MASTER_LANGUAGE setting

        - related_name
            Master model related name, by default RELATED_NAME translation model
            will be accessible throw this name

        - db_table [string]
            Table name which holds translation for a model, if not defined, then
            name is built using master table and TRANSLATION_TABLE_SUFFIX suffix

        - language_field_name [string]
            Column name which holds translation language, LANG_COLUMN_NAME by
            default

        - master_field_name [string]
            Column name which holds master model pk, REL_COLUMN_NAME by default
    """
    # translatable fields
    fields = None

    # language
    default_language = 'active'
    master_language = settings.MODEL_I18N_MASTER_LANGUAGE

    # table
    db_table = None
    language_field_name = DEFAULT_LANGUAGE_FIELD_NAME
    master_field_name = DEFAULT_MASTER_FIELD_NAME

    # master related name
    related_name = RELATED_NAME

    def __init__(self, model):
        self.model = model
        # Default db_table
        if self.db_table is None:
            self.db_table = '_'.join([ model._meta.db_table,
                                       TRANSLATION_TABLE_SUFFIX ])
        super(ModelTranslation, self).__init__()
