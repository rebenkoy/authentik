"""Telegram Source sync tests"""

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.sources.telegram.models import TelegramSource, TelegramSourcePropertyMapping
from authentik.sources.telegram.sync import TelegramSync
from authentik.sources.telegram.tasks import telegram_sync_all
from authentik.sources.telegram.tests.utils import TelegramTestCase


class TestTelegramSync(TelegramTestCase):
    """Telegram Sync tests"""

    @apply_blueprint("system/sources-telegram.yaml")
    def setUp(self):
        self.source: TelegramSource = TelegramSource.objects.create(
            name="telegram",
            slug="telegram",
            realm=self.realm.realm,
            sync_users=True,
            sync_users_password=True,
            sync_principal=self.realm.admin_princ,
            sync_password=self.realm.password("admin"),
        )
        self.source.user_property_mappings.set(
            TelegramSourcePropertyMapping.objects.filter(
                managed__startswith="goauthentik.io/sources/telegram/user/default/"
            )
        )

    def test_default_mappings(self):
        """Test default mappings"""
        TelegramSync(self.source).sync()

        self.assertTrue(
            User.objects.filter(username=self.realm.user_princ.rsplit("@", 1)[0]).exists()
        )
        self.assertFalse(
            User.objects.filter(username=self.realm.nfs_princ.rsplit("@", 1)[0]).exists()
        )

    def test_sync_mapping(self):
        """Test property mappings"""
        noop = TelegramSourcePropertyMapping.objects.create(
            name=generate_id(), expression="return {}"
        )
        email = TelegramSourcePropertyMapping.objects.create(
            name=generate_id(), expression='return {"email": principal.lower()}'
        )
        dont_sync_service = TelegramSourcePropertyMapping.objects.create(
            name=generate_id(),
            expression='if "/" in principal:\n    return {"username": None}\nreturn {}',
        )
        self.source.user_property_mappings.set([noop, email, dont_sync_service])

        TelegramSync(self.source).sync()

        self.assertTrue(
            User.objects.filter(username=self.realm.user_princ.rsplit("@", 1)[0]).exists()
        )
        self.assertEqual(
            User.objects.get(username=self.realm.user_princ.rsplit("@", 1)[0]).email,
            self.realm.user_princ.lower(),
        )
        self.assertFalse(
            User.objects.filter(username=self.realm.nfs_princ.rsplit("@", 1)[0]).exists()
        )

    def test_tasks(self):
        """Test Scheduled tasks"""
        telegram_sync_all.delay().get()
        self.assertTrue(
            User.objects.filter(username=self.realm.user_princ.rsplit("@", 1)[0]).exists()
        )
