#!/usr/bin/env python
import os, sys
import yaml
import requests
import subprocess
#import salt # this will effect logging mode, disabled here @2017.11.14
#import salt.key

# This script is used to deploy data for saltstack master which is also can be
# run by Jekins(salt-api) @ written by 
#
# Version=1.0
# Version=1.1
# Version=2.0
'''
History:
CGP project supported @ 8.30.2017
Using unzip mode instead of folders level transferring @ 11.10.2017 updated

'''

# Set initial variables
rootdir='/srv/salt/'
ENVs=['int', 'dev','cons', 'prod']
nexus_server='10.42.67.6:9999'

# Set with no proxy for testing purpose
os.environ['NO_PROXY']='localhost'

# Log Settings
import logging
LOGFILE=rootdir+'logs/deploy.log'
LOGLEVEL = logging.INFO #DEBUG, INFO, WARNING, ERROR, CRITICAL)
FORMAT = '%(asctime)s %(levelname)s: Django.autocd.Task.Handler: %(message)s'
logging.basicConfig(filename=LOGFILE, level=LOGLEVEL, format=FORMAT)


def get_definition_parser(url):
    ''' This file is to parse configuration file from remote nenux server.
        get_definition_parser(r_url)

        output:
            [('app-online-client', '1.1.11', 'dmz1'),
            ('app-online-backend-feproxy', '1.2.0', 'dmz1'),
            ('app-online-admin-portal', '1.1.0', 'dmz2'),
            ('app-online-backend-api', '1.2.0', 'dmz2'),
            ('app-online-backend-admproxy', '1.2.0', 'dmz2')]

    '''
    try:
        r=requests.get(url)

    except Exception as e:
        print (e)

    cfg = yaml.load(r.content)
    data = []

    apps=cfg['components'].keys()
    project_name=cfg['application']['metadata']['application-name']
    version_number=cfg['application']['metadata']['version-number']
    if apps:
        logging.debug("get_definition_parser: get definiation file OK")
    else:
        logging.error("get_definition_parser: get definiation file FAILED")

    # get code and push code
    for app in apps:
        #print "{0} {1} {2}".format(app, cfg['components'][app]['version'], cfg['components'][app]['dmz'])
        data.append((app, cfg['components'][app]['version'], cfg['components'][app]['dmz'], cfg['components'][app]['url']))
    # append project name to datafile
    return (data,project_name,version_number)


def check_pillar_vars():
    # get pillar_vars from definition file
    # logging.info("deploy_to_saltstack:{0} - {1} - {2} - OK".format(app_name, version_number, app_env))
    # compare pilar with local pillar file
    # if yes, pass
    # if no, reaise Exception
    pass


