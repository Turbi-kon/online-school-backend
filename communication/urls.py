from django.urls import path
from . import views

urlpatterns = [
    path('channels/', views.get_all_channels),
    path('upload/', views.upload_file, name='upload_file'),                                       #загрузка в minio из чата и сгенеренных файлов
    path("create/", views.create_notification, name="create-notification"),                       #создание уведов
    path('list/', views.NotificationsView.as_view(), name='notification-list'),                   #список уведов
    path('channels/create/', views.create_channel, name='create_channel'),                        #создание канала
    path('channels/<int:channel_id>/', views.channel_detail),                                     #просмотр инфы по каналу + редакт(для админпанели)
    path('channels/<int:channel_id>/get/', views.get_channel_details, name="get_channel_details"), #чисто просмотр инфы по каналу, чтобы не слетела загрузка сообщений в чате из бд
    path('channels/<int:channel_id>/participants/', views.get_participants),                      #просмотр инфы по пользователям канала
    path('channels/<int:channel_id>/join/', views.join_channel),                                  #апи для подключения к каналу
    path('channels/<int:channel_id>/leave/', views.leave_channel),                                #да, но
    path('channels/<int:channel_id>/messages/', views.channel_messages, name='channel-messages'), #чисто сообщения по каналу, возможно стоит убрать сообщения из инфы по каналу(это надо чтобы восстановить историю чата)
    path('gicons/', views.list_minio_icons, name='list_minio_icons'),                             #получение иконок(пока только для уведомлений, там потом что-то придумаем мб)
    path('channels/<int:channel_id>/delete/', views.delete_channel, name='delete_channel'),       #удаление канала
    path('transcribe/start/', views.start_transcription_session, name='start'),                                 #нейронка
    path('transcribe/chunk/', views.upload_transcription, name='divide'),                                  #нейронка
    path('transcribe/finish/', views.finish_transcription_session, name='finish_transcription_session'), #нейронка
]