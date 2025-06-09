from rest_framework import serializers
from .models import Group, Subject, TeachingAssignment

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'student_count')

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name')

class TeachingAssignmentSerializer(serializers.ModelSerializer):
    teacher = serializers.StringRelatedField()
    subject = serializers.StringRelatedField()
    group = serializers.StringRelatedField()

    class Meta:
        model = TeachingAssignment
        fields = ('id', 'teacher', 'subject', 'group')
