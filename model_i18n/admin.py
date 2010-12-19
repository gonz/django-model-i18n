from django.contrib import admin
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from django.utils.encoding import force_unicode
from django.utils.decorators import method_decorator


from model_i18n.exceptions import OptionWarning
from model_i18n.utils import get_translation_opt
from model_i18n.conf import CHANGE_TPL, CHANGE_TRANSLATION_TPL


def setup_admin(master_model, translation_model):
    """Setup django-admin support.
    Support is provided with a new set of urls that and custom views
    that allow i18n fields edition and aggregation for defined languages.
    """
    model_admin = admin.site._registry.get(master_model)
    if not model_admin:
        # register model in django-admin with default values
        admin.site.register(master_model, admin.ModelAdmin)
        model_admin = admin.site._registry.get(master_model)
    elif model_admin.change_form_template:
        # default change view is populated with links to i18n edition
        # sections but won't be available if change_form_template is
        # overrided on model admin options, in such case, extend from
        # model_i18n/template/change_form.html
        msg = '"%s" overrides change_form_template, extend %s to get i18n support' \
                    % (model_admin.__class__, CHANGE_TPL)
        warnings.warn(OptionWarning(msg))

    # setup admin methods, etc
    model_admin.change_form_template = CHANGE_TPL
    model_admin.__class__.get_urls_orig = model_admin.__class__.get_urls
    model_admin.__class__.get_urls = get_urls
    model_admin.__class__.i18n_change_view = i18n_change_view


def get_urls(instance):
    """Admin get_urls override to add i18n edition view. Last url is
    for django-admin change view, it's a bit gredy, so we kept it back
    to the end."""
    # original urls
    urls = instance.get_urls_orig()
    return urls[:-1] + patterns('', 
                url(r'^(?P<obj_id>\d+)/(?P<language>[a-z]{2})/$',
                    instance.i18n_change_view),
                urls[-1])


@method_decorator(csrf_protect)
@transaction.commit_on_success
def i18n_change_view(instance, request, obj_id, language):
    """Change view for i18n values for current instance. This is a
    simplified django-admin change view which displays i18n fields
    for current model/id."""
    opts = instance.model._meta
    obj = instance.get_object(request, obj_id)

    if not instance.has_change_permission(request, obj):
        raise PermissionDenied

    if obj is None:
        msg = _('%(name)s object with primary key %(key)r does not exist.')
        raise Http404(msg % {'name': force_unicode(opts.verbose_name),
                             'key': escape(obj_id)})

    if language not in dict(settings.LANGUAGES):
        raise Http404(_('Incorrect language %(lang)s') % {'lang': language})

    master_language = get_translation_opt(obj, 'master_language')
    if language == master_language:
        # redirect to instance admin on default language
        return HttpResponseRedirect('../')

    fields = get_translation_opt(obj, 'translatable_fields')
    lang_field = get_translation_opt(obj, 'language_field_name')
    master_field = get_translation_opt(obj, 'master_field_name')

    try:
        trans = obj.translations.get(**{lang_field: language})
    except obj._translation_model.DoesNotExist: # new translation
        trans = obj._translation_model(**{lang_field: language,
                                          master_field: obj})

    ModelForm = modelform_factory(obj._translation_model, fields=fields)

    if request.method == 'POST':
        form = ModelForm(instance=trans, data=request.POST,
                         files=request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(request.path)
    else:
        form = ModelForm(instance=trans)

    adminform = admin.helpers.AdminForm(form, [(None, {'fields': fields})],
                                        {}, None)

    context = {
        'title': _('Translation %s') % force_unicode(opts.verbose_name),
        'adminform': adminform, 'original': obj,
        'is_popup': request.REQUEST.has_key('_popup'),
        'errors': admin.helpers.AdminErrorList(form, None),
        'root_path': instance.admin_site.root_path,
        'app_label': opts.app_label, 'trans': True, 'lang': language,
        'current_language': dict(settings.LANGUAGES)[language],
        # override some values to provide an useful template
        'add': False, 'change': True,
        'has_change_permission_orig': True, # backup
        'has_add_permission': False, 'has_change_permission': False,
        'has_delete_permission': False, # hide delete link for now
        'has_file_field': True, 'save_as': False, 'opts': instance.model._meta,
    }

    ctx = RequestContext(request, current_app=instance.admin_site.name)
    return render_to_response(CHANGE_TRANSLATION_TPL, context,
                              context_instance=ctx)
