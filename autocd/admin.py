from django.contrib import admin

from .models import projects
#from .models import deploy_env
from .models import tasks
from .models import minions, minion_groups
from .models import AppEnv, MGDeployEnv

# Register your models here.

admin.site.register(projects)
#admin.site.register(deploy_env)
admin.site.register(tasks)
admin.site.register(minions)
admin.site.register(minion_groups)
admin.site.register(AppEnv)
admin.site.register(MGDeployEnv)
