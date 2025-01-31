"""Telegram Source Serializer"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import (
    GroupSourceConnectionSerializer,
    GroupSourceConnectionViewSet,
    UserSourceConnectionSerializer,
)
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.telegram.models import (
    GroupTelegramSourceConnection,
    UserTelegramSourceConnection,
)


class UserTelegramSourceConnectionSerializer(UserSourceConnectionSerializer):
    """Telegram Source Serializer"""

    class Meta:
        model = UserTelegramSourceConnection
        fields = UserSourceConnectionSerializer.Meta.fields + ["identifier"]


class UserTelegramSourceConnectionViewSet(UsedByMixin, ModelViewSet):
    """Source Viewset"""

    queryset = UserTelegramSourceConnection.objects.all()
    serializer_class = UserTelegramSourceConnectionSerializer
    filterset_fields = ["source__slug"]
    search_fields = ["source__slug"]
    ordering = ["source__slug"]
    owner_field = "user"


class GroupTelegramSourceConnectionSerializer(GroupSourceConnectionSerializer):
    """OAuth Group-Source connection Serializer"""

    class Meta(GroupSourceConnectionSerializer.Meta):
        model = GroupTelegramSourceConnection


class GroupTelegramSourceConnectionViewSet(GroupSourceConnectionViewSet):
    """Group-source connection Viewset"""

    queryset = GroupTelegramSourceConnection.objects.all()
    serializer_class = GroupTelegramSourceConnectionSerializer
