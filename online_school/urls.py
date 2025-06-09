"""
URL configuration for online_school project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt import views as jwt_views
from rest_framework import routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions

from adminpanel.views import GroupViewSet
router = routers.DefaultRouter()
router.register(r'groups', GroupViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="Online School API",
        default_version='v1',
        description="API для онлайн-школы",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@onlineschool.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
    path('adminpanel/', include('adminpanel.urls')),
    path('accounts/', include('accounts.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('communication/', include('communication.urls')),
]