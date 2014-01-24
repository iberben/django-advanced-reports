from django.contrib.auth.models import User
from django import forms

from advanced_reports.backoffice.shortcuts import action
from advanced_reports.defaults import AdvancedReport


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

class UserReport(AdvancedReport):
    slug = 'users'
    verbose_name = u'user'
    verbose_name_plural = u'users'
    models = (User,)

    fields = ('username', 'first_name', 'last_name', 'email')
    search_fields = fields
    sortable_fields = fields

    item_actions = (action(method='edit', verbose_name='Edit', form=UserForm, form_via_ajax=True),)
    multiple_actions = True

    def queryset_request(self, request):
        return User.objects.all()

    def edit(self, item, form):
        form.save()
