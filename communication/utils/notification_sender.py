from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from accounts.models import User

def notify_group_users(notification):
    channel_layer = get_channel_layer()

    if notification.group:
        users = User.objects.filter(role="студент", group=notification.group)
    else:
        users = User.objects.filter(role="студент")

    for user in users:
        async_to_sync(channel_layer.group_send)(
            f"user_notifications_{user.id}",
            {
                "type": "send_notification",
                "title": notification.title,
                "message": notification.message,
                "image": notification.image,
            }
        )
