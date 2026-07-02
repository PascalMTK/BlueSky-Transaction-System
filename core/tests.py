from django.test import TestCase
from django.urls import reverse

from core.models import Country, User


class AdminAgentPermanentDeleteTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name='Test Country',
            code='TC',
            currency_code='USD',
            currency_name='US Dollar',
            flag_emoji='🇹🇨',
            phone_code='255',
            default_fee_percentage=3.00,
        )
        self.admin = User.objects.create(
            name='Admin User',
            email='admin@example.com',
            password='secret',
            role='admin',
            country=self.country,
            agent_code='ADM1',
            status='active',
        )
        self.agent = User.objects.create(
            name='Archived Agent',
            email='archived@example.com',
            password='secret',
            role='agent',
            country=self.country,
            agent_code='AGT1',
            status='deleted',
        )

    def test_archived_agent_can_be_permanently_deleted(self):
        self.client.session['user_id'] = self.admin.id
        self.client.session.save()

        response = self.client.post(
            reverse('admin_agent_permanent_delete', kwargs={'agent_id': self.agent.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.agent.id).exists())
