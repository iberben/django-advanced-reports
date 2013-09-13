from django.db import models

from djorm_pgfulltext.fields import VectorField
from djorm_pgfulltext.models import SearchManager

class SearchIndex(models.Model):
    backoffice_instance = models.CharField(max_length=32)
    model_slug = models.CharField(max_length=32)
    model_id = models.PositiveIntegerField()
    to_index = models.TextField(blank=True)

    search_index = VectorField()

    objects = SearchManager(fields=('to_index',),
                            search_field='search_index',
                            auto_update_search_field=True)

    def __unicode__(self):
        return u'%s/%s/%d' % (self.backoffice_instance, self.model_slug, self.model_id)


