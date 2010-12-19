from django.conf.urls.defaults import *
from django.contrib import admin
from model_i18n import loaders


admin.autodiscover()
loaders.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)
