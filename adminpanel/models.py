from django.db import models

class Group(models.Model):
    name = models.CharField(max_length=100)
    student_count = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class TeachingAssignment(models.Model):
    teacher = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.teacher.name} → {self.subject.name} ({self.group.name})'
