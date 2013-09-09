from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as make_proxy

import json


_proxy_type = type(make_proxy('ignore this'))
def _json_object_encoder(obj):
    if isinstance(obj, _proxy_type):
        return u'%s' % obj
    else:
        return None


def to_json(obj):
    return json.dumps(obj, default=_json_object_encoder)


def JSONResponse(obj):
    return HttpResponse(to_json(obj))
