import datetime
import os
import subprocess

def get_git_version():
    git_dir = os.path.abspath(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            '.git'
        )
    )
    try:
        # Python 2.7 has subprocess.check_output
        # 2.6 needs this longer version
        git_info = subprocess.Popen(['git', '--git-dir=%s' % git_dir, 'log', '--pretty=%ct %h', '-1'], stdout=subprocess.PIPE).communicate()[0].split()
        git_time = datetime.datetime.fromtimestamp(float(git_info[0]))
    except Exception:
        git_time = datetime.datetime.now()
        git_info = ('', '0000000')
    return git_time.strftime('%Y.%m.%d') + '.' + git_info[1]

__version__ = get_git_version()

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
    advreport.internal_mode = False
    advreport.report_header_visible = True
    return advreport
