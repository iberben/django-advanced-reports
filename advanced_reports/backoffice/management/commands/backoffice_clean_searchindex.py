from django.core.management.base import BaseCommand
from django.utils import importlib
from advanced_reports.backoffice.models import SearchIndex


class Command(BaseCommand):
    help = 'Cleans the search index.'

    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        backoffice_path = args[0]
        module, obj = backoffice_path.rsplit('.', 1)
        backoffice_module = importlib.import_module(module)
        backoffice = getattr(backoffice_module, obj)

        count = 0
        models_not_found = {}

        for si in SearchIndex.objects.filter(backoffice_instance=backoffice.name):
            bo_model = backoffice.get_model(slug=si.model_slug)
            if not bo_model:
                models_not_found[si.model_slug] = True
            else:
                if not bo_model.model.objects.filter(pk=si.model_id).exists():
                    si.delete()
                    count += 1
        if models_not_found:
            self.stdout.write(u'Following models were not found: %s\n' % ', '.join(models_not_found))
        self.stdout.write(u'Done deleting %d unnecessary search indexes!\n' % count)
