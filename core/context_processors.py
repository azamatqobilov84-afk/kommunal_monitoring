"""
Shablonlar uchun umumiy context o'zgaruvchilari.
"""
from .models import Notification, Anomaly


def user_context(request):
    if not request.user.is_authenticated:
        return {}
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    open_anomalies = Anomaly.objects.filter(user=request.user, is_resolved=False).count()
    return {
        'unread_notifications_count': unread_count,
        'open_anomalies_count': open_anomalies,
    }