def get_code(url, app_name, app_env,unzip=True, project_dir=None):
    ''' This file is used to get from the configuration file from the parser and download from nexus server.
    '''
    filename=url.split('/')[-1]
    temp_dir=project_dir+'/' + app_env + '/temp/'
    zip_filename=temp_dir + filename

    r = requests.get(url, stream=True)
    if not r.ok:
        logging.error("get_code: url {0} download failed,return code: {1}".format(url,r.status_code))
        print ("ERROR: get_code: url {0} - return code: {1}, check logfile:{2} for detailed".format(url,r.status_code, LOGFILE))
        sys.exit(r.status_code)

    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
        logging.debug("get_code: making dir {0}".format(temp_dir))
        print ("making dir", temp_dir)

    # Extract file from zip
    if os.path.isfile(zip_filename):
        os.remove(zip_filename)
    else:
        # downloading file from nenux server
        with open(zip_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        logging.info("get_code: downloading file {0} OK".format(zip_filename))

        # parse the file name from zip file without version number
        if unzip:
            s_index=zip_filename.rindex("-")
            local_filename=zip_filename[:s_index]

            cmd='unzip {0} -d {1} >/dev/null'.format(zip_filename, local_filename)

            if local_run(cmd) == 0:
                print ("file {0} get done".format(local_filename))
    return zip_filename


def local_run(cmd):

    ''' This function is used to run local command which running on Linux
    '''
    logging.debug("local_run: command:" + cmd )
    p=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    print ("local run: command:", cmd)

    if out:
        logging.debug("local run - command:".format(out) )
        print (out)
    elif err:
        logging.error("local_run: command ".format(err) )
    return p.returncode


def deploy_to_saltstack(app_name, version_number, app_env, dmz, rsync=True, project_dir=None):
    ''' This function is used to deploy_code from temp file to saltstack file
    '''
    temp_dir=project_dir+'/' + app_env + '/temp/'
    #temp_file=temp_dir + app_name + '-'+ version_number
    temp_file=temp_dir + app_name
    local_file='{0}/{1}/{2}/{3}'.format(project_dir, app_env, dmz, app_name)

    #print temp_file, local_file
    copy_cmd='cp {0}-{1}.zip {2}.zip'.format(temp_file, version_number,local_file )

    if rsync:
        rsync_cmd='/usr/bin/rsync -avz --delete {0} {1}'.format(temp_file, os.path.dirname(local_file))
        local_run(rsync_cmd)
        print (rsync_cmd)
    return local_run(copy_cmd)


def check_minions(minion_id):
    if minion_id:
        logging.info("Testing minion id: {0}".format(minion_id))
        print (("Testing minion id: {0}...".format(minion_id)))
        return local_run('sudo /usr/bin/salt "{0}" test.ping'.format(minion_id))

def push_code(agent, state_file=None, timeout='180'):

    if state_file is None:
        logging.error("push_code: no state file found! - pushing code for {0} failed.".format(agenti))
        return "no state file found"
    logging.debug("push_code: pushing code to {0} with config - {1}".format(agent, state_file))
    if check_minions(agent) == 0:
    #if check_minions(agent):
        cmd='sudo /usr/bin/salt -t{2} {0} state.apply {1}'.format(agent, state_file, timeout)
        local_run(cmd)
    else:
        logging.error("Agent error {0}, no response".format(agent))
        return False


def show_help():

    print ('''
Usage: python deploy_run.py yaml_url [int|dev|cons|prod]

for example:

This script is used get source code from nexus server and deploy to
target/agent servers.
version 1.1''')
    sys.exit(55)


if __name__ == '__main__':

    # get_deploy_code('app-online-client', '1.1.11', 'int', 'dmz1')
    # get_deeinition_parser(r_url)
    import sys

    if len(sys.argv)<3:
        show_help()

    r_url,app_env=sys.argv[1],sys.argv[2]

    # check input :r_url
    if not r_url.endswith('yaml'):
        print ("ERROR: url invalid, should be a yaml definiation file!")
        sys.exit()

    # check input : application environment
    if app_env not in ENVs:
        print (app_env)
        show_help()

    logging.info("parsing definition file {0}".format(r_url))
    try:
        confs=get_definition_parser(r_url)
        print (confs)
    except Exception as e:
        print ("ERROR: cannot get conf content with:", e)
        sys.exit()

    # check pillar file of definition @ 2017.9.8
    #if not check_pillar_vars()
    #    logging.error()
    # Init project folder
    project_name = confs[-1]
    projectdir = rootdir + confs[-1].strip('/')
    import getpass
    userID = getpass.getuser()
    #print projectdir, project_name
    #sys.exit()

    # Clean the temp data
    temp_dir=projectdir+'/'+ app_env+ '/temp/'
    local_run('rm -rf {0}'.format(temp_dir))

    # Initialization
    for app_conf in confs[0]:
        app_name=app_conf[0]
        version_number=app_conf[1]
        dmz=app_conf[2]
        app_url=app_conf[3]


        # Get code from nexus server
        logging.debug("user - {0} : get_code: {1} - {2} - {3}".format(userID, app_name, version_number, app_env))
        get_code(app_url, app_name, app_env, project_dir=projectdir)

        # Deploy code to saltstack master for local distribution

        if deploy_to_saltstack(app_name, version_number, app_env, dmz, project_dir=projectdir) == 0:
            logging.info("deploy_to_saltstack:{0} - {1} - {2} - OK".format(app_name, version_number, app_env))
        else:
            logging.error("deploy_to_saltstack:{0} - {1} - {2} - FAILED".format(app_name, version_number, app_env))

    # Push code to agent(minion) servers
    print ("pushing code for ENV: {0}".format(app_env))
    print ("logfile {0}".format(LOGFILE))
#   debug breakpoint sys.exit()

    # example:
        #push_code("tgt",state_file)

