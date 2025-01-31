"""authentik telegram source config"""

from authentik.blueprints.apps import ManagedAppConfig


class AuthentikSourceTelegramConfig(ManagedAppConfig):
    """Authentik source telegram app config"""

    name = "authentik.sources.telegram"
    label = "authentik_sources_telegram"
    verbose_name = "authentik Sources.Telegram"
    mountpoint = "source/telegram/"
    default = True
