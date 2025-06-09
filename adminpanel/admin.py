from django.contrib import admin
from .models import Group, Subject, TeachingAssignment

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_count')
    search_fields = ('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'group')
    search_fields = ('teacher__username', 'subject__name', 'group__name')
    list_filter = ('group', 'subject')
