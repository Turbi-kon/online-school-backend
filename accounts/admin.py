from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import UserCreationForm, UserChangeForm

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('username', 'email', 'name', 'role', 'group', 'student_number', 'position', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'name', 'role')
    list_filter = ('role', 'group', 'is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('name', 'email', 'role', 'group', 'student_number', 'position')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'role', 'group', 'student_number', 'position', 'password1', 'password2'),
        }),
    )

    ordering = ('username',)

