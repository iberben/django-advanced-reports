from django.http.request import QueryDict
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from advanced_reports.backoffice.base import BackOfficeView
from advanced_reports import get_report_for_slug
from advanced_reports.views import api_list, api_action


class AdvancedReportView(BackOfficeView):
    """
    A BackOffice view that renders an Advanced Report.

    Usage:
    <div view="advanced_report" params="{slug: 'report_slug', updateLocation: true|false}"></div>

    ``slug`` is the slug of your registered Advanced Report

    ``updateLocation`` is a boolean. If true, the location bar will be updated with querystring parameters
    reflecting the current filters and ordering.
    """
    slug = 'advanced_report'
    template = 'advanced_reports/backoffice/contrib/advanced-reports/advanced-report.html'

    def get(self, request):
        report_slug = request.view_params.get('slug')
        advreport = get_report_for_slug(report_slug)
        context = {'advreport': advreport}
        return render_to_string(self.template, context, context_instance=RequestContext(request))

    def fetch(self, request):
        obj_id = request.view_params.get('id', None)
        ids = [obj_id] if obj_id else None
        return api_list(request, request.view_params.get('slug'), ids=ids)

    def action(self, request):
        method = request.action_params.get('method')
        pk = request.action_params.get('pk')
        slug = request.view_params.get('slug')
        data = request.action_params.get('data')
        if data:
            # We have to do str(data) because otherwise QueryDict is too lazy to decode...
            post = QueryDict(str(data), encoding='utf-8')
            request.POST = post
        return api_action(request, slug, method, int(pk))

    def action_view(self, request):
        report_slug = request.view_params.get('slug')
        method = request.view_params.get('report_method')
        pk = request.view_params.get('pk')

        advreport = get_report_for_slug(report_slug)
        item = advreport.get_item_for_id(pk)
        advreport.enrich_object(item, request=request)
        return getattr(advreport, method)(item)

    def auto_complete(self, request):
        partial = request.action_params.pop('partial')
        report_slug = request.view_params.get('slug')

        advreport = get_report_for_slug(report_slug)
        return advreport.auto_complete(request, partial, request.action_params)


class AdvancedReportActionView(BackOfficeView):
    slug = 'advanced_report_action'

    def get(self, request):
        report_slug = request.view_params.get('slug')
        method = request.view_params.get('method')
        pk = request.view_params.get('pk')

        advreport = get_report_for_slug(report_slug)
        item = advreport.get_item_for_id(pk)
        advreport.enrich_object(item, request=request)
        response = getattr(advreport, method)(item)
        return response.content
