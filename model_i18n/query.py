import operator

from django.db import connection
from django.db.models.sql import Query
from django.db.models.query_utils import Q
from django.db.models.sql.where import AND
from django.db.models.query import QuerySet

from model_i18n.conf import ATTR_BACKUP_SUFFIX, CURRENT_LANGUAGES
from model_i18n.utils import get_master_language


QN = connection.ops.quote_name # quote name


class QOuterJoins(Q):
    """ Q operator, allows to add custom LEFT OUTER joins to query """
    JOIN_TYPE = Query.LOUTER

    def __init__(self, **kwargs):
        """
        Each kwargs entry describes an LEFT OUTER join rule,
        keys will be join aliases while values must be tuples
        containing table to join with and a where like clause
        which defines the join.

        kwargs = { "join_alias": ("table", "clause"),
                   ... }
        """
        super(Q, self).__init__()
        self.joins = kwargs

    def add_to_query(self, query, used_aliases):
        """ Build joins and add them to queries """
        if self.joins:
            if not hasattr(query, 'custom_joins'):
                query.custom_joins = []
            jtype = self.JOIN_TYPE
            query.custom_joins += [
                " %s %s AS %s ON %s" % (jtype, table, alias, where)
                    for alias, (table, where) in self.joins.iteritems()
                        if alias not in used_aliases ]

    def __and__(self, right):
        """ AND operator. Useful to setup several joins rules """
        if not isinstance(right, QOuterJoins):
            return super(QOuterJoins, self).__and__(right)
        self.joins.update(right.joins)
        return self


class TransJoin(QOuterJoins):
    """Q Object which joins translation table and retrieves translatable
    attributes for selected language. Delegates join to QOuterJoins"""

    def __init__(self, model, lang):
        """ Init method.
        Args:
            model: translatable model
            lang: language desired
        """
        self.model = model

        trans_model = model._translation_model
        trans_opts = trans_model._transmeta

        alias = 'translation_%s' % lang
        self.data = { alias: lang }

        # Join data
        related_col  = trans_opts.master_field_name
        trans_table  = trans_model._meta.db_table
        trans_fk     = trans_model._meta.get_field(related_col).column
        master_table = model._meta.db_table
        master_pk    = model._meta.pk.column

        where = '%(m_table)s.%(m_pk)s = %(alias)s.%(t_fk)s %(and)s '\
                '%(alias)s.%(t_lang)s = "%(lang)s"' % {
                    'm_table': QN(master_table),
                    'm_pk':  QN(master_pk),
                    'and': AND,
                    'alias': alias,
                    't_fk': QN(trans_fk),
                    't_lang': QN(trans_opts.language_field_name),
                    'lang': lang }
        super(TransJoin, self).__init__(**{ alias: (trans_table, where) })

    def add_to_query(self, query, used_aliases):
        """
        Delegates join to QOuterJoins and adds the needed fields to 
        select list. The translateable fields will be in the form:
            <master model attribute name>_<language code>.
        Also current_languages attribute will be added with translation
        language codes joined by '_'.
        """
        # resolve joins
        super(TransJoin, self).add_to_query(query, used_aliases)
        trans_pk = QN(self.model._translation_model._meta.pk.column)
        fields = self.model._translation_model._transmeta.translatable_fields

        # add joined columns needed
        select = {}
        for alias, lang in self.data.iteritems():
            alias = QN(alias)
            select['id_%s' % lang] = '%s.%s' % (alias, trans_pk)
            select.update(('%s_%s' % (name, lang),
                           '%s.%s' % (alias, QN(name)))
                                for name in fields)
        select[CURRENT_LANGUAGES] = '"%s"' % '_'.join(self.data.itervalues())
        query.add_extra(select, None, None, None, None, None)

    def __and__(self, right):
        """ AND operator, useful to request more than one language
        in a single query:
            TransJoin(...) & TransJoin(...)
        """
        if isinstance(right, TransJoin) and self.model == right.model:
            self.data.update(right.data)
        return super(TransJoin, self).__and__(right)


class TransQuerySet(QuerySet):
    """ Translation QuerySet class
    QuerySet that joins with translation table, retrieves translated
    values and setup model attributes
    """
    def __init__(self, *args, **kwargs):
        self.languages = set()
        self.lang = None
        super(TransQuerySet, self).__init__(*args, **kwargs)

    def set_language(self, language):
        """ Defines/switch query set implicit language, attributes on
        result instances will be switched to this language on change_fields
        """
        return self.get_translations([language], language)

    def get_translations(self, languages, language=None):
        """ Adds any non-master new languages in parameter to requested
        languages list (self.languages) and build the new query joins rules

        We do not do anything if no new languages were passed

        `language` parameter will be set as implicit language (self.lang)
                   if passed
        """
        if language and language not in languages:
            languages.append(language)

        # filter added languages and master language
        master = get_master_language(self.model)
        new = set((lang for lang in languages
                        if lang and lang != master)) - self.languages

        if language not in (self.lang, master): # set implicit language
            self.lang = language

        if new: # if there's any language to add
            rules = [ TransJoin(self.model, lang) for lang in new ]
            join = reduce(operator.and_, rules) if len(rules) > 1 else rules[0]
            self.languages |= new
            return self.filter(join)
        return self

    def iterator(self):
        """ Invokes QuerySet iterator method and tries to change instance
        attributes with translated values if any translation was retrieved
        """
        for obj in super(TransQuerySet, self).iterator():
            yield self.change_fields(obj)

    def change_fields(self, instance):
        """Here we backups master values in <name>_<ATTR_BACKUP_SUFFIX>
        and overrides the default fields with their translated values using
        instance set_language.
        """
        trans_opts = instance._translation_model._transmeta

        # backup master value on <name>_<suffix> attribute
        apply(lambda name: setattr(instance,
                                   '_'.join((name, ATTR_BACKUP_SUFFIX)),
                                   getattr(instance, name, None)),
               trans_opts.translatable_fields)

        languages = filter(None, getattr(instance,
                                         CURRENT_LANGUAGES, '').split('_'))
        implicit = self.lang
        if implicit and implicit in languages:
            instance.switch_language(implicit) # switch to implicit language
        setattr(instance, CURRENT_LANGUAGES, languages)
        return instance

    def _clone(self, *args, **kwargs):
        """ _clone override, setups languages requested and current 
        selected language"""
        clone = super(TransQuerySet, self)._clone()
        clone.lang = self.lang
        clone.languages = self.languages
        return clone
