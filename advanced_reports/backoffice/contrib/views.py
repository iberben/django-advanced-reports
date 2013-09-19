from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from advanced_reports.backoffice.base import BackOfficeView
from advanced_reports import get_report_for_slug

class AdvancedReportView(BackOfficeView):
    slug = 'advanced_report'
    template = 'advanced_reports/backoffice/contrib/advanced-report.html'

    def get(self, request):
        report_slug = request.view_params.get('slug')
        advreport = get_report_for_slug(report_slug)
        context = {'advreport': advreport}
        return render_to_string(self.template, context, context_instance=RequestContext(request))


