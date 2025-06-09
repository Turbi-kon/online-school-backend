from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import JsonResponse
from django.db import models
from .models import Channel, UploadedFile, Notification, Message, WhisperModel
from .serializers import ChannelSerializer, UserSerializer, NotificationSerializer, MessageSerializer
from accounts.models import User
from adminpanel.models import Group
from .utils.minio_client import save_file_to_minio, client, get_presigned_icon_url
from .utils.notification_sender import notify_group_users
import tempfile
import whisper
import uuid
import threading
import os
from io import BytesIO
import subprocess
from filelock import FileLock





SESS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESS_DIR, exist_ok=True)
locks = {}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_transcription_session(request):
    session_id = str(uuid.uuid4())
    print(f"🚀 Начата сессия: {session_id}")
    path_txt = os.path.join(SESS_DIR, f"{session_id}.txt")
    open(path_txt, "w", encoding="utf-8").close()
    locks[session_id] = threading.Lock()
    return Response({"session_id": session_id})


model = WhisperModel()



def convert_webm_to_wav(webm_path, wav_path):
    command = [
        "ffmpeg", "-y",
        "-i", webm_path,
        "-ar", "16000",
        "-ac", "1",
        wav_path,
        
    ]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    if proc.returncode != 0:
        print(f"FFmpeg error: {proc.stderr.decode('utf-8')}")
        raise Exception("FFmpeg conversion failed")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_transcription(request):
    session_id = request.data.get("session_id")
    audio_file = request.FILES.get("file")

    if not session_id or not audio_file:
        return Response({"error": "Missing session_id or file"}, status=400)

    tmp_webm = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    for part in audio_file.chunks():
        tmp_webm.write(part)
    tmp_webm.close()

    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_wav.close()

    try:
        # Конвертация
        convert_webm_to_wav(tmp_webm.name, tmp_wav.name)

        # Транскрипция всей записи
        result = model.transcribe(tmp_wav.name)
        text = result.get("text", "")
        print(f"📥 Получен файл для сессии {session_id}, транскрибированный текст: {text}")

        # Запись текста в файл
        path_txt = os.path.join(SESS_DIR, f"{session_id}.txt")
        lock_path = os.path.join(SESS_DIR, f"{session_id}.lock")

        if not os.path.exists(path_txt):
            return Response({"error": "Session file does not exist"}, status=404)

        with FileLock(lock_path, timeout=5):
            with open(path_txt, "w", encoding="utf-8") as f:
                f.write(text.strip() + "\n")

        return Response({"message": "File processed successfully"}, status=200)

    except Exception as e:
        return Response({"error": f"Processing failed: {str(e)}"}, status=500)

    finally:
        for f in (tmp_webm.name, tmp_wav.name):
            try:
                os.remove(f)
            except Exception as cleanup_error:
                print(f"⚠️ Ошибка при удалении {f}: {cleanup_error}")



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_transcription_session(request):
    session_id = request.data.get("session_id")
    if not session_id:
        return Response({"error": "Missing session_id"}, status=400)

    path_txt = os.path.join(SESS_DIR, f"{session_id}.txt")
    if not os.path.exists(path_txt):
        return Response({"error": "Session not found"}, status=404)

    # читаем текстовый файл и превращаем в файлоподобный объект
    with open(path_txt, "r", encoding="utf-8") as f:
        file_content = f.read()

    # создаём BytesIO-объект
    transcript_file = BytesIO(file_content.encode("utf-8"))
    transcript_file.name = f"transcript_{session_id}.txt"
    transcript_file.size = len(file_content)
    transcript_file.content_type = "text/plain"

    try:
        minio_result = save_file_to_minio(
            transcript_file,
            user=request.user,
            file_type='transcript'
        )
    except Exception as e:
        return Response({"error": f"MinIO upload failed: {str(e)}"}, status=500)

    # очищаем сессию
    os.remove(path_txt)
    locks.pop(session_id, None)

    return Response({"url": minio_result["url"]})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_channels(request):
    user = request.user
    if user.role in ['преподаватель', 'админ']:
        channels = Channel.objects.all()
    else:
        # Для студентов: фильтруем каналы по разрешённым группам
        channels = Channel.objects.filter(groups_allowed=user.group)
    serializer = ChannelSerializer(channels, many=True)
    return Response(serializer.data)


