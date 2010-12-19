""" Monkey patches module """
from model_i18n.conf import MULTIDB_SUPPORT

###
# Add support for custom_joins rules used by query.QOuterJoins
from django.db.models.sql import Query

# Patch get_from_clause method so custom_joins are processed propperly
# On django pre r11952 (no multi-db support), get_from_clause is defined
# on Query class, but on post r11952, compiler module was added to
# django.db.models.sql which contains SQLCompiler with get_from_clause
if MULTIDB_SUPPORT:
    from django.db.models.sql.compiler import SQLCompiler
    get_custom_joins = lambda compiler: getattr(compiler.query,
                                                'custom_joins', [])
    GetFromClauseClass = SQLCompiler
else:
    get_custom_joins = lambda query: getattr(query, 'custom_joins', [])
    GetFromClauseClass = Query

# Backup django methods
dj_clone = Query.clone
dj_get_from_clause = GetFromClauseClass.get_from_clause


def MP_get_from_clause(self):
    """ Add custom_joins rules built by a QOuterJoins instance
    to result from django get_from_clause method """
    result, params = dj_get_from_clause(self) # django
    return (result + get_custom_joins(self), params)

def MP_clone(self, *args, **kwargs):
    """ Also clone custom_joins attribute (if any) when cloning a
    query object """
    query = dj_clone(self, *args, **kwargs) # django
    if hasattr(self, 'custom_joins'):
        query.custom_joins = self.custom_joins[:]
    return query

# Patch django
Query.clone = MP_clone
GetFromClauseClass.get_from_clause = MP_get_from_clause
