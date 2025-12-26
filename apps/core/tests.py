from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import TimeStampedModel

User = get_user_model()


class CoreViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_index_anonymous_renders_index(self):
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')

    def test_index_authenticated_renders_dashboard(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/dashboard.html')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class TimeStampedModelTestCase(TestCase):
    def test_timestamppedmodel_is_abstract(self):
        self.assertTrue(TimeStampedModel._meta.abstract)