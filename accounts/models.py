from django.db import models
from django.contrib.auth.models import User
from autocd.models import projects


# Create your models here.

class UserPrivileges(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    info = models.CharField(max_length=100, blank=True)
    projects = models.ManyToManyField(projects)

    def __str__(self):
        return self.user.username
