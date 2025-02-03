from typing import TYPE_CHECKING, Optional

from django.http import HttpRequest
import copyreg
from authentik.events.context_processors.base import EventContextProcessor
from django.contrib.sessions.backends.cache import SessionStore

if TYPE_CHECKING:
    from authentik.api.v3.config import Capabilities
    from authentik.events.models import Event

def reduce_SessionStore(self) -> ():
    return (
        dict,
        (),
        None,
        None,
        self.items(),
    )

copyreg.pickle(SessionStore, reduce_SessionStore)

class DjangoSessionContextProcessor(EventContextProcessor):
    def __init__(self):
        pass

    def configured(self) -> bool:
        """Return true if this context processor is configured"""
        return True

    """Base event enricher"""

    def capability(self) -> Optional["Capabilities"]:
        """Return the capability this context processor provides"""
        return None

    def enrich_event(self, event: "Event"):
        """Modify event"""
        pass

    def enrich_context(self, request: HttpRequest) -> dict:
        return {
            "django_session": request.session,
        }

DJANGO_SESSION_CONTEXT_PROCESSOR = DjangoSessionContextProcessor()
