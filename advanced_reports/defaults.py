import datetime
import time

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.template.defaultfilters import capfirst
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _


class ActionType(object):
    LINKS = 'links'
    BUTTONS = 'buttons'


class action(object):
    attrs_dict = None

    method = None
    '''
    Required. This is a string with the method name of your AdvancedReport subclass.
    This method must accept an item instance. If you choose to use a form, it gets an item and a bound form.
    If something goes wrong in your action, please raise an ActionException with a message to display to the user.

    When your method name ends with _view, you can return a HttpResponse object. This is useful for redirecting
    the user to another page or for download links, etc...
    '''

    verbose_name = None
    '''
    Required. This is what the user will see. If your action is simple (as in, it has no form), this
    will be the name of the web link. If your action uses a form, this will be a title that will be placed before it.
    If you don't want to display that, just use u''.
    '''

    success = None
    '''
    Optional. When you assign a string to this property it will be used as the success message when your action went
    successfully.
    '''

    confirm = None
    '''
    Optional. When you assign a string to this property, a confirm dialog will be displayed with your string as a message.
    '''

    group = None
    '''
    Optional. Give this a string with a group name so you can check your group against the verify_action_group method.
    You have to implement the verify_action_group method and return True or False depending on the applicability of your
    action to the group. If your item makes use of the states app, just make use of the state groups, it's really easy.
    '''

    form = None
    '''
    Optional. Give this a form class and your action will be displayed as a form. If your form is a subclass of ModelForm,
    the instance is automatically filled in for you. This way, it's easy to make some data editable in your report.
    '''
    
    form_via_ajax = False
    '''
    Optional. If True, the form will be loaded via mbox.
    '''

    submit = u'Submit'
    '''
    Required when using form. This is the value of your submit button when using forms.
    '''

    collapse_form = False
    '''
    Optional. If True, the form gets an "inline" css class, useful when you have some forms that must be very compact.
    '''

    form_template = None
    '''
    Optional. Give this a template path to a template that gets the {{ form }} variable. This template will then be used
    to display your form.
    '''

    next_on_success = False
    '''
    Optional. If True, when an action was executed successfully, the current row will be collapsed and the next row will
    be expanded, and the first field of the first form gets the input focus. This way you can create a report that acts
    like the "Sims requested" page.
    '''

    hidden = False
    '''
    Optional. If True, your action will not be displayed on the report. Use this when you want to move your action link
    to another place. Use the css class "action-link" and do a {% url advanced_reports_action "my_slug" "my_action_method", "my item id" %}.
    Also use this when defining a view action for your lazy divs.
    '''

    css_class = None
    '''
    Optional. This is how you can give some actions a special color, for example red when it does something destructive.
    '''

    individual_display = True
    '''
    Show the action in the list of individual items. Only applicable to simple actions (without a form).
    '''

    multiple_display = True
    '''
    Show the action in the list of multiple items. Only applicable to simple actions (without a form).
    '''

    def __init__(self, **kwargs):
        '''
        Each kwarg maps to a property above. For documentation, refer to the individual property documentation strings.
        '''
        self.attrs_dict = {}
        for k in kwargs.keys():
            setattr(self, k, kwargs[k])
            self.attrs_dict[k] = kwargs[k]

    def copy_with_instanced_form(self, prefix, instance=None, data=None):
        new_action = action(**self.attrs_dict)
        if self.form is not None:
            if issubclass(self.form, forms.ModelForm):
                new_action.form = self.form(data=data, prefix=prefix, instance=instance)
            else:
                new_action.form = self.form(data=data, prefix=prefix)

            if self.form_template:
                new_action.form_template = mark_safe(render_to_string(self.form_template, {'form': new_action.form}))

        if instance:
            if new_action.confirm: new_action.confirm = new_action.confirm % Resolver({'item': instance})
            if new_action.success: new_action.success = new_action.success % Resolver({'item': instance})
            if new_action.verbose_name: new_action.verbose_name = new_action.verbose_name % Resolver({'item': instance})

        return new_action

    def get_success_message(self):
        return self.success or _(u'Successfully executed "%s"') % self.verbose_name

class ActionException:
    def __init__(self, msg=None, form=None):
        if form is not None:
            msg = u''
            for k in form.errors.keys():
                for e in form.errors[k]:
                    msg += u' ' + e
            self.msg = e
        else:
            self.msg = u'%s' % msg

