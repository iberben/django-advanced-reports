from django.conf.urls.defaults import *
from advanced_reports.views import *

urlpatterns = patterns('',
    url(r'^(?P<slug>[^/]+)/$', list, name='advanced_reports_list'),
    url(r'^(?P<slug>[^/]+)/form/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', ajax_form, name='advanced_reports_form'),
    url(r'^(?P<slug>[^/]+)/form/(?P<method>[^/]+)/(?P<object_id>[^/]+)/(?P<param>[^/]+)/$', ajax_form, name='advanced_reports_form'),
    url(r'^(?P<slug>[^/]+)/action/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', action, name='advanced_reports_action'),
    url(r'^(?P<slug>[^/]+)/ajax/(?P<method>[^/]+)/(?P<object_id>[^/]+)/$', ajax, name='advanced_reports_ajax'),
    url(r'^(?P<slug>[^/]+)/count/$', count, name='advanced_reports_count'),
)
