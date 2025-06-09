from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from .models import User
from rest_framework import serializers, status
from rest_framework.response import Response


User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]  # Требуется аутентификация

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


class CreateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'админ':
            return Response({'detail': 'Нет доступа'}, status=403)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def student_self_register(request):
    data = request.data.copy()
    data['role'] = 'студент'
    data['is_active'] = False  # заявка, не активен

    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({"detail": "Регистрация отправлена, ожидайте подтверждения администратора."}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
