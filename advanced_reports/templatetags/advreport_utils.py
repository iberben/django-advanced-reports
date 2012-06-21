from django import template
from django.template.context import RequestContext
from django.template.loader import render_to_string

from advanced_reports.views import list as advreport_list
from advanced_reports import get_report_or_404

register = template.Library()
             
@register.tag(name='advreport_detail')
def advreport_detail(parser, token):
    try:
        tag_name, advreport_slug, obj_list, internal_mode, report_header_visible = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires exactly 4 argument" % token.contents.split()[0]
    return AdvReportNode(advreport_slug, obj_list, internal_mode, report_header_visible)

class AdvReportNode(template.Node):
    def __init__(self, advreport_slug, obj_list, internal_mode, report_header_visible):
        if isinstance(advreport_slug, str):
            self.advreport_slug = advreport_slug
        else:
            self.advreport_slug = template.Variable(advreport_slug)
        self.obj_list = template.Variable(obj_list)
        self.internal_mode = internal_mode
        self.report_header_visible = report_header_visible
        self.request = template.Variable('request')
    
    def render(self, context):
        try:
            if isinstance(self.advreport_slug, str):
                slug = self.advreport_slug[1:-1]
            else:
                slug = self.advreport_slug.resolve(context)
            obj_list = self.obj_list.resolve(context)
            internal_mode = self.internal_mode.lower() == 'true'
            report_header_visible = self.report_header_visible.lower() == 'true'
            request = self.request.resolve(context)
            ids = []
            if isinstance(obj_list, list):
                ids = [o.pk for o in obj_list]
            else:
                ids = [obj_list.id,]
            return advreport_list(request, slug, ids, internal_mode, report_header_visible)
        except Exception, e:
             return e

@register.tag(name='advreport_js')
def advreport_js(parser, token):
    return AdvReportJSNode()

class AdvReportJSNode(template.Node):
    def __init__(self):
        self.request = template.Variable('request')

    def render(self, context):
        request = self.request.resolve(context)
        return render_to_string('advanced_reports/inc_js.html', {}, context_instance=RequestContext(request))

@register.tag(name='advreport_css')
def advreport_css(parser, token):
    return AdvReportCSSNode()

class AdvReportCSSNode(template.Node):
    def __init__(self):
        self.request = template.Variable('request')

    def render(self, context):
        request = self.request.resolve(context)
        return render_to_string('advanced_reports/inc_css.html', {}, context_instance=RequestContext(request))