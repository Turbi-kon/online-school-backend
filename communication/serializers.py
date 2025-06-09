from rest_framework import serializers
from .models import Channel, Notification, Message, UploadedFile, Stream
from accounts.models import User
from adminpanel.models import Group
from urllib.parse import quote
from .utils import minio_client
from datetime import timedelta
from urllib.parse import urlparse


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'username']

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']

class ChannelSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    groups_allowed = serializers.PrimaryKeyRelatedField(many=True, queryset=Group.objects.all(), required=False)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Channel
        fields = '__all__'

    def to_representation(self, instance):
        # Для вывода вернём подробные данные участников и групп
        rep = super().to_representation(instance)
        rep['participants'] = UserSerializer(instance.participants.all(), many=True).data
        rep['groups_allowed'] = GroupSerializer(instance.groups_allowed.all(), many=True).data
        rep['created_by'] = UserSerializer(instance.created_by).data if instance.created_by else None
        return rep



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"

    def validate_image(self, value):
        parsed = urlparse(value)
        if not parsed.netloc == "localhost:9000":
            raise serializers.ValidationError("Неверный хост изображения.")
        if not parsed.path.startswith("/online-school/system/icons/"):
            raise serializers.ValidationError("Изображение должно быть из MinIO бакета online-school/system/icons.")
        return value


class UploadedFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    is_image = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = ['id', 'file_name', 'path', 'file_type', 'uploaded_at', 'url', 'is_image']

    def get_url(self, obj):
        try:
            expires = timedelta(days=7)
            presigned_url = minio_client.client.presigned_get_object("online-school", obj.path, expires=expires)
            return presigned_url
        except Exception as e:
            return None

    def get_is_image(self, obj):
        return obj.file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    uploaded_file = UploadedFileSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['sender', 'content', 'timestamp', 'uploaded_file']



class StreamSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Stream
        fields = (
            'user',
            'is_audio_enabled',
            'is_video_enabled',
            'is_muted_by_admin',
            'is_speaking',
        )
