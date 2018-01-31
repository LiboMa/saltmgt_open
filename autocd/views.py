from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponse
# from django.urls import reverse
from django.contrib.auth.decorators import login_required

from django.views.decorators.csrf import requires_csrf_token

# Create your views here.

from .models import projects
#from .models import deploy_env
from .models import  MGDeployEnv as deploy_env
from .models import tasks

from accounts.models import UserPrivileges

import json

# import background tasks
#from .test_tasks import deploy_to_env, notify_task

# import task q here
from django_q.tasks import async, result, fetch


# from django_q.models impor

@login_required(login_url='/accounts/login/')
def index(request):
    # deploy_env_list = deploy_env.objects.all()
    project_list = projects.objects.all()
    deploy_env_ob = deploy_env.objects.select_related().all()
    tasks_list = tasks.objects.select_related().all()
    context = {'projects': project_list, 'deploy_env_list': deploy_env_ob, 'tasks': tasks_list}
    #return HttpResponse("user is: {0}".format(request.user))
    return render(request, './index.html', context)

@login_required(login_url='/accounts/login/')
def projects_view(request):
    '''
        request is a web object which can be accessed request.user etc.
    '''
    try:
        UserPrivileges.objects.exists()
        privileged_projects = UserPrivileges.objects.get(user_id=request.user.id).projects.all()
        #return HttpResponse(privileged_projects)
        #return HttpResponse(request.user.id)
        #return HttpResponse(user_pri)
        project_list = privileged_projects
        #deploy_env_ob = deploy_env.objects.select_related().all()
        deploy_env_ob = deploy_env.objects.filter(project_name_id__in=privileged_projects)
        #return HttpResponse(deploy_env_ob)
        #tasks_list = tasks.objects.select_related().all()
        tasks_list = tasks.objects.filter(env_id__in=deploy_env_ob).all().order_by('-id')
        context = {'projects': project_list, 'deploy_env_list': deploy_env_ob, 'tasks': tasks_list}
        #return HttpResponse("user is: {0}".format(request.user))
        return render(request, './project_view.html', context)
    except Exception:
        context = {'projects': None, 'deploy_env_list': None, 'tasks': None}
        return render(request, './project_view.html', context)


@login_required(login_url='/accounts/login/')
def deploy(request, deploy_env_id):
    if request.method == 'GET':
        # deploy_env_ob = deploy_env.objects.get(pk=deploy_env_id)
        deploy_env_tasks = deploy_env.objects.select_related().get(pk=deploy_env_id)
        # task = tasks.objects.get(env_id=deploy_env_id)
        context = {'tasks': deploy_env_tasks,
                   'error_msg': "deploy env not found"}
        return render(request, './deploy.html', context)


@login_required(login_url='/accounts/login/')
def project(request, project_id):
    if request.method == 'GET':
        # deploy_env_ob = deploy_env.objects.get(pk=deploy_env_id)
        privileged_projects = UserPrivileges.objects.get(user_id=request.user.id).projects.all()
        project_list = privileged_projects
        #return HttpResponse(project_list)

        deploy_env_ob = deploy_env.objects.select_related().filter(project_name_id=project_id)

        tasks_query_list = tasks.objects.filter(env_id__in=deploy_env_ob).order_by('-id')
        # task = tasks.objects.get(env_id=deploy_env_id)
        context = {'projects':project_list,
                'deploy_env_list': deploy_env_ob,
                   'tasks': tasks_query_list,
                   'error_msg': "deploy env not found"}
        return render(request, './project.html', context)


@requires_csrf_token
@login_required(login_url='/accounts/login/')
def deploy_new(request, deploy_env_id):
    # deploy_env_ob = deploy_env.objects.get(pk=deploy_env_id)
    # check auth
    if request.method == 'GET':
        context = {'deploy_env_id': deploy_env_id}
        return render(request, './test.html', context)

    if request.method == 'POST':
        # validate post projects
        privileged_projects = UserPrivileges.objects.get(user_id=request.user.id).projects.all()
        de_project = deploy_env.objects.get(pk=deploy_env_id).project_name

        if de_project in privileged_projects:

            # get value of form
            data = request.POST
            print((data))
            # insert into db
            new_task = tasks.objects.create(deploy_url=data.get('deploy_url'),
                                            env_id=data.get('deploy_env_id'),
                                            owner="dkx4oih",
                                            status="pending"
                                            )
            env_obj = deploy_env.objects.get(pk=deploy_env_id)
            env_obj.pillar = data.get('pillar')
            env_obj.state = data.get('state')
            env_obj.save()

            # new Tasks - run salt deploy command here
            task_qid = async('autocd.task_handler.deploy_task', new_task.id )

            context = { 'data': data,
                    'deploy_env_id' : deploy_env_id,
                    'error_msg': "deploy fielded"}
            # return render(request,'./test.html', context)
            # redirect to details
            return redirect('/autocd/project/' + str(env_obj.project_name.id) + '/')

        else:
            return HttpResponse('Post Permission Denied')


from .models import minion_groups
from .models import AppEnv, MGDeployEnv

