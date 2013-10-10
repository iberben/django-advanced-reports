from collections import defaultdict
from django.conf.urls import patterns, url
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save, post_delete, pre_delete
from django.http import Http404
from django.http.response import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from advanced_reports.backoffice.api_utils import JSONResponse, ViewRequestParameters
from advanced_reports.backoffice.models import SearchIndex
from advanced_reports.backoffice.search import convert_to_raw_tsquery

from .decorators import staff_member_required

import json


class AutoSlug(object):
    def __init__(self, remove_suffix=None):
        self.remove_suffix = remove_suffix

    def __get__(self, instance, owner):
        slug = owner.__name__
        if self.remove_suffix and slug.endswith(self.remove_suffix):
            slug = slug[:-len(self.remove_suffix)]
        return slug.lower()


class BackOfficeBase(object):
    """
    The base class of a Back Office application. Inherit from this class and
    define your own custom backoffice!
    """

    #: The title of the BackOffice application. This is used on pages that
    #: inherit from the ``model_template``.
    title = 'Untitled Backoffice'

    #: The template file that will be used to show models. It has to define
    #: an ng-view inside of it. Please extend the default template if you
    #: want to specify your own navigation (which you will probably want
    #: to do) and put your own template here.
    model_template = 'advanced_reports/backoffice/model-base.html'

    def __init__(self, name='backoffice', app_name='backoffice'):
        """
        Constructor for a BackOfficeBase implementation.

        :param name: the instance name for this implementation used for
        Django url namespacing.
        :param app_name: the app name for this implementation. In most cases
        can be just left alone.
        :return: a BackOfficeBase implementation instance.
        """
        self.name = name
        self.app_name = app_name


    def define_urls(self):
        """
        Implement this to add some custom url patterns to a backoffice.
        They will automatically get the proper namespacing. For example,
        if your backoffice is called "helpdesk" and your url is called
        "stats", you must use ``{% url 'helpdesk:stats' %}`` in your
        templates.

        :return: a tuple/list of url patterns (not using ``patterns()``!)
        """
        return ()

    @property
    def urls(self):
        """
        The actual url patterns for this backoffice. You can include
        these in your main urlconf.

        :return: url patterns
        """
        return patterns('',
                        url(r'^$', self.decorate(self.home), name='home'),
                        url(r'^logout/$', self.logout, name='logout'),
                        url(r'^api/(?P<method>[^/]+)/$', self.decorate(self.api), name='api'),
                        url(r'^api/$', self.decorate(self.api), name='api_home'),
                        *self.define_urls()
        ), self.app_name, self.name

    def decorate(self, view):
        """
        Implement this to add some custom decoration for the internal
        Django views for this backoffice.

        :param view: the view to decorate
        :return: the decorated view
        """
        # TODO: add permissions
        return staff_member_required(self)(view)

    def default_context(self):
        """
        Default template context values for internal backoffice page.

        :return: context dict
        """
        return {'backoffice': self,
                'api_url': reverse(self.name + ':api_home', current_app=self.app_name),
                'root_url': reverse(self.name + ':home', current_app=self.app_name)}

    @never_cache
    def logout(self, request, *args, **kwargs):
        """
        Calls ``django.contrib.auth.views.logout`` with a custom template and
        extra context.
        """
        from django.contrib.auth.views import logout
        kwargs['template_name'] = 'advanced_reports/backoffice/logout.html'
        kwargs['extra_context'] = self.default_context()
        return logout(request, *args, **kwargs)

    def home(self, request):
        """
        The main Django view for this backoffice.
        """
        return render_to_response(self.model_template,
                                  self.default_context(),
                                  context_instance=RequestContext(request))

    def api(self, request, method=None):
        """
        A very simple REST-like API implementation which just passes requests
        on to the right functions.

        An instance of ``advanced_reports.backoffice.api_utils.ViewRequestParameters``
        will be assigned to the ``request`` as ``view_params``.

        :param request: A HTTP request where ``view_params`` will be attached to.
        :param method: The actual instance method of this backoffice class that will
        be called.
        :return: a JSONResponse
        """
        if not method:
            return JSONResponse(None)

        request.view_params = ViewRequestParameters(request)

        #import pdb; pdb.set_trace()

        fn = getattr(self, 'api_%s_%s' % (request.method.lower(), method), None)
        if fn is None:
            raise Http404

        response = fn(request)

        if isinstance(response, HttpResponse):
            return response
        return JSONResponse(response)

    ######################################################################
    # Model Registration
    ######################################################################

    #: A mapping between Django models and ``BackOfficeModel`` implementation
    #: instances.
    model_to_bo_model = None

    #: A mapping between the ``slug`` of a ``BackOfficeModel`` implementation
    #: and ``BackOfficeModel`` implementation instances.
    #: This is where slugs will be resolved to their actual ``BackOfficeModel``
    #: instance.
    slug_to_bo_model = None

    #: A mapping between Django models and lists of ``BackOfficeModel``
    #: instances that depend on the Django models for their ``search_index``.
    search_index_dependency_to_dependants = defaultdict(lambda: [])

    def _reindex_model_signal_handler(self, sender, **kwargs):
        """
        Signal handler for re-indexing models. If the sender is a dependency
        for another model, the other model will also be indexed.
        """
        bo_model = self.get_model(model=sender)
        instance = kwargs.get('instance')

        # Just do a simple reindex
        if bo_model:
            bo_model.reindex(instance, self.name)

        # Reindex search_index dependants if there are any.
        if sender in self.search_index_dependency_to_dependants:
            dependants = self.search_index_dependency_to_dependants[sender]
            for dependant in dependants:
                get_dependant_instance, expected_dependant_model = dependant.search_index_dependencies[sender]
                dependant_instance = get_dependant_instance(instance)
                if isinstance(dependant_instance, expected_dependant_model):
                    dependant.reindex(dependant_instance, self.name)

    def _delete_index_signal_handler(self, sender, **kwargs):
        """
        Signal handler for deleting search indexes for models that will
        be deleted..
        """
        bo_model = self.get_model(model=sender)
        instance = kwargs.get('instance')

        if bo_model:
            bo_model.delete_index(instance, self.name)

    def register_model(self, bo_model):
        """
        Register a ``BackOfficeModel`` implementation class with this
        backoffice.

        :param bo_model: a ``BackOfficeModel`` implementation class
        """
        if not self.model_to_bo_model:
            self.model_to_bo_model = {}
        if not self.slug_to_bo_model:
            self.slug_to_bo_model = {}

        if not bo_model.slug in self.slug_to_bo_model:
            bo_model_instance = bo_model()
            self.slug_to_bo_model[bo_model.slug] = bo_model_instance
            self.model_to_bo_model[bo_model.model] = bo_model_instance
            self.link_relationship(bo_model_instance)

            # Connect signals to listen for changes to this model and their
            # ``search_index_dependencies``.
            post_save.connect(self._reindex_model_signal_handler, sender=bo_model.model)
            pre_delete.connect(self._delete_index_signal_handler, sender=bo_model.model)
            for dependency in bo_model_instance.search_index_dependencies:
                self.search_index_dependency_to_dependants[dependency].append(bo_model_instance)
                post_save.connect(self._reindex_model_signal_handler, sender=dependency)
                post_delete.connect(self._reindex_model_signal_handler, sender=dependency)

    def get_model(self, slug=None, model=None):
        """
        Gets a registered ``BackOfficeModel`` implementation instance either
        by slug or Django model.
        """
        if slug:
            return self.slug_to_bo_model.get(slug, None)
        else:
            return self.model_to_bo_model.get(model, None)

    def serialize_model_instance(self, instance, include_children=False):
        """
        Serializes an Django model instance that is registered with this
        backoffice using their ``BackOfficeModel`` implementation.

        :param instance: a Django model instance
        :param include_children: whether to include children in the
        serialization
        :return: a simple Python object that is JSON serializable
        """
        bo_model = self.get_model(model=type(instance))
        if include_children:
            return bo_model.get_serialized(instance)
        else:
            return bo_model.get_serialized_with_children(instance)

    def serialize_model_instances(self, instances, include_children=False):
        """
        Serializes multiple Django model instances using
        ``serialize_model_instance``.

        :param instances: an iterable containing registered Django model
        instances registered with this backoffice.
        :param include_children: whether to include children in the
        serialization
        :return: a list of simple Python objects that are JSON serializable.
        """
        return [self.serialize_model_instance(i) for i in instances]

    def link_relationship(self, bo_model):
        """
        Links parent ``BackOfficeModel`` implementations with their parents
        and children. The parent will get a ``children`` attribute containing
        a mapping between the children slugs and child ``BackOfficeModel``
        implementations.

        :param bo_model: a child ``BackOfficeModel`` implementation instance
        that wants to link with its parent.
        """
        parent_fields = bo_model.parent_fields_list

        if parent_fields:
            for parent_field in parent_fields:
                parent_model_slug = bo_model.get_parent_model_slug_for_field(parent_field)
                if parent_model_slug:
                    parent_bo_model = self.get_model(slug=parent_model_slug)
                else:
                    parent_model = bo_model.model._meta.get_field(parent_field).rel.to
                    parent_bo_model = self.get_model(model=parent_model)
                if parent_bo_model:
                    if not bo_model.slug in parent_bo_model.children:
                        parent_bo_model.children[bo_model.slug] = bo_model
                        parent_bo_model.child_to_accessor[bo_model.slug] = bo_model.get_parent_accessor_to_myself(parent_field)
                    if not parent_bo_model.slug in bo_model.parents:
                        bo_model.parents[parent_bo_model.slug] = parent_bo_model
                        bo_model.parent_to_accessor[parent_bo_model.slug] = bo_model.get_parent_accessor_from_myself(parent_field)

    ######################################################################
    # View Registration
    ######################################################################
    slug_to_bo_view = None

    def register_view(self, bo_view):
        """
        Registers a ``BackOfficeView`` implementation class with this
        backoffice.

        :param bo_view: a ``BackOfficeView`` implementation class
        """
        if not self.slug_to_bo_view:
            self.slug_to_bo_view = {}

        if not bo_view.slug in self.slug_to_bo_view:
            bo_view_instance = bo_view()
            self.slug_to_bo_view[bo_view.slug] = bo_view_instance

    def get_view(self, slug):
        """
        Gets a registered ``BackOfficeView`` implementation instance by slug.
        """
        return self.slug_to_bo_view.get(slug, None)

    ######################################################################
    # Search
    ######################################################################
    def serialize_search_result(self, index):
        """
        Transforms a ``SearchIndex`` instance to a serialized ``BackOfficeModel``
        including metadata.
        """
        bo_model = self.get_model(slug=index.model_slug)
        if bo_model is None:
            return None
        try:
            instance = bo_model.model.objects.get(pk=index.model_id)
        except ObjectDoesNotExist:
            return None
        serialized = bo_model.get_serialized(instance)
        return serialized

    def count_by_model(self, indices):
        """
        Given an iterable of ``SearchIndex`` instances, return a report of
        counts by ``model_slug``, and their serialized ``BackOfficeModel``
        metadata.

        :param indices: an iterable of ``SearchIndex`` instances
        :returns: ``[{'meta': {'slug': 'user', ...}, 'count': 15}, ...]``
        """
        model_counts = defaultdict(lambda: 0)
        for index in indices:
            model_counts[index.model_slug] += 1
        model_counts = [[self.get_model(mc[0]), mc[1]] for mc in model_counts.items()]
        model_counts = [mc for mc in model_counts if mc[0] is not None]
        model_counts.sort(key=lambda x: x[0].priority)
        model_counts = [{'meta': mc[0].serialize_meta(),
                         'count': mc[1]
                        } for mc in model_counts]
        return model_counts

    def serialize_search_results(self, indices):
        """
        Transforms ``SearchIndex`` instances to a list of serialized
        ``BackOfficeModel`` including metadata.
        """
        return [self.serialize_search_result(i) for i in indices if i.model_slug in self.slug_to_bo_model]


    def search(self, query, filter_on_model_slug=None, page=1, page_size=20, include_counts=True):
        """
        Performs a search on Django models registered with this backoffice.

        :param query: The search query.
        :param filter_on_model_slug: (optional) a ``BackOfficeModel`` slug
        to filter on
        :param page: (optional) the page of the search results to show. By
        default 1.
        :param page_size: (optional) the page size. By default 20.
        :param include_counts: (optional) whether to include the counts.
        :return: ``{'results': [self.serialize_search_results()], 'model_counts': [self.count_by_model()]}``
        """
        if query == u'':
            return ()

        ts_query = convert_to_raw_tsquery(query)
        all_indices = SearchIndex.objects.search(ts_query, raw=True).filter(backoffice_instance=self.name)

        model_counts = self.count_by_model(all_indices) if include_counts else []

        if filter_on_model_slug:
            all_indices = all_indices.filter(model_slug=filter_on_model_slug)

        indices = all_indices[(page-1)*page_size:page*page_size]

        return {
            'results': self.serialize_search_results(indices),
            'model_counts': model_counts
        }

    def reindex_all_models(self):
        SearchIndex.objects.all().delete()
        for bo_model in self.slug_to_bo_model.values():
            for obj in bo_model.model.objects.all():
                bo_model.reindex(obj, self.name)

    ######################################################################
    # Internal JSON API
    ######################################################################
    def api_get_search(self, request):
        """
        API call implementation for ``self.search()``. It passes on ``q``,
        ``page`` and ``filter_model`` from the ``request.view_params``.

        :param request: a HttpRequest containing ``view_params``.
        :return: the results of ``self.search()``.
        """
        page = int(request.view_params.get('page', '1'))
        filter_model = request.view_params.get('filter_model')
        q = request.view_params.get('q')
        return self.search(q, page=page, filter_on_model_slug=filter_model)

    def api_get_search_preview(self, request):
        """
        API call to perform a search preview. It passes on ``q``, ``page``
        and ``filter_model``. It uses a ``page_size`` of 5.

        :param request: a HttpRequest containing ``view_params``.
        :return: the results of ``self.search(page_size=5)``.
        """
        filter_model = request.view_params.get('filter_model')
        q = request.view_params.get('q')
        return self.search(q, page_size=5, filter_on_model_slug=filter_model,
                           include_counts=False)

    def api_get_model(self, request):
        """
        API call to retrieve a serialized Django model instance using his
        ``BackOfficeModel`` implementation.

        :param request: ``request.view_params with 'model_slug' and 'pk'``
        :return: a serialized Django model instance using his
        ``BackOfficeModel`` implementation.
        """
        model_slug = request.view_params.get('model_slug')
        pk = request.view_params.get('pk')
        bo_model = self.get_model(slug=model_slug)
        obj = bo_model.model.objects.get(pk=pk)
        serialized = bo_model.get_serialized(obj, children=True, parents=True, siblings=True)
        return serialized

    def api_get_view(self, request):
        """
        Retrieves a ``BackOfficeView`` implementation based on the given slug
        and calls the ``get_serialized()`` method on it, whose contents are
        returned.

        :param request: ``request.view_params with 'view_slug'``
        :return: a serialized view content
        """
        bo_view = self.get_view(request.view_params.get('view_slug'))
        return bo_view.get_serialized(request)

    def api_post_view(self, request):
        """
        Retrieves a ``BackOfficeView`` implementation based on the given slug
        and calls the ``get_serialized_post()`` method on it, whose contents are
        returned.

        :param request: ``request.view_params with 'view_slug'``
        :return: a serialized view content
        """
        bo_view = self.get_view(request.view_params.get('view_slug'))
        return bo_view.get_serialized_post(request)

    def api_post_view_action(self, request):
        """
        Performs an action to a given view.

        :param request: ``request.view_params with 'method', 'params' and 'view_params'``
        :return: the results of the called view method.
        """
        method = request.view_params.get('method')
        action_params = request.view_params.get('params')
        view_params = request.view_params.get('view_params')

        # Attach the actual view_params and action_params to the request.
        request.action_params = action_params
        request.view_params = view_params

        bo_view = self.get_view(view_params.get('view_slug'))

        fn = getattr(bo_view, method, None)
        if not fn:
            raise Http404(u'Cannot find method %s on view %s' % (method, bo_view.slug))
        return fn(request)

    def api_get_view_view(self, request):
        """
        Calls a regular Django view on the given BackOffice view.

        :param request: ``request.view_params with 'method' and 'view_slug'``
        :return: the HttpResponse from the BackOffice method with the name inside 'method'
        """
        method = request.view_params.get('method')
        view_slug = request.view_params.get('view_slug')

        bo_view = self.get_view(view_slug)

        fn = getattr(bo_view, method, None)
        if not fn:
            raise Http404(u'Cannot find method %s on view %s' % (method, bo_view.slug))
        return fn(request)