class AdvancedReport(object):
    slug = None
    '''
    Required. A unique url-friendly name for your Advanced Report
    '''

    fields = None
    '''
    Required. The fields that are included in your Advanced Report as a tuple of strings.
    When "models" is specified, it takes some values like the verbose_name from your model.

    By default, a lookup will be performed on your items but you can implement the get_FOO_html
    methods to override the output.

    field__value__subvalue notation is also supported, but it is recommended to implement that
    in the get_FOO_html method.
    '''

    sortable_fields = ()
    '''
    Optional. A tuple of fields that are sortable. __ notation is supported and you can sort on
    multiple fields a the same time by using the comma (,) separator. Only model fields can be
    sorted. Make sure to add your model to the "models" property.
    '''

    search_fields = ()
    '''
    Optional. A tuple of fields that can be searched.
    '''

    item_actions = ()
    '''
    Optional. A tuple of available actions for your report.
    See the documentation for the action class above.
    '''

    verbose_name = None
    '''
    Required. A name for an individual item. For example _(u'user')
    '''

    verbose_name_plural = None
    '''
    Required. A plural name for some individual items. For example _(u'users')
    '''

    title = None
    '''
    Required. The title of your report. This will be displayed at the top of your report page.
    '''

    help_text = None
    '''
    Optional. Some text to explain the purpose of the report and some extra info.
    '''

    models = None
    '''
    Optional, but strongly advisable to use it. A tuple of model classes. This is merely for
    extra metadata and checking if some of your fields are real model fields.
    '''

    items_per_page = 20
    '''
    Optional. The maximum number of items shown on one page. When you have more than this number
    of items, your report will be paginated.
    '''

    links = ()
    '''
    Optional. A tuple of link tuples. You can define some top level links for your report.
    Example:
    links = (
        (u'Print this page', 'javascript:printPage();', u'Click here to print this page'),
        (u'Refresh', '.'),
    )

    As you can see, the third item of your link tuple is optional and can contain some help text.

    Advanced Reports has a nice little feature to let you export CSV files from your reports.
    Just add this link tuple:
    (u'Download CSV', '?csv')
    '''

    template = 'advanced_reports/default.html'
    '''
    Optional. Override this to use your own template for your report.
    '''

    item_template = 'advanced_reports/item_row.html'
    '''
    Optional. Override this to specify the item template. This is required when your normal template
    uses a custom view for items. Make sure to base it off the original and please keep the "action-row".
    '''

    decorate_views = False
    '''
    Required when using get_decorator. True indicates that Advanced Reports should use your implementation
    of the get_decorator method.
    This is needed because due to a special implementation from Jonathan Slenders we cannot try the get_decorator
    function before we really know if it is implemented.
    '''

    multiple_actions = False
    '''
    Optional. Puts checkboxes before each item and puts a combobox with group actions on your report.
    Only simple (as in, not using a form) actions can be performed on multiple items.

    You can implement your own special action method for multiple items. See the documenation for
    FOO_multiple below.
    '''

    urlname = None
    '''
    Optional. Use this if you have a custom urlname for your report. Advanced Reports then knows how to
    reach your report.
    '''

    date_range = None
    '''
    Optional. If a date field name is assigned to this, you can filter on date ranges. Made by Maarten, Thanks!
    '''

    animation = False
    '''
    Optional. True allows animation, but that does not work with table rows.
    '''

    empty_text = None
    '''
    Optional. The text displayed when no items are shown on your report. By default this is:
    There are no <your_verbose_name_plural> to display.
    '''

    header_visible = True
    '''
    Controls the visibility of the table header.
    '''
    
    show_actions_separator = True
    '''
    Shows the separator between actions.
    '''
    
    action_list_type = ActionType.LINKS
    '''
    Show the actions as LINKS or BUTTONS.
    '''
    
    show_actions_only_on_hover = True
    '''
    Show the actions of an item only when the user hovers over the item
    '''

    def queryset(self):
        '''
        You must implement this function as this is the primary source of the data you will
        want to manage.
        '''
        return None

    def get_FOO_verbose_name(self):
        '''
        Implement this function to specify the column header for the field FOO.
        '''
        return None

    def get_FOO_html(self):
        '''
        Implement this function to specify the HTML representation for the field FOO.
        '''
        return None

    def get_FOO_decorator(self):
        '''
        Implement this function to specify a decorator function for the field FOO.
        Return a function that accepts one parameter and returns the decorated html.
        '''
        return lambda s: s

    def verify_action_group(self, item, group):
        '''
        Implement this function to verify if the given group currently applies to the given item.

        For example, if the item is a paid purchase and the group is "paid", we must return True.
        To turn of filtering of actions by groups, just don't specify the group when creating an
        action and just leave this function alone.
        '''
        return True

    '''
    The following two functions work both in tandem for naming and finding items.
    It is recommended to override get_item_for_id as the default implementation may be a little
    bit inefficient.
    '''

    def get_item_id(self, item):
        '''
        Advanced Reports expects each item to have a unique ID. By default this is the primary key
        of a model instance, but this can be anything you want, as long it is a unicode string.
        '''
        return unicode(item.pk)

    def get_item_for_id(self, item_id):
        '''
        Advanced Reports also expects each item to be found by its unique ID. By default it does
        a lookup of the primary key of a model.
        '''
        try:
            return self.queryset().get(pk=item_id)
        except ObjectDoesNotExist, e:
            raise Http404(u'%s' % e)

    def get_decorator(self):
        '''
        To be used in tandem with decorate_views. Set it to True when you want to implement this function.
        Here you can return a decorator. That decorator will be used to decorate the Advanced Report views.
        This way you can easily add some permission restrictions to your reports.
        '''
        return None

    def FOO(self, item, form=None):
        '''
        The implementation of the FOO action method.
        '''

    def FOO_view(self, item):
        '''
        The implementation of the FOO action method that can return a HttpResponse
        '''

    def FOO_multiple(self, items):
        '''
        The implementation of the FOO action method with multiple items.
        This may return a HttpResponse object or just None.
        '''
        return None

    def get_item_class(self, item):
        '''
        Implement this to get some extra CSS classes for the item. Separate them with spaces.
        '''
        return u''

    def get_FOO_class(self, item):
        '''
        Implement this to get some extra CSS classes for the field FOO. Separate them with spaces.
        '''
        return u''

    def get_extra_information(self, item):
        '''
        Implement this to get some extra information about an item.
        This will be shown right below a data row and above the actions.

        = Ajax loading of information =

        You can specify some "lazy divs" that are only loaded when an action row expands.
        You must define a hidden item action with a method name that ends with '_view'.

        Example:

        def get_extra_information(self, item):
            return u'<div class="lazy" x:method="credit_view"></div>'

        item_actions = (
            action(method='credit_view', verbose_name=u'', group='mygroup', hidden=True),
        )

        def credit_view(self, item):
            balance = get_credit_balance(item)
            return render_to_response('credit_template.html', {'balance': balance})

        '''
        return u''

    def get_FOO_style(self):
        '''
        Implement this to apply some CSS to the FOO td table cell.
        For example, you can define a fixed width here.
        '''
        return u''

    def enrich_list(self, items):
        '''
        Implement this to attach some extra information to each item of the given items list.

        Use self.assign_attr(item, attr_name, value) to do that, it automatically detects dicts.

        Example usage: adding state information to each item to prevent multiple queries to the State model.
        '''
        pass

    def get_item_count(self):
        '''
        Implement this if you don't use Django model instances.
        Returns the number of items in the report.
        '''
        return self.queryset().count()
    
    def extra_context(self):
        '''
        Implement this to define some extra context for your template
        '''
        return {}
    
    def get_filtered_items(self, queryset, params):
        filter_query = None
        date_range_query = None
        fake_fields = []
        uses_model = None

        # Extract parameters
        q = params['q'].lower() if 'q' in params else None
        exact = 'exact' in params
        from_date = params.get('from', '')
        to_date = params.get('to', '')
        from_date_struct = time.strptime(params['from'], '%Y-%m-%d') if from_date else None
        to_date_struct = time.strptime(params['to'], '%Y-%m-%d') if to_date else None

        if from_date_struct and to_date_struct:
            date_range_query = Q()

            # Filtering on date range

            from_date = datetime.datetime(year=from_date_struct.tm_year,
                                          month=from_date_struct.tm_mon,
                                          day=from_date_struct.tm_mday)
            to_date = datetime.datetime(year=to_date_struct.tm_year,
                                        month=to_date_struct.tm_mon,
                                        day=to_date_struct.tm_mday)

            # Date range has no hour so we add 1 day to the to_date so that we get the results of that day aswell
            # eg: if we selected from: 2011-01-17 and to: 2011-01-18, then the actual date rangewill be:
            # between 2011-01-17 00:00 and 2011-01-19 00:00

            to_date += datetime.timedelta(days=1)
            uses_model = False

            field = self.get_model_field(self.date_range.split('__')[0])

            if field is None:
                fake_fields.append(self.date_range)
            else:
                uses_model = True
                date_range_query = Q(**{'%s__range' % self.date_range: (from_date, to_date)})

            queryset = queryset.filter(date_range_query)

        if q:
            if uses_model is None:
                uses_model = False

            parts = q.split()
            filter_query = Q()
            for part in parts:
                part_query = Q()
                for search_field in self.search_fields:
                    field = self.get_model_field(search_field.split('__')[0])
                    if field is None:
                        fake_fields.append(search_field)
                    else:
                        uses_model = True
                        if exact:
                            part_query = part_query | Q(**{'%s__iexact' % search_field: part})
                        else:
                            part_query = part_query | Q(**{'%s__icontains' % search_field: part})
                filter_query = filter_query & part_query


        fake_found = []
        if len(fake_fields) > 0:
            self.enrich_list(queryset)
            for fake_field in fake_fields:
                for o in queryset:
                    test_string = strip_tags(self.get_item_html(fake_field, o)).lower().replace(u'&nbsp;', u' ')
                    if q == test_string if exact else q in test_string:
                        fake_found.append(int(o.pk) if uses_model else o)

        if uses_model or uses_model is None:
            # uses_model is None when none of the search parameters were found
            if fake_found:
                if filter_query:
                    filter_query = filter_query | Q(pk__in=fake_found)
                else:
                    filter_query = Q(pk__in=fake_found)

            if filter_query:
                return EnrichedQueryset(queryset.filter(filter_query), self)
            else:
                # When no filter parameter is found then we don't apply the filter_query
                return EnrichedQueryset(queryset, self)
        else:
            return EnrichedQueryset(fake_found, self)

    def get_sorted_queryset(self, by_field):
        field_name = by_field.split('__')[0].split(',')[0]
        field_name = field_name[1:] if field_name[0] == '-' else field_name
        if self.get_model_field(field_name) is None:
            return self.queryset()
        return self.queryset().order_by(*by_field.split(','))

    def get_enriched_items(self, queryset):
        return EnrichedQueryset(queryset, self)

    def get_ordered_by(self, by_field):
        if by_field == '':
            return u''
        field_names = (part.strip('-') for part in by_field.split(','))
        verbose_names = (self.get_field_metadata(field_name)['verbose_name'] for field_name in field_names)
        return u', '.join(verbose_names)

    def get_action_callable(self, method):
