from django import template
from django.utils.safestring import mark_safe

import re
import HTMLParser
import json as json_lib


register = template.Library()


@register.filter
def angularize_form(value, model_prefix=None):
    """
    Make a Django form ready for AngularJS

    :param value: a HTML form
    :param model_prefix: if specified, will be used as the container for the form data
    :return: a HTML form made ready for AngularJS
    """

    def replace_name_func(match):
        name = match.groups()[0]
        short_name = name.split(u'-', 1)[1] if u'-' in name else name
        model = short_name if model_prefix is None else u'%s.%s' % (model_prefix, short_name)
        return u' name="%(name)s" ng-model="%(model)s"' % locals()

    def replace_value_func(match):
        model, value = 1, 3
        groups = list(match.groups())
        parsed_value = HTMLParser.HTMLParser().unescape(groups[value])
        groups[model] = u'%s" ng-init="%s=\'%s\'' % (groups[model], groups[model], parsed_value.replace(u"'", u"\\'"))
        print repr(groups)
        return u''.join(groups)

    replaced_name = re.sub(r'\s+name="([^"]+)"', replace_name_func, value)
    replaced_value = re.sub(r'(<[^>]+\s+ng-model=")([^"]+)("[^>]+\s+value=")([^"]+)("[^>]*>)', replace_value_func, replaced_name)
    return mark_safe(replaced_value)

@register.filter
def json(value):
    """
    Convert a simple Python object to JSON

    :param value: a simple Python object
    :return: the JSON for the simple Python object
    """
    return json_lib.dumps(value)
