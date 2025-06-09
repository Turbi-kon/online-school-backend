from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from adminpanel.models import Group

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLES = [('студент', 'Student'), ('преподаватель', 'Teacher'), ('админ', 'Admin')]
    name = models.CharField(max_length=255, null=False, default="Ф.И.О.")
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=20, choices=ROLES)  # student, teacher, admin
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.CharField(max_length=100, null=True, blank=True) #это чисто для преподователей( доцент, кандидат и т.д.)
    student_number = models.CharField(max_length=20, null=True, blank=True)  # Номер зачётки для студентов
    email = models.EmailField(unique=True, null=True, blank=True) #пошта

    # Мусор для AbstractBaseUser (вроде без этого низя, хз)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['name']

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.get_next_available_id()
        super().save(*args, **kwargs)

    @staticmethod
    def get_next_available_id():
        '''
        Это для того чтобы когда удаляются из базы пользователи id был не (max(id) + 1) а первый свободный
        было там 1000 idшников, а потом удалили 521, 33, и 128
        при добавлении нового пользователя будет не 1001 а 33
        '''
        # Получаем список всех занятых ID
        taken_ids = set(User.objects.values_list('id', flat=True))
        # Генерируем все возможные ID от 1 до max текущего ID + 1
        all_ids = set(range(1, max(taken_ids) + 2))
        # Находим все свободные ID
        free_ids = sorted(list(all_ids - taken_ids))
        if free_ids:
            return free_ids[0]  # Возвращаем первый свободный ID
        return max(taken_ids) + 1  # Если нет свободных, возвращаем следующий номер