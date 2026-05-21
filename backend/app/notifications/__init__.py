"""Notification provider factory. Expo Push is the default transport."""

from functools import lru_cache

from app.services.notifications import NotificationProvider


@lru_cache
def get_notifier() -> NotificationProvider:
    from app.notifications.expo_push import ExpoPushProvider

    return ExpoPushProvider()
