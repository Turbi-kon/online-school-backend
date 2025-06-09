from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, SubjectViewSet, TeachingAssignmentViewSet, admin_create_user, activate_user, pending_users, delete_user, update_user

router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'teachingassignments', TeachingAssignmentViewSet)

urlpatterns = [
    path('api/', include(router.urls)), #да
    path('api/create/', admin_create_user, name='admin_create_user'), #создать юзера
    path('api/<int:user_id>/activate/', activate_user, name='activate_user'), #подтвердить регистрацию
    path('api/pending_users/', pending_users, name='pending_users'), #ждущие подтверждения
    path('api/delete/<int:user_id>/', delete_user, name='delete_user'), #удаление пользователя
    path('api/update/<int:user_id>/', update_user, name='update_user'), #изменение
]