class BackOfficeTab(object):
    """
    A tab that will be shown for a ``BackOfficeModel``. A ``BackOfficeModel`` can
    have some tabs associated with it. Each tab is represented by:

    *   ``slug``: The unique (inside a model) slug for a tab.
        Used for navigation in the URL.
    *   ``title``: A human title that will pe used as the caption for a tab.
    *   ``template``: The path to a template that must be rendered inside the tab.
        This template is given the ``instance`` context variable, which contains
        the current model instance.
    """

    slug = AutoSlug(remove_suffix='Tab')
    title = None
    template = None

    def __init__(self, slug, title, template, shadow=None):
        self.slug = slug
        self.title = title
        self.template = template
        self.shadow = shadow

    def get_serialized_meta(self):
        return {
            'slug': self.slug,
            'title': self.title,
            'shadow': self.shadow
        }

    def get_serialized(self, instance):
        return {
            'slug': self.slug,
            'title': self.title,
            'template': render_to_string(self.template, {'instance': instance}),
            'shadow': self.shadow
        }

    def __repr__(self):
        return 'BackOfficeTab(%r, %r, %r, shadow=%r)' % (self.slug, self.title, self.template, self.shadow)


class BackOfficeModel(object):
    """
    The base class for a ``BackOfficeModel`` implementation. Implement this
    class and register your own Django models to a backoffice.
    """

    #: A unique slug to identify a model ('user', 'sim', ...)
    slug = AutoSlug(remove_suffix='Model')

    #: The actual Django model that is being used
    model = None

    #: (optional) The name of a ``ForeignKey`` that points to a parent object.
    #: If this parent is registered with the same backoffice, they are shown as
    #: a parent/child relation.
    parent_field = None

    #: (optional) The plural version of parent_field.
    parent_fields = None

    #: Verbose name for displaying purposes. Should be lowercase. E.g. 'user'
    verbose_name = None

    #: Plural verbose name for displaying purposes. Should be lowercase. E.g. 'users'
    verbose_name_plural = None

    #: A mapping of slugs to ``BackOfficeModel`` implementation instances
    #: to represent kinds of children. This property will be automatically filled
    #: when you register your parent and child models with a BackOfficeBase
    #: implementation instance.
    children = None
    child_to_accessor = None

    #: A mapping of slugs to ``BackOfficeModel`` implementation instances
    #: to represent kinds of parents. This property will be automatically filled
    #: when you register your parent and child models with a BackOfficeBase
    #: implementation instance.
    parents = None
    parent_to_accessor = None

    #: Include siblings of specified parent slug in serialization.
    siblings = None

    #: Define a priority that will be used for displaying purposes.
    #: Can also be used as a way to sort models by kind, if used uniquely.
    priority = 999

    #: For displaying purposes. Will probably change, so leave alone.
    has_header = True

    #: For displaying purposes. Will probably change, so leave alone.
    collapsed = True

    #: Whether we want to appear as a menu of children in the parent view
    show_in_parent = False

    #: An optional template path to render a header for a model instance
    #: above the tabs.
    header_template = None

    #: A tuple of ``BackOfficeTab`` instances. These tabs can contain templates
    #: which in turn can display extra information about this model.
    tabs = ()

    #: When you have overridden ``search_index`` and included child objects
    #: in your search index (e.g. comments on a user) you can define these
    #: child models to trigger a reindex when a child changes.
    #: Example: ``{Comment: (lambda c: c.content_object, User)}``.
    #: In the value of this dictionary you define a tuple with a function
    #: which knows how to find the parent object and a model type to make
    #: sure we are getting the right argument to our ``search_index``
    #: implementation.
    search_index_dependencies = None

    def __init__(self):
        self.children = {}
        self.child_to_accessor = {}
        self.parents = {}
        self.parent_to_accessor = {}
        self.search_index_dependencies = {}

    def get_title(self, instance):
        """
        A textual representation of a model instance to be used as a title.
        """
        return unicode(instance)

    def serialize(self, instance):
        """
        Override this to add extra information to be exposed to the Angular
        side of your tab templates.
        """
        return {}

    def render_template(self, instance):
        if self.header_template:
            context = {
                'instance': instance
            }
            return render_to_string(self.header_template, context)
        return u''

    def get_parent_model_slug_for_field(self, parent_field):
        return None

    def get_parent_accessor_to_myself(self, parent_field):
        parent_django_field = self.model._meta.get_field(parent_field)
        return parent_django_field.rel.related_name \
            or '%s_set' % self.model.__name__.lower()

    def get_parent_accessor_from_myself(self, parent_field):
        return parent_field

    def get_serialized(self, instance, children=False, parents=False, siblings=False):
        serialized = {
            'id': instance.pk,
            'title': self.get_title(instance),
            'model': self.slug,
            'path': '/%s/%d/' % (self.slug, instance.pk),
            'header_template': self.render_template(instance),
            'tabs': dict((t.slug, t.get_serialized(instance)) for t in self.tabs),
            'is_object': True,
            'meta': self.serialize_meta()
        }

        if children:
            serialized['children'] = self.get_children(instance)
        if parents:
            serialized['parents'] = self.get_parents(instance)
        if self.siblings and siblings:
            parent_bo_model = self.parents[self.siblings]
            parent = self.get_parent_by_model(instance, parent_bo_model)
            serialized['siblings'] = parent_bo_model.get_serialized_children_by_model(parent, self, exclude_meta=True)

        serialized.update(self.serialize(instance))
        return serialized

    @property
    def parent_fields_list(self):
        return self.parent_fields or self.parent_field and [self.parent_field]

    def get_children_by_model(self, instance, bo_model):
        return getattr(instance, self.child_to_accessor[bo_model.slug]).all()

    def get_serialized_children_by_model(self, instance, bo_model, exclude_meta=False):
        children = self.get_children_by_model(instance, bo_model)
        serialized_children = [bo_model.get_serialized(c) for c in children]
        if bo_model.has_header and not exclude_meta:
            serialized = bo_model.serialize_meta()
            serialized['children'] = serialized_children
            return [serialized]
        else:
            return serialized_children

    def get_parent_by_model(self, instance, bo_model):
        parent = getattr(instance, self.parent_to_accessor[bo_model.slug])
        if parent is None:
            return None
        if not isinstance(parent, bo_model.model):
            return None
        return parent

    def get_serialized_parent_by_model(self, instance, bo_model):
        parent = self.get_parent_by_model(instance, bo_model)
        return bo_model.get_serialized(parent) if parent else None

    def serialize_meta(self):
        return {
            'slug': self.slug,
            'verbose_name': self.verbose_name,
            'verbose_name_plural': self.verbose_name_plural,
            'has_header': self.has_header,
            'collapsed': self.collapsed,
            'show_in_parent': self.show_in_parent,
            'tabs': [t.get_serialized_meta() for t in self.tabs],
            'is_meta': True
        }

    def get_children(self, instance):
        if not self.children:
            return ()
        child_models = sorted(self.children.values(), key=lambda m: m.priority)
        return sum((self.get_serialized_children_by_model(instance, m) for m in child_models), [])

    def get_parents(self, instance):
        if not self.parents:
            return ()
        parent_models = sorted(self.parents.values(), key=lambda m: m.priority)
        parents = (self.get_serialized_parent_by_model(instance, parent_model) for parent_model in parent_models)
        return [parent for parent in parents if parent]

    def reindex(self, instance, backoffice_instance):
        index_text = self.search_index(instance)
        index, created = SearchIndex.objects.get_or_create(backoffice_instance=backoffice_instance,
                                                           model_slug=self.slug,
                                                           model_id=instance.pk,
                                                           defaults={'to_index': index_text})
        if not created:
            index.to_index = index_text
            index.save()

    def delete_index(self, instance, backoffice_instance):
        try:
            index = SearchIndex.objects.get(backoffice_instance=backoffice_instance,
                                            model_slug=self.slug,
                                            model_id=instance.pk)
            index.delete()
        except ObjectDoesNotExist:
            pass

    def search_index(self, instance):
        return unicode(instance)


class BackOfficeView(object):
    slug = AutoSlug(remove_suffix='View')

    def serialize(self, content, extra_context=None):
        context = {
            'slug': self.slug,
            'content': content,
        }
        if extra_context:
            context.update(extra_context)
        return context

    def serialize_view_result(self, result):
        content, extra_context = result, {}
        if isinstance(result, tuple):
            content, extra_context = result
        if isinstance(content, HttpResponse):
            if hasattr(content, 'render'):
                content.render()
            content = content.content
        return self.serialize(content, extra_context)

    def get_serialized(self, request):
        return self.serialize_view_result(self.get(request))

    def get_serialized_post(self, request):
        return self.serialize_view_result(self.post(request))

    def get(self, request):
        raise NotImplementedError

    def post(self, request):
        raise NotImplementedError

    def FOO(self, request):
        raise NotImplementedError
