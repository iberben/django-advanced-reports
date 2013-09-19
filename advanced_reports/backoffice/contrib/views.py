from django.http.request import QueryDict
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from advanced_reports.backoffice.base import BackOfficeView
from advanced_reports import get_report_for_slug
from advanced_reports.views import api_list, api_action


class AdvancedReportView(BackOfficeView):
    slug = 'advanced_report'
    template = 'advanced_reports/backoffice/contrib/advanced-report.html'

    def get(self, request):
        report_slug = request.view_params.get('slug')
        advreport = get_report_for_slug(report_slug)
        context = {'advreport': advreport}
        return render_to_string(self.template, context, context_instance=RequestContext(request))

    def fetch(self, request):
        return api_list(request, request.view_params.get('slug'))

    def action(self, request):
        method = request.action_params.get('method')
        pk = request.action_params.get('pk')
        slug = request.view_params.get('slug')
        data = request.action_params.get('data')
        if data:
            post = QueryDict(data)
            request.POST = post
            print repr(request.POST)
        return api_action(request, slug, method, int(pk))
