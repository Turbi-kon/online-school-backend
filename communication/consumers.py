import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Channel, Message, UploadedFile, Stream
from .serializers import MessageSerializer, StreamSerializer
from django.contrib.auth import get_user_model
from .utils.minio_client import save_file_to_minio

User = get_user_model()

class ChannelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.group_name = f"channel_{self.channel_id}"
        

        # Добавляем этот сокет в группу канала
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        

        user = self.scope.get('user')
        if user and user.is_authenticated:
            await self._db_add_participant(user)
            await self._broadcast_participants()

        streams = await self._get_all_streams()
        await self.send(text_data=json.dumps({
            "type": "streams_update",
            "streams": streams
        }))

        await self.channel_layer.group_send(
        self.group_name,
        {
            "type": "new_participant",
            "new_user": user.name,
        }
        )



            
        

    async def disconnect(self, close_code):
        user = self.scope.get('user')
        if user and user.is_authenticated:
            await self._db_remove_participant(user)
            await self._broadcast_participants()

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            return

        data = json.loads(text_data)
        print("Received data:", data)

        # WebRTC
        if 'signal_type' in data:
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'webrtc.signal',
                    'signal_type': data['signal_type'],
                    'signal_data': data['signal_data'],
                    'from': user.name,
                    'to': data.get('to'),
                    'stream_type': data.get('stream_type', 'webcam'),
                }
            )
            return

        # Chat message
        if data.get('message'):
            if data.get('file_path') and data.get('file_name'):
                file_path = data['file_path']
                file_name = data['file_name']
                uploaded_file = await self._save_file(file_path, file_name, user)
            else:
                uploaded_file = None

            msg_obj = await self._db_save_message(user, data['message'], uploaded_file)
            serializer = MessageSerializer(msg_obj)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat.message',
                    'message': serializer.data
                }
            )
        elif data.get('action') == 'update_stream':
            # Обновление состояния потока (например, включил микрофон)
            await self._update_stream_state(self.scope['user'], data)

            # Рассылаем обновление состояния пользователя
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'stream_update',
                    'user': self.scope['user'].name,
                    'stream_state': data
                }
            )

            # Также рассылаем полный список актуальных потоков
            streams = await self._get_all_streams()
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "streams_update",
                    "streams": streams,
                }
            )

        elif data.get('action') == 'admin_mute':
            # Только для преподавателей и админа
            if self.scope['user'].role == 'преподаватель' or self.scope['user'].role == 'админ':
                await self._mute_user(data['target_user'], mute=True)


    async def new_participant(self, event):
        # Отправлять только стримерам (т.е. тем, у кого активны webcam/screen)
        if self.scope["user"].name == event["new_user"]:
            return  # не слать самому себе

        streams = await self._get_all_streams()
        for stream in streams:
            if stream["user"] == self.scope["user"].name:
                await self.send(text_data=json.dumps({
                    "type": "new_participant",
                    "username": event["new_user"]
                }))
                break

    
    async def chat_message(self, event):
        # Сериализуем сообщение, чтобы получить данные с именем отправителя
        message_data = event["message"]
        message_serialized = message_data

        # Отправляем сериализованное сообщение в WebSocket
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message_serialized
        }))

    # Метод для сохранения файла в MinIO
    async def _save_file(self, file_path, file_name, user):
        """
        Сохраняет путь к файлу в базу, предполагая, что файл уже загружен в MinIO.
        """
        return await database_sync_to_async(UploadedFile.objects.create)(
            user=user,
            file_name=file_name,
            file_type='user_upload',
            path=file_path
        )

    # Handlers for group_send

    async def webrtc_signal(self, event):
        if event.get('to') and event['to'] != self.scope['user'].name:
            return

        await self.send(text_data=json.dumps({
            "type": "signal",
            "signal_type": event["signal_type"],
            "signal_data": event["signal_data"],
            "from": event["from"],
            "stream_type": event.get("stream_type", "webcam"),
        }))

    async def broadcast_participants(self, event):
        await self.send(text_data=json.dumps({
            "type": "participants_update",
            "participants": event["participants"],
        }))

    # = Вспомогательные методы для БД 

    async def _broadcast_participants(self):
        participants = await self._db_get_participants()
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'broadcast_participants',
                'participants': participants,
            }
        )
    async def stream_update(self, event):
        streams = await self._get_all_streams()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "streams_update",
                "streams": streams,
            }
        )


    

    @database_sync_to_async
    def _update_stream_state(self, user, state_data):
        stream, _ = Stream.objects.get_or_create(user=user, channel_id=self.channel_id)
        stream.is_audio_enabled = state_data.get('is_audio_enabled', stream.is_audio_enabled)
        stream.is_video_enabled = state_data.get('is_video_enabled', stream.is_video_enabled)
        stream.is_speaking = state_data.get('is_speaking', stream.is_speaking)
        stream.save()
    
    async def streams_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "streams_update",
            "streams": event["streams"]
        }))
    
    
    @database_sync_to_async
    def _mute_user(self, username, mute=True):
        try:
            target = User.objects.get(username=username)
            stream, _ = Stream.objects.get_or_create(user=target, channel_id=self.channel_id)
            stream.is_muted_by_admin = mute
            stream.save()
        except User.DoesNotExist:
            pass
    
    @database_sync_to_async
    def _get_all_streams(self):
        streams = Stream.objects.filter(channel_id=self.channel_id).select_related('user')
        return StreamSerializer(streams, many=True).data


    @database_sync_to_async
    def _db_get_participants(self):
        try:
            ch = Channel.objects.get(id=self.channel_id)
            return [u.name for u in ch.participants.all()]
        except Channel.DoesNotExist:
            return []

    @database_sync_to_async
    def _db_add_participant(self, user):
        try:
            Channel.objects.get(id=self.channel_id).participants.add(user)
        except Channel.DoesNotExist:
            pass

    @database_sync_to_async
    def _db_remove_participant(self, user):
        try:
            Channel.objects.get(id=self.channel_id).participants.remove(user)
        except Channel.DoesNotExist:
            pass

    @database_sync_to_async
    def _db_save_message(self, user, content, uploaded_file=None):
        ch = Channel.objects.get(id=self.channel_id)
        return Message.objects.create(
            sender=user,
            content=content,
            channel=ch,
            uploaded_file=uploaded_file
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = None  # ← добавлено, чтобы избежать ошибки в disconnect

        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_notifications_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.group_name:  # ← защита от ошибки
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event['title'],
            'message': event['message'],
            'image': event['image'],
        }))
