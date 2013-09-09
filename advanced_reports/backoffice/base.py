from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _
from advanced_reports.backoffice.api_utils import JSONResponse

from advanced_reports.defaults import action

from .decorators import staff_member_required

import json


class BackOfficeBase(object):
    """
    The base class of a Back Office application. Inherit from this class and
    define your own custom backoffice!
    """
    title = 'Untitled Backoffice'
    login_template = None
    model_to_bo_model = {}
    slug_to_bo_model = {}

    def __init__(self, name='backoffice', app_name='backoffice'):
        self.name = name
        self.app_name = app_name


    @property
    def urls(self):
        return patterns('',
                        url(r'^$', self.decorate(self.home), name='home'),
                        url(r'^logout/$', self.logout, name='logout'),
                        url(r'^api/(?P<method>[^/]+)/$', self.decorate(self.api), name='api'),
                        url(r'^api/$', self.decorate(self.api), name='api_home'),
                        url(r'^(?P<page_slug>[^/]+)/$', self.decorate(self.page), name='page'),
        ), self.app_name, self.name

    def decorate(self, view):
        return staff_member_required(self)(view)

    def default_context(self):
        return {'backoffice': self,
                'api_url': reverse(self.name + ':api_home', current_app=self.app_name)}

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

    def api(self, request, method=None):
        if not method:
            return JSONResponse(None)

        if request.method == 'GET':
            kwargs = dict(request.GET)
        elif request.method in ('POST', 'PUT'):
            kwargs = dict(json.loads(request.body))
        else:
            kwargs = {}

        fn = getattr(self, 'api_%s_%s' % (request.method.lower(), method), None)
        if fn is None:
            raise Http404
        return JSONResponse(fn(**kwargs))

    def serialize_model_instance(self, instance):
        bo_model = self.get_model(model=type(instance))
        serialized = {
            'id': instance.pk,
            'title': bo_model.get_title(instance),
            'model': bo_model.slug
        }
        serialized.update(bo_model.serialize_instance(instance))
        return serialized

    def serialize_model_instances(self, instances):
        return [self.serialize_model_instance(i) for i in instances]

    def register_model(self, bo_model):
        if not bo_model.slug in self.slug_to_bo_model:
            bo_model_instance = bo_model()
            self.slug_to_bo_model[bo_model.slug] = bo_model_instance
            self.model_to_bo_model[bo_model.model] = bo_model_instance

    def get_model(self, slug=None, model=None):
        if slug:
            return self.slug_to_bo_model.get(slug, None)
        else:
            return self.model_to_bo_model.get(model, None)

    def api_get_search(self, q):
        from django.contrib.auth.models import User
        users = User.objects.order_by('-pk')[:20]
        return self.serialize_model_instances(users)


class BackOfficeTab(object):
    slug = None
    title = None
    views = ()

    def __init__(self, slug, title, views):
        self.slug = slug
        self.title = title
        self.views = views

    def get_views(self):
        return self.views


class BackOfficeModel(object):
    slug = None
    model = None
    parent = None

    def get_title(self, instance):
        return unicode(instance)

    def serialize_instance(self, instance):
        return {}


def BackOfficeView(object):
    slug = None