def get_channel_details(request, channel_id):
    try:
        channel = Channel.objects.get(id=channel_id)
        participants = channel.participants.all().values("username", "name")  # получаем участников канала
        messages = Message.objects.filter(channel=channel)
        message_serializer = MessageSerializer(messages, many=True)
        return JsonResponse({
            "id": channel.id,
            "name": channel.name,
            "participants": list(participants),
            "messages": message_serializer.data
        })
    except Channel.DoesNotExist:
        return JsonResponse({"error": "Канал не найден или не существует"}, status=404)    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_participants(request, channel_id):
    try:
        channel = Channel.objects.get(pk=channel_id)
        users = channel.participants.all()
        return Response(UserSerializer(users, many=True).data)
    except Channel.DoesNotExist:
        return Response({"error": "Channel not found"}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_channel(request, channel_id):
    try:
        channel = Channel.objects.get(pk=channel_id)
        if not channel.can_user_join(request.user):
            return Response({"error": "Access denied or room is full"}, status=status.HTTP_403_FORBIDDEN)

        channel.participants.add(request.user)
        return Response({"status": "joined"})
    except Channel.DoesNotExist:
        return Response({"error": "Channel not found"}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_channel(request, channel_id):
    try:
        channel = Channel.objects.get(pk=channel_id)
        channel.participants.remove(request.user)
        return Response({"status": "left"})
    except Channel.DoesNotExist:
        return Response({"error": "Channel not found"}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_channel(request):
    if request.user.role not in ['преподаватель', 'админ']:
        return Response({"error": "Only teachers and admins can create channels."}, status=403)

    data = request.data.copy()
    data['created_by'] = request.user.id  # Передадим создателя в сериализатор

    serializer = ChannelSerializer(data=data)
    if serializer.is_valid():
        channel = serializer.save()
        return Response(ChannelSerializer(channel).data, status=201)
    return Response(serializer.errors, status=400)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_file(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided'}, status=400)

    minio_result = save_file_to_minio(file, user=request.user)

    uploaded = UploadedFile.objects.create(
        user=request.user,
        file_name=file.name,
        file_type='user_upload',
        path=minio_result['path']
    )

    return Response({
        'status': 'uploaded',
        'file_name': file.name,
        'path': minio_result['path'],
        'url': minio_result['url'],  # временная ссылка (presigned)
        'is_image': file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    }, status=201)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_notification(request):
    user: User = request.user
    if user.role == 'студент':
        return Response({"detail": "Студенты не могут отправлять уведомления."}, status=status.HTTP_403_FORBIDDEN)

    serializer = NotificationSerializer(data=request.data)
    if serializer.is_valid():
        notification = serializer.save()
        notify_group_users(notification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == "студент":
            notifications = Notification.objects.filter(
                models.Q(group__isnull=True) | models.Q(group=user.group)
            ).order_by('-created_at')
        else:
            notifications = Notification.objects.all().order_by('-created_at')

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def channel_messages(request, channel_id):
    try:
        channel = Channel.objects.get(pk=channel_id)
    except Channel.DoesNotExist:
        return Response({"error": "Channel not found"}, status=404)

    messages = Message.objects.filter(channel=channel).order_by('timestamp')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


def list_minio_icons(request):
    prefix = "system/icons/"
    bucket_name = "online-school"
    objects = client.list_objects(bucket_name, prefix=prefix, recursive=True)

    icon_urls = []
    for obj in objects:
        url = get_presigned_icon_url(obj.object_name, expires_days=1)
        if url:
            icon_urls.append(url)

    return JsonResponse(icon_urls, safe=False)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def channel_detail(request, channel_id):
    try:
        channel = Channel.objects.get(id=channel_id)
    except Channel.DoesNotExist:
        return Response({"error": "Channel not found"}, status=404)

    if request.user.role not in ['преподаватель', 'админ']:
        return Response({"error": "Forbidden"}, status=403)

    data = request.data.copy()
    serializer = ChannelSerializer(channel, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_channel(request, channel_id):
    try:
        channel = Channel.objects.get(id=channel_id)
        channel.delete()
        return Response({"message": "Канал удалён"}, status=status.HTTP_204_NO_CONTENT)
    except Channel.DoesNotExist:
        return Response({"error": "Канал не найден"}, status=status.HTTP_404_NOT_FOUND)
    

