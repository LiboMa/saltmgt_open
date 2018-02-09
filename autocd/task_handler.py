# from background_task import background
#from django.contrib.auth.models import User


# load django q
#from django_q.tasks import async, result
#from autocd.autocd_keeper import *

# version=1.0
# written by testuser(Ma Libo)@ 2018.1.23
from __future__ import barry_as_FLUFL
__all__ = [ 'get_task_by_id',
            'output_checker',
            'get_nodegroups',
            'Tasks_deploy'
        ]
__version__ = '0.1'
__author__ = 'Ma Libo'


import os
import sys
import yaml
from django.utils import timezone
import subprocess

import json

#from .models import tasks


project_path="/opt/test/saltmgt/"
salt_path="/srv/salt/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saltmgt.settings")
#_ENVS = ['prod','cons','dev', 'init','test']
_DMZ = ['dmz1', 'dmz2', 'dmz3','temp']

sys.path.append(project_path)
sys.path.append(salt_path)
#os.chdir(project_path)

from django_autocd_deploy_run import *

def get_task_by_id(tid):
    from autocd.models import tasks
    if tid is None:
        return None
    else:
        task_queue = tasks.objects.select_related().get(pk=tid)
    return task_queue

def get_or_create_minions():
    '''This func get the minions list from local host
    and returns a minions list'''

    cmd = "sudo salt-key -L --out=json"

    from autocd.models import minions
    try:
        run_process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # try to decode from output and convert to json dict
        minion_list_json = json.loads(run_process.stdout.decode())
        for minion in minion_list_json['minions']:
            print ("add minions", minion)
            try:
                minions.objects.get_or_create(minion_name=minion, status='online')
            except:
                # ignore add error
                logging.warning("minion {0} checked".format(minion))

        return minions.objects.all()

    except Exception as err:
        raise logging.warning("error when geting minion list", err)
        return None


def output_checker(strings):

    try:
        data = strings.lower().split()

        if 'error' in data:
            return False
        if 'failed' in data:
            return False
        if 'failure' in data:
            return False

    except Exception as err:
        return False


def get_or_create_project(project_name, env):
    from autocd.models import AppEnv
    _ENVS = [ env.name for env in AppEnv.objects.all() ]

    project_dir = salt_path + project_name
    deploy_dir = salt_path + project_name + '/' + env
    temp_dir = project_dir + '/'+ env +'/' + "temp/"

    if os.path.isdir(project_dir):
        pass
    else:

        for app_env in _ENVS:
            for dmz in _DMZ:
                dmz_dir = "{0}/{1}/{2}".format(project_dir, app_env, dmz)
                os.makedirs(dmz_dir)
    return (project_dir, temp_dir)


def get_nodegroups():

    from autocd.models import minion_groups as mgs

    # get all groups
    qmgs = mgs.objects.select_related()
    # init nodegroups for salt master server
    nodegroups = {'nodegroups':{}}

    # initial all nodegroups for saltstack master which storing in master's
    # default dir: /etc/salt/master.d/nodegroups.conf
    for qg in qmgs:
        if qg.minions_set.values():
            nodegroups['nodegroups'][qg.group_name]=[m['minion_name'] for m in qg.minions_set.values()]

    with open('/etc/salt/master.d/nodegroups.conf','w+') as ymfile:
        yaml.safe_dump(nodegroups, ymfile, indent=4, default_flow_style=False)

    return nodegroups


