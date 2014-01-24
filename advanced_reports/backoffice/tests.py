from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from advanced_reports.backoffice.examples.backoffice import test_backoffice

class BackOfficeBackend(TestCase):
    def setUp(self):
        User.objects.create(username='admin',
                            password='admin',
                            first_name='Admin',
                            last_name='User',
                            email='admin@example.com',
                            is_active=True,
                            is_staff=True,
                            is_superuser=True)

        self.client.login(username='admin', password='admin')
        self.home_url = reverse(test_backoffice.name + ':home', current_app=test_backoffice.app_name)

    def _reverse(self, name, args=None, kwargs=None):
        pass

    def test_default_context(self):
        """The default context contains usable values"""
        context = test_backoffice.default_context()
        self.assertEqual(context['backoffice'], test_backoffice)
        self.assertTrue('api_url' in context)
        self.assertTrue('root_url' in context)

    def test_home_view(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

