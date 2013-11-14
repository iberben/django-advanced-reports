from django.contrib import messages
from django.http.request import QueryDict
from django.http.response import HttpResponseBase
from django.shortcuts import redirect
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from advanced_reports.backoffice.base import BackOfficeView
from advanced_reports import get_report_for_slug
from advanced_reports.defaults import ActionException
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
        obj_id = request.view_params.get('pk', None)
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

    def multiple_action(self, request):
        report_slug = request.view_params.get('slug')
        method = request.action_params.get('report_method')
        items = request.action_params.get('items').split(',')
        global_select = request.action_params.get('global')
        advreport = get_report_for_slug(report_slug)

        if global_select:
            items, context = advreport.get_object_list(request)
        else:
            items = [advreport.get_item_for_id(pk) for pk in items]
        if hasattr(advreport, '%s_multiple' % method):
            return getattr(advreport, '%s_multiple' % method)(items)
        else:
            succeeded, failed = {}, {}
            for item in items:
                try:
                    action = advreport.find_object_action(item, method)
                    if action and action.is_allowed(request):
                        result = getattr(advreport, method)(item)
                        if isinstance(result, HttpResponseBase) and result.status_code == 200:
                            messages.warning(request, _(u'This action does not support batch operations.'))
                        else:
                            succeeded[advreport.get_item_id(item)] = action.get_success_message()
                    elif not action.is_allowed(request):
                        failed[advreport.get_item_id(item)] = _(u'You are not allowed to execute this action.')
                    else:
                        failed[advreport.get_item_id(item)] = _(u'This action is not applicable to this item.')
                except ActionException, e:
                    failed[advreport.get_item_id(item)] = e.msg
            if succeeded and not failed:
                messages.success(request, _(u'Successfully executed action on all selected items.'))
            elif succeeded and failed:
                messages.warning(request, _(u'Some actions were successful, but some were also failed.'))
            else:
                messages.error(request, _(u'No action on the selected items was successful.'))
            return {'succeeded': succeeded, 'failed': failed}

    def multiple_action_view(self, request):
        report_slug = request.view_params.get('slug')
        method = request.view_params.get('report_method')
        items = request.view_params.get('items').split(',')
        global_select = request.view_params.get('global')
        advreport = get_report_for_slug(report_slug)

        if global_select == 'true':
            items = advreport.get_object_list(request)
        else:
            items = [advreport.get_item_for_id(pk) for pk in items]

        items = [item for item in items if advreport.find_object_action(item, method)]
        if items:
            return getattr(advreport, '%s_multiple' % method)(items)
        messages.error(request, _(u'No items were applicable for this action.'))
        return redirect(request.META['HTTP_REFERER'])

    def auto_complete(self, request):
        partial = request.action_params.pop('partial')
        report_slug = request.view_params.get('slug')

        advreport = get_report_for_slug(report_slug)
        return advreport.auto_complete(request, partial, request.action_params)


class AdvancedReportActionView(BackOfficeView):
    slug = 'actionview'

    def get(self, request):
        report_slug = request.view_params.get('slug')
        method = request.view_params.get('method')
        pk = request.view_params.get('pk')

        advreport = get_report_for_slug(report_slug)
        item = advreport.get_item_for_id(pk)
        advreport.enrich_object(item, request=request)
        response = getattr(advreport, method)(item)
        return response.content
