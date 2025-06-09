from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CurrentUserView, CreateUserView, student_self_register
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),            #получение токена для входа
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),           #обновление
    path('api/user/', CurrentUserView.as_view(), name='current_user'),                      #инфа по себе
    path('api/user/create', CreateUserView.as_view(), name='create-user'),                  #забыл
    path('api/register/', student_self_register, name='student_self_register'),             #регистрация от пользователя
]