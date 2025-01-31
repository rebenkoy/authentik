"""Telegram source SPNEGO views"""
from typing import Any

import base64
import hmac
import json
from enum import Enum
from hashlib import sha256

from azure.core.pipeline.transport import HttpRequest
from django.core.handlers.asgi import ASGIRequest
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from msgraph.generated.models.event_type import EventType
from rest_framework.status import HTTP_403_FORBIDDEN
from structlog.stdlib import get_logger
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings

from authentik.core.sources.flow_manager import SourceFlowManager
from authentik.events.models import Event
from authentik.sources.telegram.models import (
    GroupTelegramSourceConnection,
    TelegramSource,
    UserTelegramSourceConnection,
)

LOGGER = get_logger()


class TelegramLoginView(RedirectView):

    def get_redirect_url(self, **kwargs) -> str:
        """Build redirect url for a given source."""
        Event.new("TelegramLoginView").from_http(self.request)
        slug = kwargs.get("source_slug", "")
        try:
            source: TelegramSource = TelegramSource.objects.get(slug=slug)
        except TelegramSource.DoesNotExist:
            raise Http404(f"Unknown OAuth source '{slug}'.") from None
        if not source.enabled:
            raise Http404(f"source {slug} is not enabled.")

        return (source.serializer)(context=dict(request=self.request)).get_authorization_url(source)

class TelegramIntermediateView(View):
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        Event.new("TelegramIntermediateView").from_http(self.request)
        return HttpResponse(
            """
            <html>
                <body>
                    <script>
                        window.location = window.location.toString().replace("#", "?").replace("intermediate", "callback");
                    </script>
                </body>
            </html>
            """.replace(" ", ""),
            status=200
        )



class TelegramCallbackView(View):
    source: TelegramSource

    def dispatch(self, request: ASGIRequest, *_, **kwargs) -> HttpResponse:
        """View Get handler"""
        Event.new("TelegramCallbackView").from_http(self.request)

        slug = kwargs.get("source_slug", "")
        try:
            self.source = TelegramSource.objects.get(slug=slug)
        except TelegramSource.DoesNotExist:
            raise Http404(f"Unknown Telegram source '{slug}'.") from None

        if not self.source.enabled:
            raise Http404(f"Source {slug} is not enabled.")

        tg_auth_result = request.GET.get("tgAuthResult")
        if not tg_auth_result:
            return HttpResponseForbidden()

        pad = "=" * ((4 - len(tg_auth_result) % 4) % 4)
        auth_result: dict[str, int|str] = json.loads(base64.b64decode(tg_auth_result + pad))

        response_hash = auth_result.pop("hash")
        data_check_string = "\n".join((f"{key}={value}" for key, value in sorted(auth_result.items())))
        secret_key = sha256(self.source.bot_token.encode()).digest()
        computed_hash = hmac.new(secret_key, msg=data_check_string.encode(), digestmod=sha256).hexdigest()

        if computed_hash != response_hash:
            return HttpResponseForbidden()

        identifier = self.get_user_id(info=auth_result)
        if identifier is None:
            return self.handle_login_failure("Could not determine id.")

        sfm = TelegramSourceFlowManager(
            source=self.source,
            request=self.request,
            identifier=identifier,
            user_info={
                "info": auth_result,
            },
            policy_context={
                "telegram_userinfo": auth_result,
            },
        )

        return sfm.get_flow(
            raw_info=auth_result,
        )

    def get_error_redirect(self, source: TelegramSource, reason: str) -> str:
        """Return url to redirect on login failure."""
        return settings.LOGIN_URL

    def get_user_id(self, info: dict[str, Any]) -> str | None:
        """Return unique identifier from the profile info."""
        if "id" in info:
            return info["id"]
        return None

    def handle_login_failure(self, reason: str) -> HttpResponse:
        """Message user and redirect on error."""
        LOGGER.warning("Authentication Failure", reason=reason)
        messages.error(
            self.request,
            _(
                "Authentication failed: {reason}".format_map(
                    {
                        "reason": reason,
                    }
                )
            ),
        )
        return redirect(self.get_error_redirect(self.source, reason))


class TelegramSourceFlowManager(SourceFlowManager):
    """Flow manager for oauth sources"""

    user_connection_type = UserTelegramSourceConnection
    group_connection_type = GroupTelegramSourceConnection


class RequestKind(Enum):
    """Enum of OAuth Request types"""

    CALLBACK = "callback"
    INTERMEDIATE = "intermediate"
    REDIRECT = "redirect"


@method_decorator(csrf_exempt, name="dispatch")
class DispatcherView(View):
    """Dispatch OAuth Redirect/Callback views to their proper class based on URL parameters"""

    kind = ""

    def dispatch(self, *args, source_slug: str, **kwargs):
        """Find Source by slug and forward request"""
        match self.kind:
            case RequestKind.REDIRECT:
                view = TelegramLoginView
            case RequestKind.INTERMEDIATE:
                view = TelegramIntermediateView
            case RequestKind.CALLBACK:
                view = TelegramCallbackView
            case _:
                raise Exception(f"Unknown request kind: {self.kind}")

        LOGGER.debug("dispatching Telegram request to", view=view, kind=self.kind)
        return view.as_view()(*args, source_slug=source_slug, **kwargs)
