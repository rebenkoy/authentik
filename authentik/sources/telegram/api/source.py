"""Source API Views"""
from django.urls import reverse_lazy
from rest_framework.viewsets import ModelViewSet
from rest_framework.fields import BooleanField, SerializerMethodField

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.events.api.tasks import SystemTaskSerializer
from authentik.sources.telegram.models import TelegramSource


class TelegramSourceSerializer(SourceSerializer):
    """Telegram Source Serializer"""
    callback_url = SerializerMethodField()
    authorization_url = SerializerMethodField()

    def get_callback_url(self, instance: TelegramSource) -> str:
        """Get OAuth Callback URL"""
        relative_url = reverse_lazy(
            "authentik_sources_telegram:telegram-intermediate",
            kwargs={"source_slug": instance.slug},
        )
        if "request" not in self.context:
            return relative_url
        return self.context["request"].build_absolute_uri(relative_url)

    def get_authorization_url(self, instance: TelegramSource) -> str:
        """Get OAuth Authorization URL"""
        return f"https://oauth.telegram.org/auth?bot_id={instance.bot_id}&origin={self.get_callback_url(instance)}"

    class Meta:
        model = TelegramSource
        fields = SourceSerializer.Meta.fields + [
            "callback_url",
            "authorization_url",
            "group_matching_mode",
            "bot_id",
            "bot_token",
        ]


class TelegramSyncStatusSerializer(PassiveSerializer):
    """Telegram Source sync status"""

    is_running = BooleanField(read_only=True)
    tasks = SystemTaskSerializer(many=True, read_only=True)


class TelegramSourceViewSet(UsedByMixin, ModelViewSet):
    """Telegram Source Viewset"""

    queryset = TelegramSource.objects.all()
    serializer_class = TelegramSourceSerializer
    lookup_field = "slug"
    search_fields = [
        "name",
        "slug",
        "bot_id",
    ]
    ordering = ["name"]
