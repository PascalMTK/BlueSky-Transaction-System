from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from core.models import Country, Transaction, User


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
        session = self.client.session
        session['user_id'] = self.admin.id
        session.save()

        response = self.client.post(
            reverse('admin_agent_permanent_delete', kwargs={'agent_id': self.agent.id})
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.agent.id).exists())


class TransactionEditTests(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name='Test Country',
            code='TZ',
            currency_code='TZS',
            currency_name='Tanzanian Shilling',
            flag_emoji='🇹🇿',
            phone_code='255',
            default_fee_percentage=3.00,
        )
        self.agent = User.objects.create(
            name='Agent User',
            email='agent2@example.com',
            password='secret',
            role='agent',
            country=self.country,
            agent_code='AGT2',
            status='active',
        )
        self.transaction = Transaction.objects.create(
            transaction_number='BSK-TEST-2',
            sender_name='Alice',
            sender_phone='123',
            receiver_name='Bob',
            amount=Decimal('100.00'),
            fee_percentage=Decimal('3.00'),
            fee_amount=Decimal('3.00'),
            total_amount=Decimal('97.00'),
            currency='TZS',
            origin_country=self.country,
            destination_country=self.country,
            agent=self.agent,
            status='completed',
            payment_method='cash',
            transaction_type='send',
        )

    def test_edit_transaction_with_blank_fee_falls_back_to_existing_values(self):
        # Amount unchanged, fee/total left blank — should fall back to the
        # transaction's existing fee_amount/total_amount (still consistent: 3 + 97 = 100).
        session = self.client.session
        session['user_id'] = self.agent.id
        session.save()

        response = self.client.post(
            reverse('tx_edit', kwargs={'tx_id': self.transaction.id}),
            {
                'sender_name': 'Alice Updated',
                'sender_phone': '1234',
                'receiver_name': 'Bob Updated',
                'receiver_phone': '5678',
                'amount': '100',
                'fee_amount': '',
                'total_amount': '',
                'currency': 'TZS',
                'payment_method': 'cash',
                'status': 'completed',
                'notes': 'updated',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.sender_name, 'Alice Updated')
        self.assertEqual(self.transaction.fee_amount, Decimal('3.00'))
        self.assertEqual(self.transaction.total_amount, Decimal('97.00'))

    def test_edit_transaction_rejects_fee_exceeding_amount(self):
        # The fee can never exceed what the client handed over — the edit
        # must be rejected, not silently clamped.
        session = self.client.session
        session['user_id'] = self.agent.id
        session.save()

        response = self.client.post(
            reverse('tx_edit', kwargs={'tx_id': self.transaction.id}),
            {
                'sender_name': 'Alice Updated',
                'amount': '120',
                'fee_amount': '150',
                'currency': 'TZS',
                'payment_method': 'cash',
                'status': 'completed',
                'notes': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.sender_name, 'Alice')
        self.assertEqual(self.transaction.amount, Decimal('100.00'))

    def test_edit_transaction_recomputes_total_from_amount_and_fee(self):
        # Montant remis au client is derived, never submitted directly.
        session = self.client.session
        session['user_id'] = self.agent.id
        session.save()

        response = self.client.post(
            reverse('tx_edit', kwargs={'tx_id': self.transaction.id}),
            {
                'sender_name': 'Alice Updated',
                'amount': '120',
                'fee_amount': '10',
                'currency': 'TZS',
                'payment_method': 'cash',
                'status': 'completed',
                'notes': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.sender_name, 'Alice Updated')
        self.assertEqual(self.transaction.fee_amount, Decimal('10.00'))
        self.assertEqual(self.transaction.total_amount, Decimal('110.00'))
