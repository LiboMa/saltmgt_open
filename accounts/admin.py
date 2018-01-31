from django.contrib import admin

# Register your models here.

from .models import *
#from .models import deploy_env
#from .models import tasks
#from .models import minions, minion_groups

#admin.site.register(UserProfiles)
admin.site.register(UserPrivileges)
