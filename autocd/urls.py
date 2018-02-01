from django.urls import path

from . import views

app_name = 'autocd'
urlpatterns = [
    path('', views.projects_view, name='index'),
    path('project/<int:project_id>/', views.project, name='project'),

    path('deploy/<int:deploy_env_id>/', views.deploy, name='deploy'),
    path('deploy/<int:deploy_env_id>/new/', views.deploy_new, name='deploy_new'),
	path('project/<int:project_id>/mgdeployenv/add/', views.mgdeployenv, name='mgdeployenv'),
    path('project/<int:project_id>/mgdeployenv/<int:mg_deploy_env_id>/delete/', views.delete_mgdeployenv, name='delete_mgdeployenv'),

	path('mgdeployenv/<int:mg_deploy_env_id>/change/', views.change_mgdeployenv, name='change_mgdeployenv'),

    path('tasks/', views.tasks_detail, name='tasks_detail'),
    path('result/<int:task_id>/', views.show_task_result, name='task_result'),

    path('miniongroups/', views.miniongroups_view, name='miniongroups'),
    path('miniongroups/<int:miniongroup_id>/change/', views.miniongroups_change, name='miniongroups_change'),
#    path('<int:question_id>/', views.detail, name='detail'),
]