class Tasks_deploy():

    def __init__(self,id=None):
        self.task = get_task_by_id(id)
        self.pillar =  self.task.env.pillar
        self.state =  self.task.env.state
        self.status =  self.task.status
        self.result =  self.task.result
        # task.env.project_name is a query set whitch returns a object
        # initial vars for deploy to salt
        self.salt_project_name =  str(self.task.env.project_name).lower()
        self.salt_env =  str(self.task.env).split('_')[1].lower()
        self.task_deploy_env =  str(self.task.env).lower()
        self.minion_group = self.task.env
        self.cmd =  None
        self.ret =  {'msg':
                        {'cmd':[],
                        'out': [],
                        'err': [],
                        'status': None
                        },
                    'version_number': None
                    }
        self.version_number = None

        # set nodegroups
        get_nodegroups()

    def set_pillar(self, pillar):

        if pillar:
    #        print ('check pillar{0}'.format(pillar))
            pillar_yaml = yaml.load(pillar)
    #        print ('check pillar{0}'.format(pillar_yaml))
        return pillar_yaml

    def set_state(self, state):

        state_file_abs_path = salt_path + self.salt_project_name + '/'+ self.task_deploy_env + '.sls'
        state_sls =  self.salt_project_name + '/'+ self.task_deploy_env

        logging.debug("setting state file - {0} - {1}".format(state_sls, state_file_abs_path))
        #return True

        if state:
            with open(state_file_abs_path, 'w') as sf:
                sf.write(state)
            return (state_sls, state_file_abs_path)
        else:
            self.ret['msg']['err'].append('set state file error')
            self.ret['msg']['status'] = False
            return self.ret['msg']['status']

    def download_code(self, url):

        try:
            # confs data - data, project_name, major version_number
            confs=get_definition_parser(url)
            self.ret['version_number'] = confs[2]
            #print (confs)
        except Exception as e:
            print ("ERROR: cannot get conf content with:", e)
            logging.error ("ERROR: cannot get conf content with:", e)

        project_dir, temp_dir = get_or_create_project(self.salt_project_name, self.salt_env)
        local_run('rm -rf {0}'.format(temp_dir))
        #print(self.ret['version_number'])

        #self.ret.append(app_name,version_number,app_env)
        #return self.ret
        for app_conf in confs[0]:
            app_name=app_conf[0]
            version_number=app_conf[1]
            dmz=app_conf[2]
            app_url=app_conf[3]
            app_env = self.salt_env

			# Get code from nexus server
            logging.debug("user - {0} : get_code: {1} - {2}".format(app_name, version_number, app_env))
            get_code(app_url, app_name, app_env, project_dir=project_dir)

			# Deploy code to saltstack master for local distribution

            d = deploy_to_saltstack(app_name, version_number, app_env, dmz, project_dir=project_dir)
            if d == 0:
                logging.info("deploy_to_saltstack:{0} - {1} - {2} - OK".format(app_name, version_number, app_env))
            else:
                logging.error("deploy_to_saltstack:{0} - {1} - {2} - FAILED".format(app_name, version_number, app_env))

        return self.ret


    #def deploy(self, deploy_url=self.task.deploy_url, deploy_env=self.task.env):
    def deploy(self):
        #if deploy_url and deploy_env:
        pillar_data = self.set_pillar(self.pillar)
        state_sls, state_abs_path = self.set_state(self.state)

        logging.debug("deploying state_file - {0} - abs:{1}".format(state_sls,state_abs_path))
        #return False

        #print ("task id:{0}, deploy_env:{1}, deploy_url:{2}, pillar_yaml:{3},state_data:{4}"\
        if pillar_data and state_sls:
            if os.path.isfile(state_abs_path):
                print ('downloading files from url: {0}'.format(self.task.deploy_url))

                self.download_code(self.task.deploy_url)

                # cmd = core deploy function, it call salt of master to deploy
                # application by nodegroups, e.g. minion_group
                self.cmd = ('/usr/bin/salt -t120 -N {0} state.apply {1} pillar="{2}" --out=json --out-indent -1'\
                        .format(str(self.minion_group).lower(), state_sls, pillar_data)
                        )
                print (self.cmd)
                self.ret['msg']['cmd'].append(self.cmd)

                try:
                    run_process = subprocess.run(self.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except Exception as cmd_err:
                    self.ret['msg']['err'].append(cmd_err)
                    self.ret['msg']['err'].append(run_process.stderr.decode().strip('\n'))
                    self.ret['msg']['status'] = False
                    return self.ret['msg']['err'].append(cmd_err)

                if run_process.returncode == 0:
                    #check=output_checker(run_process.stdout.decode())
                    check=True
                    #print ("!!!!!!!!!!!!!!!!!!check info!!!!!!!!!!", check)
                    if check is True:
                        self.ret['msg']['out'].append(run_process.stdout.decode())
                        self.ret['msg']['status'] = True
                        return self.ret['msg']['status']
                    else:
                        self.ret['msg']['err'].append(run_process.stdout.decode().strip('\n'))
                        self.ret['msg']['status'] = False
                        return self.ret['msg']['status']
                else:
                    self.ret['msg']['out'].append(run_process.stdout.decode().strip('\n'))
                    self.ret['msg']['err'].append(run_process.stderr.decode().strip('\n'))
                    self.ret['msg']['status']=False
                    return self.ret['msg']['status']

             #   return self.ret['msg']['status']

            else:
                self.ret['msg']['out'].append('state file error')
                self.ret['msg']['status']=False
                return self.ret['msg']['status']

            #    return self.ret['msg']['status']
        else:
            self.ret['msg']['out'].append('Pillar file error')
            self.ret['msg']['status']=False
            return self.ret['msg']['status']

    def report_status(self):
        '''task status: processing, ok, failure'''
        if self.ret['msg']['status']:
            self.task.status = "done"
            self.task.env.current_version = str(self.ret['version_number'])
            self.task.env.update_on = timezone.now()
            print (str(self.ret['version_number']))
            #self.task.result = self.cmd
            self.task.result = json.dumps(self.ret)
            self.task.date = timezone.now()
            self.task.save()
            self.task.env.save()
            return True
        else:
            self.task.status = "failed"
            self.task.result = json.dumps(self.ret)
            self.task.date = timezone.now()
            print (self.status)
            self.task.save()
            return False


def deploy_task(task_id):

    if task_id:
        new_deploy = Tasks_deploy(task_id)
        new_deploy.deploy()
        new_deploy.report_status()
        print (new_deploy.ret['msg']['status'])
    else:
        return False

def load_minions_task():

    return get_or_create_minions()

if __name__ == '__main__':
    import django
    django.setup()
    from autocd.models import *
    print ("djang setup OK!")
#
    for k,v in os.environ.items():
        print((k,v))
    #deploy_task(37)
    print (load_minions_task())
