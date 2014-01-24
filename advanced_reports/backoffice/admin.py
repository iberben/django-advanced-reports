from django.contrib import admin
from advanced_reports.backoffice.models import SearchIndex

class SearchIndexAdmin(admin.ModelAdmin):
    list_display = ('backoffice_instance', 'model_slug', 'model_id', 'to_index')
    list_filter = ('backoffice_instance', 'model_slug')
    search_fields = ('model_id',)

admin.site.register(SearchIndex, SearchIndexAdmin)

