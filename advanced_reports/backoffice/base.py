from collections import defaultdict
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

    def register_model(self, bo_model):
        if not bo_model.slug in self.slug_to_bo_model:
            bo_model_instance = bo_model()
            self.slug_to_bo_model[bo_model.slug] = bo_model_instance
            self.model_to_bo_model[bo_model.model] = bo_model_instance
            self.link_relationship(bo_model_instance)

    def get_model(self, slug=None, model=None):
        if slug:
            return self.slug_to_bo_model.get(slug, None)
        else:
            return self.model_to_bo_model.get(model, None)

    def serialize_model_instance(self, instance, include_children=False):
        bo_model = self.get_model(model=type(instance))
        if include_children:
            return bo_model.get_serialized(instance)
        else:
            return bo_model.get_serialized_with_children(instance)

    def serialize_model_instances(self, instances, include_children=False):
        return [self.serialize_model_instance(i) for i in instances]

    def link_relationship(self, bo_model):
        if bo_model.parent_field:
            parent_field = bo_model.model._meta.get_field(bo_model.parent_field)
            parent_model = parent_field.rel.to
            parent_bo_model = self.get_model(model=parent_model)
            if parent_bo_model:
                if parent_bo_model.children is None:
                    parent_bo_model.children = {}
                if not bo_model.slug in parent_bo_model.children:
                    parent_bo_model.children[bo_model.slug] = bo_model

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
    parent_field = None
    verbose_name = None
    verbose_name_plural = None
    children = None
    has_header = True
    priority = 1

    def get_title(self, instance):
        return unicode(instance)

    def serialize(self, instance):
        return {}

    def get_serialized(self, instance):
        serialized = {
            'id': instance.pk,
            'title': self.get_title(instance),
            'model': self.slug
        }
        serialized.update(self.serialize(instance))
        return serialized

    def get_children_by_model(self, instance, bo_model):
        child_field = bo_model.model._meta.get_field(bo_model.parent_field)
        related_name = child_field.rel.related_name or ('%s_set' % bo_model.model.__name__.lower())
        return getattr(instance, related_name).all()

    def get_serialized_children_by_model(self, instance, bo_model):
        children = self.get_children_by_model(instance, bo_model)
        serialized = bo_model.serialize_meta()
        serialized['children'] = [bo_model.get_serialized(c) for c in children]
        return serialized

    def serialize_meta(self):
        return {
            'slug': self.slug,
            'verbose_name': self.verbose_name,
            'verbose_name_plural': self.verbose_name_plural,
            'has_header': self.has_header
        }

    def get_children(self, instance):
        if not self.children:
            return ()
        child_models = sorted(self.children.values(), key=lambda m: m.priority)
        return [self.get_serialized_children_by_model(instance, m) for m in child_models]

    def get_serialized_with_children(self, instance):
        serialized = self.get_serialized(instance)
        serialized['children'] = self.get_children(instance)
        return serialized



def BackOfficeView(object):
    slug = None
