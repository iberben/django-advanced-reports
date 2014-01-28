from functools import wraps
from django_delegation.decorators import delegate
from django_delegation.utils import SimpleHTTPRequest

try:
    from django.utils.timezone import now
except:
    import datetime
    now = datetime.datetime.now


def conditional_delegation(condition_func):
    """
    Delegate a view depending on a certain condition.
    """
    def decorator(view_func):
        @wraps(view_func)
        def delegated_view(request, *args, **kwargs):
            if not isinstance(request, SimpleHTTPRequest) and condition_func(request):
                return delegate(view_func)(request, *args, **kwargs)
            return view_func(request, *args, **kwargs)
        return delegated_view
    return decorator
