from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from advanced_reports.backoffice.examples.backoffice import test_backoffice

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'advreport_test_project.views.home', name='home'),
    # url(r'^advreport_test_project/', include('advreport_test_project.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^test-backoffice/', include(test_backoffice.urls))
)
