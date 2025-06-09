from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from accounts.serializers import UserSerializer
from accounts.models import User
from .models import Group, Subject, TeachingAssignment
from .serializers import GroupSerializer, SubjectSerializer, TeachingAssignmentSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

class TeachingAssignmentViewSet(viewsets.ModelViewSet):
    queryset = TeachingAssignment.objects.all()
    serializer_class = TeachingAssignmentSerializer


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_create_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def activate_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        if user.is_active:
            return Response({"detail": "Пользователь уже активен."})
        user.is_active = True
        user.save()
        return Response({"detail": f"Пользователь {user.username} активирован."})
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден."}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pending_users(request):
    if request.user.role != 'админ':
        return Response({"detail": "Недостаточно прав."}, status=status.HTTP_403_FORBIDDEN)
    
    users = User.objects.filter(is_active=False)
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.delete()
        return Response({"detail": f"Пользователь {user.username} удалён."}, status=status.HTTP_204_NO_CONTENT)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserSerializer(user, data=request.data, partial=True)  # partial=True чтобы обновить только часть данных
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
