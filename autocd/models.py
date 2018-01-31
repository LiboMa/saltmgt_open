from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class projects(models.Model):
    #env = models.ForeignKey(deploy_env, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=200, unique=True)
    #owner = models.CharField(max_length=200)
    #user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.project_name


class minion_groups(models.Model):
    group_name = models.CharField(max_length=100, unique=True)
    project = models.ForeignKey(projects, on_delete=models.CASCADE)

    def __str__(self):
        return self.group_name


class minions(models.Model):

    minion_name = models.CharField(max_length=100, unique=True)
    groups_name = models.ManyToManyField(minion_groups)
    status = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.minion_name


class AppEnv(models.Model):

    name = models.CharField(max_length=200, unique=True, default="INIT")
    def __str__(self):
        return self.name

class MGDeployEnv(models.Model):
    deploy_env = models.OneToOneField(minion_groups, on_delete=models.CASCADE)
    project_name = models.ForeignKey(projects, on_delete=models.CASCADE)
    env_name = models.ForeignKey(AppEnv, on_delete=models.CASCADE)
    pillar = models.TextField()
    state = models.TextField()
    current_version = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=200, blank=True)
    comments = models.CharField(max_length=200, blank=True)
    update_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.deploy_env)



class tasks(models.Model):
    #question = models.ForeignKey(Question, on_delete=models.CASCADE)
    #project_name = models.ForeignKey(projects, on_delete=models.CASCADE)
    env = models.ForeignKey(MGDeployEnv, on_delete=models.CASCADE)
    deploy_url = models.CharField(max_length=200)
    owner = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=200, blank=True)
    result = models.TextField(blank=True)

    def __str__(self):
        return self.deploy_url
