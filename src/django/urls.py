from django.conf.urls.defaults import *
from ui_django import settings


urlpatterns = patterns('view',
    #(r'^pyglossary/(?P<path>.*)$', 'pyglossary'),
    (r'^pyglossary', 'index'),
    (r'^$', 'index'),
    (r'^index', 'index'),## r'^(pyglossary)?index'
) + patterns('',
    (r'^img/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.IMAGES_DIR}),
    (r'^js/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.JS_DIR}),
)



