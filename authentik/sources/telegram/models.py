"""authentik Telegram Source Models"""

import os
from pathlib import Path
from tempfile import gettempdir
from typing import Any

import gssapi
import pglock
from django.db import connection, models
from django.db.models.fields import b64decode
from django.http import HttpRequest
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from kadmin import KAdmin, KAdminApiVersion
from kadmin.exceptions import PyKAdminException
from rest_framework.serializers import Serializer
from structlog.stdlib import get_logger

from authentik.core.models import (
    GroupSourceConnection,
    PropertyMapping,
    Source,
    UserSourceConnection,
    UserTypes,
)
from authentik.core.types import UILoginButton, UserSettingSerializer
from authentik.flows.challenge import RedirectChallenge

LOGGER = get_logger()


class TelegramSource(Source):
    """Federate Telegram realm with authentik"""

    bot_id = models.TextField(
        blank=False,
        default=False,
        help_text=_("Telegram bot id can be obtained from telegram API"),
    )
    bot_token = models.TextField(
        blank=False,
        default=False,
        help_text=_("Telegram bot token can be obtained from BotFather"),
    )

    class Meta:
        verbose_name = _("Telegram Source")
        verbose_name_plural = _("Telegram Sources")

    def __str__(self):
        return f"Telegram Source {self.name}"


    @property
    def component(self) -> str:
        return "ak-source-telegram-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.telegram.api.source import TelegramSourceSerializer
        return TelegramSourceSerializer

    @property
    def property_mapping_type(self) -> type[PropertyMapping]:
        return TelegramSourcePropertyMapping

    @property
    def icon_url(self) -> str:
        icon = super().icon_url
        if not icon:
            return static("authentik/sources/telegram.png")
        return icon

    def ui_login_button(self, request: HttpRequest) -> UILoginButton:
        return UILoginButton(
            challenge=RedirectChallenge(
                data={
                    "to": reverse(
                        "authentik_sources_telegram:telegram-login",
                        kwargs={"source_slug": self.slug},
                    ),
                    "context": {"request": request.GET.dict()},
                },
            ),
            name=self.name,
            icon_url=self.icon_url,
        )

    def ui_user_settings(self) -> UserSettingSerializer | None:
        return UserSettingSerializer(
            data={
                "title": self.name,
                "component": "ak-user-settings-source-telegram",
                "configure_url": reverse(
                    "authentik_sources_telegram:telegram-login",
                    kwargs={"source_slug": self.slug},
                ),
                "icon_url": self.icon_url,
            }
        )

    def get_base_user_properties(self, info: dict[str, str|int], **kwargs):
        return {
            "username": info.get("username"),
            "name": info.get("first_name"),
        }

    def get_base_group_properties(self, group_id: str, **kwargs):
        return {
            "name": group_id,
        }


class TelegramSourcePropertyMapping(PropertyMapping):
    """Map Telegram Property to User object attribute"""

    @property
    def component(self) -> str:
        return "ak-property-mapping-source-telegram-form"

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.telegram.api.property_mappings import (
            TelegramSourcePropertyMappingSerializer,
        )

        return TelegramSourcePropertyMappingSerializer

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name = _("Telegram Source Property Mapping")
        verbose_name_plural = _("Telegram Source Property Mappings")


class UserTelegramSourceConnection(UserSourceConnection):
    """Connection to configured Telegram Sources."""

    identifier = models.TextField()

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.telegram.api.source_connection import (
            UserTelegramSourceConnectionSerializer,
        )

        return UserTelegramSourceConnectionSerializer

    class Meta:
        verbose_name = _("User Telegram Source Connection")
        verbose_name_plural = _("User Telegram Source Connections")


class GroupTelegramSourceConnection(GroupSourceConnection):
    """Connection to configured Telegram Sources."""

    @property
    def serializer(self) -> type[Serializer]:
        from authentik.sources.telegram.api.source_connection import (
            GroupTelegramSourceConnectionSerializer,
        )

        return GroupTelegramSourceConnectionSerializer

    class Meta:
        verbose_name = _("Group Telegram Source Connection")
        verbose_name_plural = _("Group Telegram Source Connections")
