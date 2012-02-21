from django import template
from advanced_reports.views import detail

register = template.Library()

@register.tag(name='advreport_detail')
def advreport_detail(parser, token):
    try:
        tag_name, advreport_slug, id = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires exactly 2 arguments" % token.contents.split()[0]
    return AdvReportNode(advreport_slug, id)

class AdvReportNode(template.Node):
    def __init__(self, advreport_slug, id):
        if isinstance(advreport_slug, str):
            self.advreport_slug = advreport_slug
        else:
            self.advreport_slug = template.Variable(advreport_slug)
        self.id = template.Variable(id)
        self.request = template.Variable('request')
    
    def render(self, context):
        try:
            if isinstance(self.advreport_slug, str):
                slug = self.advreport_slug[1:-1]
            else:
                slug = self.advreport_slug.resolve(context)
            id = self.id.resolve(context)
            request = self.request.resolve(context)
            return detail(request, slug, id, False)
        except Exception, e:
             return e