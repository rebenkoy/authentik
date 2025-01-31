"""Telegram Source urls"""

from django.urls import path

from authentik.sources.telegram.api.property_mappings import TelegramSourcePropertyMappingViewSet
from authentik.sources.telegram.api.source import TelegramSourceViewSet
from authentik.sources.telegram.api.source_connection import (
    GroupTelegramSourceConnectionViewSet,
    UserTelegramSourceConnectionViewSet,
)
from authentik.sources.telegram.views import DispatcherView, RequestKind

urlpatterns = [
    path(
        "login/<slug:source_slug>/",
        DispatcherView.as_view(kind=RequestKind.REDIRECT),
        name="telegram-login",
    ),
    path(
        "intermediate/<slug:source_slug>/",
        DispatcherView.as_view(kind=RequestKind.INTERMEDIATE),
        name="telegram-intermediate",
    ),
    path(
        "callback/<slug:source_slug>/",
        DispatcherView.as_view(kind=RequestKind.CALLBACK),
        name="telegram-callback",
    ),
]

api_urlpatterns = [
    ("propertymappings/source/telegram", TelegramSourcePropertyMappingViewSet),
    ("sources/user_connections/telegram", UserTelegramSourceConnectionViewSet),
    ("sources/group_connections/telegram", GroupTelegramSourceConnectionViewSet),
    ("sources/telegram", TelegramSourceViewSet),
]
