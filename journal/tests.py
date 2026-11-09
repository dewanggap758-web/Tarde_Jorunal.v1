from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import TradeLog


class HomePageTests(TestCase):
    def test_home_page_introduces_the_app_and_links_to_authentication(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kendalikan')
        self.assertContains(response, 'Dewangga Putra')
        self.assertContains(response, reverse('login'))
        self.assertContains(response, reverse('register'))

    def test_dashboard_stays_private_and_logout_returns_to_home(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(
            response,
            '{}?next={}'.format(reverse('login'), reverse('dashboard')),
        )

        user = User.objects.create_user(username='home-test', password='safe-test-password')
        self.client.force_login(user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('home'))


class RegistrationTests(TestCase):
    def test_registration_saves_a_hashed_password_and_logs_user_in(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new-trader',
                'email': 'trader@example.com',
                'password1': 'TradeJournal-Test-Password-934!',
                'password2': 'TradeJournal-Test-Password-934!',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        user = User.objects.get(username='new-trader')
        self.assertTrue(user.check_password('TradeJournal-Test-Password-934!'))
        self.assertNotEqual(user.password, 'TradeJournal-Test-Password-934!')


class TradeRecapTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='trader', password='safe-test-password')

    def test_dashboard_and_trade_page_use_distinct_buy_sell_colors(self):
        self.client.force_login(self.user)

        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard_response, 'class="buy-sell-buy"')
        self.assertContains(dashboard_response, 'class="mix-label-sell"')

        trade_response = self.client.get(reverse('add_trade'))
        self.assertContains(trade_response, 'class="trade-side-buy"')
        self.assertContains(trade_response, 'class="trade-side-sell"')

    def test_dashboard_offers_recap_pdf_download(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('download_trade_recap'))

    def test_recap_download_is_pdf_and_only_available_to_logged_in_users(self):
        TradeLog.objects.create(
            user=self.user,
            pair='EURUSD',
            order_type='BUY',
            lot_size='0.10',
            entry_price='1.08',
            exit_price='1.09',
            pnl='10.00',
            strategy='Breakout',
            emotion='Calm',
            notes='Test trade',
        )
        other_user = User.objects.create_user(
            username='another-trader',
            password='another-safe-password',
        )
        TradeLog.objects.create(
            user=other_user,
            pair='PRIVATEPAIR',
            order_type='SELL',
            lot_size='0.10',
            entry_price='1.08',
        )

        response = self.client.get(reverse('download_trade_recap'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

        self.client.force_login(self.user)
        response = self.client.get(reverse('download_trade_recap'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="trade-recap-', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-'))
        self.assertTrue(response.content.rstrip().endswith(b'%%EOF'))
        self.assertIn(b'EURUSD', response.content)
        self.assertIn(b'Test trade', response.content)
        self.assertNotIn(b'PRIVATEPAIR', response.content)

    def test_recap_download_returns_valid_pdf_when_user_has_no_trades(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('download_trade_recap'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF-'))
