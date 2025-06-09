from rest_framework import serializers
from .models import User
from adminpanel.models import Group

class UserSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        required=False,
        allow_null=True
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'name', 'username', 'email', 'password',
            'role', 'group', 'student_number',
            'position', 'is_active', 'is_staff'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.role != 'студент':
            rep.pop('group', None)
            rep.pop('student_number', None)
        return rep

    def validate(self, data):
        role = data.get('role')
        if role == 'студент':
            if not data.get('group'):
                raise serializers.ValidationError({"group": "Группа обязательна для студента."})
            if not data.get('student_number'):
                raise serializers.ValidationError({"student_number": "Номер зачётки обязателен для студента."})
        return data
