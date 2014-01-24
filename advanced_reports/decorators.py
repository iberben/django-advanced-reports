from functools import wraps
from django_delegation.decorators import delegate
from django_delegation.utils import SimpleHTTPRequest

try:
    from django.utils.timezone import now
except:
    import datetime
    now = datetime.datetime.now


def csv_delegation(view_func):
    """
    Detect if we want a CSV report. If we do, handle it via Django Delegation
    """

    @wraps(view_func)
    def delegated_view(request, *args, **kwargs):
        if isinstance(request, SimpleHTTPRequest) or not 'csv' in request.GET:
            return view_func(request, *args, **kwargs)
        return delegate(view_func)(request, *args, **kwargs)
    return delegated_view