#        if isinstance(method, basestring):
#            return getattr(self, method, lambda i, f=None: False)
#        else:
#            return method
        return getattr(self, method, lambda i, f=None: False)

    def handle_multiple_actions(self, method, selected_object_ids, request=None):
        action = self.find_action(method)
        objects = [self.get_item_for_id(item_id) for item_id in selected_object_ids]
        self.enrich_list(objects)
        for o in objects:
            self.enrich_object(o, list=False, request=request)
        objects = [object for object in objects if self.verify_action_group(object, action.group)]
        handler = getattr(self, '%s_multiple' % method, None)
        if handler:
            if len(objects) == 0:
                return None, 0
            return handler(objects), -1

        count = 0
        self.enrich_list(objects)
        for object in objects:
            self.enrich_object(object, list=False)
            if self.find_object_action(object, method) is not None:
                self.get_action_callable(method)(object)
                count += 1

        return None, count

    @property
    def column_headers(self):
        return [self.get_field_metadata(field_name) for field_name in self.fields]

    @property
    def searchable_columns(self):
        if not self.search_fields:
            return None
        field_names = (s.rsplit('__', 1)[-1] for s in self.search_fields)
        field_names = u', '.join(self.get_field_metadata(field_name)['verbose_name'] for field_name in field_names)
        return _(u'You can search by %(fields)s') % {'fields': field_names}

    def get_column_values(self, item):
        for field_name in self.fields:
            yield {'html': self.get_item_html(field_name, item),
                   'class': getattr(self, 'get_%s_class' % field_name, lambda i: u'')(item),
                   'style': getattr(self, 'get_%s_style' % field_name, lambda: None)()}

    def get_model_field(self, field_name):
        if self.models is None:
            return None

        for model in self.models:
            try:
                return model._meta.get_field_by_name(field_name)[0]
            except:
                pass
        return None

    def get_field_metadata(self, field_name):
        verbose_name = getattr(self, 'get_%s_verbose_name' % field_name, lambda: None)()
        if verbose_name is None:
            model_field = self.get_model_field(field_name)
            if model_field is not None:
                verbose_name = model_field.verbose_name

        if verbose_name is None:
            verbose_name = capfirst(field_name.replace(u'_', u' '))

        sortable = False
        order_by = ''
        for sf in self.sortable_fields:
            fn = sf.split('__')[0].split(',')[0].strip('-')
            if fn == field_name.split('__')[0]:
                sortable = True
                order_by = sf.strip('-')

        return {'name': field_name.split('__')[0],
                'verbose_name': capfirst(verbose_name),
                'sortable': sortable,
                'order_by': order_by,
                'style': getattr(self, 'get_%s_style' % field_name, lambda: None)()}

    def lookup_item_value(self, field_name, item):
        if '__' in field_name:
            field_name, remainder = field_name.split('__', 1)
            obj = getattr(item, field_name, None)
            return self.lookup_item_value(remainder, obj)
        else:
            html = getattr(item, 'get_%s_display' % field_name, lambda: None)()
            if html is None:
                html = getattr(item, field_name, None)
        return html

    def get_item_html(self, field_name, item):
        html = getattr(self, 'get_%s_html' % field_name, lambda i: None)(item)
        if html is None:
            html = self.lookup_item_value(field_name, item)

        decorator = getattr(self, 'get_%s_decorator' % field_name, lambda i: None)(item)
        if decorator is not None:
            html = decorator(html)

        return mark_safe(html)

    @property
    def objects(self):
        return EnrichedQueryset(self.queryset(), self)

    def enrich_object(self, o, list=True, request=None):
        '''
        This method adds extra metadata to an item.
        When the list argument is True, enrich_list will be called on the item.
        When calling this method multiple times, it is inefficient to call enrich_list,
        as it can be run once on the whole list, so in this case set list to False.
        If supplied, the request will be attached to the item so that you can use this
        in your actions.
        '''
        if list:
            self.enrich_list([o])

        self.assign_attr(o, 'advreport_column_values', [v for v in self.get_column_values(o)])
        self.assign_attr(o, 'advreport_actions', self.get_object_actions(o))
        self.assign_attr(o, 'advreport_object_id', self.get_item_id(o))
        self.assign_attr(o, 'advreport_class', self.get_item_class(o))
        self.assign_attr(o, 'advreport_extra_information', self.get_extra_information(o) % Resolver({'item': o}))
        self.assign_attr(o, 'advreport_request', request)

    def enrich_generic_relation(self, items, our_model, foreign_model, attr_name, fallback):
        '''
        This is a utility method that can be used to prefetch backwards generic foreign key relations.
        Use this if you have a lot of lookups of this kind when generating the report.

        Parameters:
        - items: a iterable of items where we want to attach the backwards relation object.
        - our_model: the type of items where the generic foreign key points to.
        - foreign_model: the type of items that have a generic foreign relation to our_model.
        - attr_name: specifies name of the attribute that will contain an instance of foreign_model.
        - fallback: a function that will be called when the backwards relation was not found.
          It must accept a our_model instance and must return a foreign_model instance.
        '''
        ct = ContentType.objects.get_for_model(our_model)
        pks = [item.pk for item in items]
        foreigns = foreign_model.objects.filter(content_type=ct, object_id__in=pks).select_related('content_type')
        foreign_mapping = {}
        for foreign in foreigns:
            foreign_mapping[int(foreign.object_id)] = foreign
        for item in items:
            setattr(item, attr_name, foreign_mapping.get(int(item.pk), None) or fallback(item))

    def enrich_backward_relation(self, items, foreign_model, field_name, related_name,
                                 our_index=None, our_foreign_index=None,
                                 select_related=None, many=True):
        '''
        This is a utility method that can be used to pretech backward relations.
        For instance, you can add subscription lists to each user using only one line of code.

        Parameters:
        - items: a iterable of items where we want to attach the backwards relation object.
        - foreign_model: the type of items that have a foreign relation to our_model.
        - field_name: the field name of foreign_model that points to our_model.
        - related_name: specifies name of the attribute that will contain (a list of)
          instances of foreign_model.
        - our_index: a callable that gets the id of an instance of our_model.
        - our_foreign_index: a callable that gets the id of our instance from foreign_model.
        - select_related: performs a select_related on the query on foreign_model.
        - many: if set to False, a single item will be assigned instead of a list. When
          the list is empty, None will be assigned.
        '''

        our_index = our_index or (lambda i: i.pk)
        oi = lambda i: int(our_index(i)) if our_index(i) is not None else None
        our_foreign_index = our_foreign_index or (lambda i: getattr(i, '%s_id' % field_name))
        ofi = lambda i: int(our_foreign_index(i)) if our_foreign_index(i) is not None else None

        pks = [oi(item) for item in items]
        foreigns = foreign_model.objects.filter(**{'%s__in' % field_name: pks})
        if select_related:
            foreigns = foreigns.select_related(*select_related)

        foreign_mapping = {}

        for foreign in foreigns:
            our_id = ofi(foreign)
            if our_id in foreign_mapping:
                foreign_mapping[our_id].append(foreign)
            else:
                foreign_mapping[our_id] = [foreign]

        if many:
            for item in items:
                setattr(item, related_name, foreign_mapping.get(oi(item), ()))
        else:
            for item in items:
                setattr(item, related_name, foreign_mapping.get(oi(item), (None,))[0])

    def get_object_actions(self, object):
        actions = []

        for a in self.item_actions:
            if self.verify_action_group(object, a.group):
                new_action = a.copy_with_instanced_form(prefix=self.get_item_id(object), instance=object)
                if not new_action.hidden and new_action.individual_display:
                    actions.append(new_action)

        return actions

    def find_object_action(self, object, method):
        for a in self.item_actions:
            if self.verify_action_group(object, a.group):
                if a.method == method:
                    return a
        return None

    def find_action(self, method):
        for a in self.item_actions:
            if a.method == method:
                return a
        return None

    @property
    def date_range_verbose_name(self):
        if not self.date_range:
            return u''
        return self.get_field_metadata(self.date_range)['verbose_name']

    def get_empty_text(self):
        if self.empty_text:
            return empty_text
        return _(u'There are no %(items)s to display.') % {'items': self.verbose_name_plural}

    def assign_attr(self, object, attr_name, value):
        '''
        Assigns a value to an attribute. When the given object is a dict, the value will be assigned
        as a key-value pair.
        '''
        if isinstance(object, dict):
            object[attr_name] = value
        else:
            setattr(object, attr_name, value)

    def urlize(self, urlname, kwargs):
        return lambda h: u'<a href="%(l)s">%(h)s</a>' % {'l': reverse(urlname, kwargs=kwargs), 'h': h}

class EnrichedQueryset(object):
    def __init__(self, queryset, advreport):
        self.queryset = queryset
        self.advreport = advreport

    def __getitem__(self, k):
        if isinstance(k, slice):
            return self._enrich_list(list(self.queryset[k.start:k.stop]))
        else:
            return self._enrich(self.queryset[k])

    def __iter__(self):
        return self.queryset.__iter__()

    def __len__(self):
        return len(self.queryset)

    def _enrich_list(self, l):
        # We run enrich_list on all items in one pass.
        self.advreport.enrich_list(l)

        for o in l:
            # We pass list=False to prevent running enrich_list from enrich_object.
            self.advreport.enrich_object(o, list=False)

        return l

    def _enrich(self, o):
        self.advreport.enrich_object(o)
        return o

class Resolver(object):
    def __init__(self, context):
        self.context = context

    def __getitem__(self, k):
        from django.template import Variable
        return Variable(k).resolve(self.context)

