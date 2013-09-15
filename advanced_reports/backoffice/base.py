from collections import defaultdict
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext as _
from advanced_reports.backoffice.api_utils import JSONResponse
from advanced_reports.backoffice.models import SearchIndex
from advanced_reports.backoffice.search import convert_to_raw_tsquery

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
    model_template = 'advanced_reports/backoffice/model-base.html'

    def __init__(self, name='backoffice', app_name='backoffice'):
        self.name = name
        self.app_name = app_name


    def define_urls(self):
        return ()

    @property
    def urls(self):
        return patterns('',
                        url(r'^$', self.decorate(self.home), name='home'),
                        url(r'^logout/$', self.logout, name='logout'),
                        url(r'^api/(?P<method>[^/]+)/$', self.decorate(self.api), name='api'),
                        url(r'^api/$', self.decorate(self.api), name='api_home'),
                        *self.define_urls()
        ), self.app_name, self.name

    def decorate(self, view):
        return staff_member_required(self)(view)

    def default_context(self):
        return {'backoffice': self,
                'api_url': reverse(self.name + ':api_home', current_app=self.app_name),
                'root_url': reverse(self.name + ':home', current_app=self.app_name)}

    @never_cache
    def logout(self, request, *args, **kwargs):
        from django.contrib.auth.views import logout
        kwargs['template_name'] = 'advanced_reports/backoffice/logout.html'
        kwargs['extra_context'] = self.default_context()
        return logout(request, *args, **kwargs)

    def home(self, request):
        return render_to_response(self.model_template,
                                  self.default_context(),
                                  context_instance=RequestContext(request))

    def api(self, request, method=None):
        if not method:
            return JSONResponse(None)

        if request.method == 'GET':
            kwargs = dict(request.GET)
        elif request.method in ('POST', 'PUT'):
            if request.META['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
                kwargs = dict(request.POST)
            else:
                kwargs = dict(json.loads(request.body))
        else:
            kwargs = {}

        fn = getattr(self, 'api_%s_%s' % (request.method.lower(), method), None)
        if fn is None:
            raise Http404
        return JSONResponse(fn(request, **kwargs))

    ######################################################################
    # Model Registration
    ######################################################################
    model_to_bo_model = {}
    slug_to_bo_model = {}

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

    ######################################################################
    # View Registration
    ######################################################################
    slug_to_bo_view = {}

    def register_view(self, bo_view):
        if not bo_view.slug in self.slug_to_bo_view:
            bo_view_instance = bo_view()
            self.slug_to_bo_view[bo_view.slug] = bo_view_instance

    def get_view(self, slug):
        return self.slug_to_bo_view.get(slug, None)

    ######################################################################
    # Search
    ######################################################################
    def serialize_search_result(self, index):
        bo_model = self.get_model(slug=index.model_slug)
        instance = bo_model.model.objects.get(pk=index.model_id)
        return bo_model.get_serialized_with_children(instance)

    def serialize_search_results(self, indices):
        return [self.serialize_search_result(i) for i in indices]

    def search(self, query, filter_on_model_slug=None, page=1, page_size=20):
        if query == u'':
            return ()
        f = dict(backoffice_instance=self.name)
        if filter_on_model_slug:
            f['model_slug'] = filter_on_model_slug
        ts_query = convert_to_raw_tsquery(query)
        indices = SearchIndex.objects.search(ts_query, raw=True).filter(**f)[(page-1)*page_size:page*page_size]
        return self.serialize_search_results(indices)

    ######################################################################
    # Internal JSON API
    ######################################################################
    def api_get_search(self, request, q, page=None, filter_model=None):
        page = int(page[0]) if page else 1
        filter_model = filter_model[0] if filter_model else None
        return self.search(q[0], page=page, filter_on_model_slug=filter_model)

    def api_get_search_preview(self, request, q, filter_model=None):
        return self.search(q[0], page_size=5, filter_on_model_slug=filter_model)

    def api_get_model(self, request, model_slug, pk):
        bo_model = self.get_model(slug=model_slug[0])
        obj = bo_model.model.objects.get(pk=pk[0])
        serialized = bo_model.get_serialized(obj)
        serialized['meta'] = bo_model.serialize_meta()
        return serialized

    def api_get_view(self, request, slug=None, **kwargs):
        bo_view = self.get_view(slug[0])
        return bo_view.get_serialized(request, **kwargs)

    def api_post_view(self, request, slug=None, **kwargs):
        bo_view = self.get_view(slug[0])
        return bo_view.get_serialized_post(request, **kwargs)

    def api_post_view_action(self, request, method=None, params=None, view_params=None):
        bo_view = self.get_view(view_params.pop('slug'))
        fn = getattr(bo_view, method, None)
        if not fn:
            raise Http404(u'Cannot find method %s on view %s' % (method, bo_view.slug))
        fn(request, params=params, **view_params)


class BackOfficeTab(object):
    slug = None
    title = None
    template = None

    def __init__(self, slug, title, template):
        self.slug = slug
        self.title = title
        self.template = template

    def get_serialized_meta(self):
        return {
            'slug': self.slug,
            'title': self.title
        }

    def get_serialized(self, instance):
        return {
            'slug': self.slug,
            'title': self.title,
            'template': render_to_string(self.template, {'instance': instance})
        }


class BackOfficeModel(object):
    slug = None
    model = None
    parent_field = None
    verbose_name = None
    verbose_name_plural = None
    children = None
    priority = 1
    has_header = True
    collapsed = True
    header_template = None
    tabs = ()

    def get_title(self, instance):
        return unicode(instance)

    def serialize(self, instance):
        return {}

    def render_template(self, instance):
        if self.header_template:
            context = {
                'instance': instance
            }
            return render_to_string(self.header_template, context)
        return u''

    def get_serialized(self, instance):
        serialized = {
            'id': instance.pk,
            'title': self.get_title(instance),
            'model': self.slug,
            'path': '/%s/%d/' % (self.slug, instance.pk),
            'header_template': self.render_template(instance),
            'tabs': dict((t.slug, t.get_serialized(instance)) for t in self.tabs),
            'is_object': True
        }
        serialized.update(self.serialize(instance))
        return serialized

    def get_children_by_model(self, instance, bo_model):
        child_field = bo_model.model._meta.get_field(bo_model.parent_field)
        related_name = child_field.rel.related_name or ('%s_set' % bo_model.model.__name__.lower())
        return getattr(instance, related_name).all()

    def get_serialized_children_by_model(self, instance, bo_model):
        children = self.get_children_by_model(instance, bo_model)
        serialized_children = [bo_model.get_serialized(c) for c in children]
        if bo_model.has_header:
            serialized = bo_model.serialize_meta()
            serialized['children'] = serialized_children
            return [serialized]
        else:
            return serialized_children

    def serialize_meta(self):
        return {
            'slug': self.slug,
            'verbose_name': self.verbose_name,
            'verbose_name_plural': self.verbose_name_plural,
            'has_header': self.has_header,
            'collapsed': self.collapsed,
            'tabs': [t.get_serialized_meta() for t in self.tabs],
            'is_meta': True
        }

    def get_children(self, instance):
        if not self.children:
            return ()
        child_models = sorted(self.children.values(), key=lambda m: m.priority)
        return sum((self.get_serialized_children_by_model(instance, m) for m in child_models), [])

    def get_serialized_with_children(self, instance):
        serialized = self.get_serialized(instance)
        serialized['children'] = self.get_children(instance)
        return serialized

    def reindex(self, instance, backoffice_instance):
        index_text = self.search_index(instance)
        index, created = SearchIndex.objects.get_or_create(backoffice_instance=backoffice_instance,
                                                           model_slug=self.slug,
                                                           model_id=instance.pk,
                                                           defaults={'to_index': index_text})
        if not created:
            index.to_index = index_text
            index.save()

    def search_index(self, instance):
        return unicode(instance)



class BackOfficeView(object):
    slug = None

    def get_serialized(self, request, **kwargs):
        serialized = {
            'slug': self.slug,
            'content': self.get(request, **kwargs)
        }
        return serialized

    def get_serialized_post(self, request, **kwargs):
        serialized = {
            'slug': self.slug,
            'content': self.post(request, **kwargs)
        }
        return serialized

    def get(self, request, **kwargs):
        return repr(kwargs)

    def post(self, request, **kwargs):
        return repr(kwargs)
