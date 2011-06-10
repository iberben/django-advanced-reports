
REGISTRY = {}

def register(advreport):
    REGISTRY[advreport.slug] = advreport()

def get_report_for_slug(slug):
    return REGISTRY.get(slug, None)

def get_report_or_404(slug):
    advreport = get_report_for_slug(slug)
    if advreport is None:
        from django.http import Http404
        raise Http404('No AdvancedReport matches the given query.')
    return advreport
