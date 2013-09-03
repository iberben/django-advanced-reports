from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http.response import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _

from advanced_reports.defaults import action

from .decorators import staff_member_required


class BackOfficeBase(object):
    """
    The base class of a Back Office application. Inherit from this class and
    define your own custom backoffice!
    """
    title = 'Untitled Backoffice'
    login_template = None

    def __init__(self, name='backoffice', app_name='backoffice'):
        self.name = name
        self.app_name = app_name


    @property
    def urls(self):
        return patterns('',
                        url(r'^$', self.decorate(self.home), name='home'),
                        url(r'^logout/$', self.logout, name='logout'),
                        url(r'^(?P<page_slug>[^/]+)/$', self.decorate(self.page), name='page'),
        ), self.app_name, self.name

    def decorate(self, view):
        return staff_member_required(self)(view)

    def default_context(self):
        return {'backoffice': self}

    @never_cache
    def logout(self, request, *args, **kwargs):
        from django.contrib.auth.views import logout
        kwargs['template_name'] = 'advanced_reports/backoffice/logout.html'
        kwargs['extra_context'] = self.default_context()
        return logout(request, *args, **kwargs)

    def page(self, request, *args, **kwargs):
        return render_to_response('advanced_reports/backoffice/page.html',
                                  self.default_context(),
                                  context_instance=RequestContext(request))

    def home(self, request):
        return render_to_response('advanced_reports/backoffice/page.html',
                                  self.default_context(),
                                  context_instance=RequestContext(request))

    def api(self, request, *args, **kwargs):
        return HttpResponse('null')


