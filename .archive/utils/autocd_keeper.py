#!/usr/bin/env python3

#!/usr/bin/env python3

import os
import sys
import yaml
from django.utils import timezone

project_path="/opt/test/saltmgt/"
salt_path="/srv/salt/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saltmgt.settings")

sys.path.append(project_path)
sys.path.append(salt_path)
#os.chdir(project_path)

import deploy_run as dr

def tasks_parser(qt=None):
    if qt is None:
        tasks_queue = tasks.objects.select_related().filter(status='processing')
    else:
        tasks_queue = tasks.objects.select_related().filter(env_id=qt)
    return tasks_queue

def get_task_by_id(tid):
    from autocd.models import tasks
    if tid is None:
        return None
    else:
        task_queue = tasks.objects.select_related().get(pk=tid)
    return task_queue


def get_or_create_project(project_name):

    project_dir = salt_path + project_name
    temp_dir = project_dir + '/' + "temp"

    if os.path.isdir(project_dir):
        return project_dir
    else:
        ENVS = ['prod','cons','dev', 'init']
        DMZ = ['dmz1', 'dmz2', 'dmz3']

        os.makedirs(temp_dir)
        for env in ENVS:
            env_dir = "{0}/{1}".format(project_dir, env)
            os.makedirs(env_dir)
            for dmz in DMZ:
                dmz_dir = "{0}/{1}".format(env_dir, dmz)
                os.makedirs(dmz_dir)
        return project_dir


def get_nodegroups():

    from autocd.models import minion_groups as mgs

    # get all groups
    qmgs = mgs.objects.select_related()
    # init nodegroups for salt master server
    nodegroups = {'nodegroups':{}}
    for qg in qmgs:
        if qg.minions_set.values():
            nodegroups['nodegroups'][qg.group_name]=[m['minion_name'] for m in qg.minions_set.values()]

    with open('nodegroups.conf','w+') as ymfile:
        yaml.safe_dump(nodegroups, ymfile, indent=4, default_flow_style=False)

    return nodegroups


def command_call(status, pillar, state, url):

    # init environment
    print ("I am initializaing the environment")
    # - setup & check folder structure
    # - download files
    # - setup pillar & state

    # do tasks using loop
    # upload result

    tasks_ids=[ 11, 12, 13, 14, 15 ]
    # set status

class Tasks_deploy():

    def __init__(self,id=None):
        self.task = get_task_by_id(id)
        self.pillar =  self.task.env.pillar
        self.state =  self.task.env.state
        self.status =  self.task.status
        self.result =  self.task.result

    def set_pillar(self, pillar):

        if pillar:
    #        print ('check pillar{0}'.format(pillar))
            pillar_yaml = yaml.load(pillar)
    #        print ('check pillar{0}'.format(pillar_yaml))
        return pillar_yaml

    def set_state(self, state):

        state_file_abs_path = salt_path + str(self.task.env.project_name).lower() + '/'+ str(self.task.env).lower() + '.sls'
        state_file_path =  str(self.task.env.project_name).lower() + '/'+ str(self.task.env).lower()

        if state:
            with open(state_file_abs_path, 'w') as sf:
                sf.write(state)
            return (state_file_path, state_file_abs_path)
        else:
            print ("set state error")
            return None

    #def deploy(self, deploy_url=self.task.deploy_url, deploy_env=self.task.env):
    def deploy(self):

        #if deploy_url and deploy_env:
        pillar_data = self.set_pillar(self.pillar)
        state_sls, state_abs_path = self.set_state(self.state)
        #print ("task id:{0}, deploy_env:{1}, deploy_url:{2}, pillar_yaml:{3},state_data:{4}"\
        if pillar_data and state_sls:
            if os.path.isfile(state_abs_path):
                print ('downloading files from url{0}'.format(self.task.deploy_url))

                print ('deploy cmd: salt -N {0} state.apply {1} pillar="{2}"'\
                        .format(str(self.task.env).lower(), state_sls, pillar_data)
                        )
                self.task.result = self.task.deploy_url
                return True
            else:
                print ('ERROR: state file not exist')
                return False
        else:
            return False
        #print ("task id:{0}, deploy_env:{1}, deploy_url:{2}, pillar_yaml:{3}"\
        #        .format(
        #            self.task.id,
        #            self.task.env,
        #            self.task.deploy_url,
        #            pillar_data,
        #            self.state
        #            )
        #        )


    def report_status(self):
        '''task status: processing, ok, failure'''
        if self.deploy():
            self.task.status = "OK"
            #self.task.result = "deploy output here"
            print (self.status)
            self.task.save()
            return True
        else:
            self.task.status = "failure"
            self.task.result = "deploy output here"
            self.task.date = timezone.now()
            print (self.status)
            self.task.save()
            return None


if __name__ == '__main__':
    import django
    django.setup()
    from autocd.models import *
    print ("djang setup OK!")

    project_dir = get_or_create_project('test_fso')
    if project_dir:
        print ("Project dir ok", project_dir)

    print (get_nodegroups())

    #new_deploy = Tasks_deploy()
    print ("starting deploy task")
    new_deploy=Tasks_deploy(35)


    new_deploy.deploy()
    new_deploy.report_status()
    #if qt:
    #    for t in qt:
    #        print ("task id:{0}, deploy_env:{1}, deploy_url:{2}".format(t.id, t.env, t.deploy_url))
            #dr.get_definition_parser(url)
