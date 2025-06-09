from django.db import models
from accounts.models import User
from adminpanel.models import Group
import whisper

class Channel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    participants = models.ManyToManyField(User, related_name="channels", blank=True)
    max_participants = models.PositiveIntegerField(default=50)
    groups_allowed = models.ManyToManyField(Group, related_name="channels", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_channels")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def can_user_join(self, user):
        """
        Проверяет, может ли пользователь зайти в канал:
        - Если группы указаны: пользователь должен быть в одной из них
        - Если макс. участников достигнут: нельзя зайти
        """
        if self.groups_allowed.exists():
            if not user.group or user.group not in self.groups_allowed.all():
                return False

        if self.max_participants and self.participants.count() >= self.max_participants:
            return False

        return True



class UploadedFile(models.Model):
    FILE_CATEGORIES = [
        ('lecture', 'Lecture Document'),
        ('report', 'Activity Report'),
        ('user_upload', 'User Upload')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_CATEGORIES)
    path = models.CharField(max_length=512)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name


class Notification(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    image = models.URLField(max_length=2048)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')


    class Meta:
        ordering = ['timestamp']  # Сообщения по порядку

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.sender.username}: {self.content[:30]}"


class Stream(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='streams')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='streams')
    
    has_video = models.BooleanField(default=False)
    has_audio = models.BooleanField(default=False)
    has_webcam = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_muted_by_admin = models.BooleanField(default=False)
    is_speaking = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'channel')  # 1 стрим на пользователя в канале

    def __str__(self):
        return f"{self.user.username} in {self.channel.name} (video={self.has_video}, audio={self.has_audio}, webcam={self.has_webcam})"
    


class WhisperModel:
    def __init__(self):
        self.model = whisper.load_model("base")

    def transcribe(self, audio_path):
        try:
            result = self.model.transcribe(audio_path)
            return {"text": result.get("text", "").strip()}
        except Exception as e:
            print(f"[WhisperModel] Ошибка транскрипции: {e}")
            return {"text": ""}


    