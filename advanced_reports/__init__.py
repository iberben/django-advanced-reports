#: The version list
VERSION = (1, 3, 3)


def get_version():
    '''
    Converts the :attr:`VERSION` into a nice string
    '''
    if len(VERSION) > 3 and VERSION[3] != 'final' and VERSION[3] != '':
        return '%s.%s.%s %s' % (VERSION[0], VERSION[1], VERSION[2], VERSION[3])
    else:
        return '%s.%s.%s' % (VERSION[0], VERSION[1], VERSION[2])


#: The actual version number, used by python (and shown in sentry)
__version__ = get_version()

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
