from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as make_proxy
from django.conf import settings

import json


_proxy_type = type(make_proxy('ignore this'))
def _json_object_encoder(obj):
    if isinstance(obj, _proxy_type):
        return u'%s' % obj
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return None


def to_json(obj):
    if settings.DEBUG:
        return json.dumps(obj, default=_json_object_encoder, indent=2)
    return json.dumps(obj, default=_json_object_encoder)


def JSONResponse(obj):
    return HttpResponse(to_json(obj), content_type='application/json;charset=UTF-8')


class ViewRequestParameters(object):
    def __init__(self, request):
        self.GET = request.GET
        self.POST = request.POST
        try:
            self.body = request.body
            self.json_dict = json.loads(self.body) if 'application/json' in request.META['CONTENT_TYPE'] else {}
        except:
            self.json_dict = {}

        self.fallbacks = (self.GET, self.POST, self.json_dict)
        self.list_fallbacks = (self.GET, self.POST)

    def get(self, item, default=None):
        for fallback in self.fallbacks:
            obj = fallback.get(item, None)
            if obj is not None:
                return obj
        return default

    def getlist(self, item, default=None):
        for fallback in self.list_fallbacks:
            l = fallback.getlist(item)
            if l != []:
                return l
        if default is None:
            return []
        return default

    def __repr__(self):
        return 'ViewRequestParameters(%r, %r, %r)' % (self.GET, self.POST, self.json_dict)
