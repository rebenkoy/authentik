"""Telegram Source Auth tests"""

from django.contrib.auth.hashers import is_password_usable

from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.sources.telegram.auth import TelegramBackend
from authentik.sources.telegram.models import TelegramSource, UserTelegramSourceConnection
from authentik.sources.telegram.tests.utils import TelegramTestCase


class TestTelegramAuth(TelegramTestCase):
    """Telegram Auth tests"""

    def setUp(self):
        self.source = TelegramSource.objects.create(
            name="telegram",
            slug="telegram",
            realm=self.realm.realm,
            sync_users=False,
            sync_users_password=False,
            password_login_update_internal_password=True,
        )
        self.user = User.objects.create(username=generate_id())
        self.user.set_unusable_password()
        self.user.save()
        UserTelegramSourceConnection.objects.create(
            source=self.source, user=self.user, identifier=self.realm.user_princ
        )

    def test_auth_username(self):
        """Test auth username"""
        backend = TelegramBackend()
        self.assertEqual(
            backend.authenticate(
                None, username=self.user.username, password=self.realm.password("user")
            ),
            self.user,
        )

    def test_auth_principal(self):
        """Test auth principal"""
        backend = TelegramBackend()
        self.assertEqual(
            backend.authenticate(
                None, username=self.realm.user_princ, password=self.realm.password("user")
            ),
            self.user,
        )

    def test_internal_password_update(self):
        """Test internal password update"""
        backend = TelegramBackend()
        backend.authenticate(
            None, username=self.realm.user_princ, password=self.realm.password("user")
        )
        self.user.refresh_from_db()
        self.assertTrue(is_password_usable(self.user.password))