@requires_csrf_token
@login_required(login_url='/accounts/login/')
def mgdeployenv(request, project_id=None):

    try:
        project_obj = projects.objects.get(pk=project_id)
    except Exception:
        project_obj = None

    app_env_obj = AppEnv.objects.all()

    context={'project': project_obj,
             'app_envs': app_env_obj,
             'error_msg': "",
             'app_title': "Add"
             }
    if request.method =='GET':

        return render(request, './mg_deploy_env.html', context)

    if request.method == 'POST':
        data = request.POST
        # get environment name instance of object
        env_name = AppEnv.objects.get(name=data.get('app_env'))
        project_name = data.get('project_name').lower()
        # create minion_groups for deploy env
        mg_env_obj = data.get('mg_deploy_env').lower()

        if not mg_env_obj.startswith(project_name):
            error_msg = 'Invalid format, first field should starts with project name, like:{0}_{1}_xx '\
                .format(project_name, env_name)
            context['error_msg'] = error_msg
            return render(request, "./mg_deploy_env.html", context)

        pillar = data.get('pillar')
        state = data.get('state')

        try:
            mg_obj = minion_groups.objects.create(group_name=mg_env_obj, project_id=project_id)
        # create mg_denv_obj
            mg_denv_obj = MGDeployEnv(deploy_env=mg_obj, project_name=project_obj, env_name=env_name,
                                  pillar=pillar,
                                  state=state)
            mg_denv_obj.save()
        except Exception as error_msg:
            context['error_msg'] = error_msg
            return render(request, "./mg_deploy_env.html", context)

        render(request, "./mg_deploy_env.html", context)
        return redirect('/autocd/project/' + str(project_id))


@requires_csrf_token
@login_required(login_url='/accounts/login/')
def change_mgdeployenv(request, mg_deploy_env_id):

    try:
        mg_denv_obj = MGDeployEnv.objects.get(pk=mg_deploy_env_id)
    except Exception as err:
        return HttpResponse("minion_groups get error", err)
    project_obj = mg_denv_obj.project_name
    project_id = mg_denv_obj.project_name_id
    app_env_obj = AppEnv.objects.all()

    context={'project': project_obj,
             'app_envs': app_env_obj,
             'mg_deploy_env': mg_denv_obj,
             'error_msg': "",
             'app_title': "Change"
             }
    if request.method =='GET':

        return render(request, './mg_deploy_env.html', context)

    if request.method == 'POST':
        data = request.POST
        # get environment name instance of object
        env_name = AppEnv.objects.get(name=data.get('app_env'))
        project_name = data.get('project_name').lower()
        # create minion_groups for deploy env
        mg = data.get('mg_deploy_env').lower()

        if not mg.startswith(project_name):
            error_msg = 'Invalid format, first field should starts with project name, like:{0}_{1}_xx '\
                .format(project_name, env_name)
            context['error_msg'] = error_msg
            return render(request, "./mg_deploy_env.html", context)

        pillar = data.get('pillar')
        state = data.get('state')
        mg_obj = minion_groups.objects.get(pk=mg_denv_obj.deploy_env_id)
        env_obj = AppEnv.objects.get(pk=mg_denv_obj.env_name_id)

        try:
        # update mg_denv_obj

            mg_obj.group_name = mg
            env_obj.env_name = env_name
            mg_denv_obj.pillar = pillar
            mg_denv_obj.state = state

            mg_denv_obj.save()
            env_obj.save()
            mg_obj.save()

        except Exception as error_msg:
            context['error_msg'] = error_msg
            return render(request, "./mg_deploy_env.html", context)

        return redirect('/autocd/project/' + str(project_id))

@requires_csrf_token
@login_required(login_url='/accounts/login/')
def delete_mgdeployenv(request, project_id, mg_deploy_env_id):

    if mg_deploy_env_id:
        try:
            # get Minion Groups Objects via MG Deploy environment
            mg_denv_obj = MGDeployEnv.objects.get(pk=mg_deploy_env_id)
            mg_obj = MGDeployEnv.objects.get(pk=mg_deploy_env_id).deploy_env
            #return HttpResponse(mg_obj)
            project_id = mg_denv_obj.project_name_id
            #return HttpResponse(project_id)
            mg_obj.delete()
            return redirect('/autocd/project/' + str(project_id))
        except Exception as err:
            return HttpResponse("Error info", err)
    return None


def hook_tasks(task):
    print(task.result)


def tasks_detail(request, task_id=None):
    if task_id is None:
        task_list = tasks.objects.select_related().all()
        context = {'tasks_list': task_list}
        return render(request, './tasks.html', context)
    else:
        task = tasks.objects.get(pk=task_id)
        return HttpResponse("Result:".format(task.result))


def show_task_result(request, task_id):
    msg = []
    if task_id:
        task = tasks.objects.get(pk=task_id)
        try:
            result = json.loads(task.result)
        except Exception as error_msg:
            #msg.append("no output,:{0}".format(error_msg))
            #msg.append("no output: {0}".format(error_msg))
            result = None

        context = {'result': result,
                'task': task,
                'error_msg': msg
                }
        #return HttpResponse("Result of #{0}: {1}".format(task.id, result['msg'] ))
        return render(request, './task_result.html', context)
