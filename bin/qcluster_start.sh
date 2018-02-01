#!/bin/sh
# This is script is used for managing django daemon.
# Wirtten by Libo.Ma @ 2014.2.19 Wed Feb 19 22:59:38 CST 2014
# Draft version 1.0

curdir=$(cd `dirname $0`;pwd)
rootdir=$(cd ..;pwd)
pidfile=$curdir/django_q.pid
logfile=$curdir/django_access.log
SITEPATH=$rootdir
PYTHON=python3
CMD="$PYTHON $SITEPATH/manage.py qcluster"
app_name='qcluster'


if [ -f /opt/rh/rh-python35/enable ];
then
    if [ -z "$LD_LIBRARY_PATH" ];
        then 
            source /opt/rh/rh-python35/enable
    else
        echo "RUNING ENV: $LD_LIBRARY_PATH"
    fi  
fi

start () {

# Check pid 
#if [ -f $pidfile ] && ps aux |grep ssh |grep -q `cat $pidfile`
if [ -f $pidfile ] && pgrep -F $pidfile
then
    echo "Django $app_name is running."
    exit 0
else
    # Startup running proc
    nohup $CMD >$logfile 2>&1 &
    
    if [ $? -eq 0 ];then

        echo "$!" >$pidfile
        echo "django $app_name is up"
    fi
fi

}

stop () {
    
    # Check pid
    
    # Check pidfile
    [ ! -f $pidfile ] && { echo "$app_name no running"; return 1; } || pid=`cat $pidfile` 
    # Check running process of ssh tunnel
    if pgrep -F $pidfile # updated on 2015.6.17
    then
        gid=$(ps ax -opid,pgid,ppid|grep $pid |grep -v grep|awk -F" " '{print $2}'|head -1)
        pkill -9 -g $gid 
        kill -9 $(ps aux |grep qcluster|grep -v grep) >/dev/null 2>&1;
        rm $pidfile; 
        return 0;
    else
        echo "django $app_name not running..."
        rm $pidfile; 
        return 1
    fi

}

reload () {

    # Check pidfile
    [ ! -f $pidfile ] && { echo "no running"; exit 1; } || pid=`cat $pidfile`

    # Reload configuration...
    #if ps aux |grep ssh |grep -q $pid
    if pgrep -F $pidfile # updated on 2015.6.17
    then
        kill -HUP $pid && return 0
    else
        echo "ssh tunnel not running..."
        exit 1
    fi

}

status () {

    # Check pidfile
    [ ! -f $pidfile ] && { echo "no running"; exit 1; } || pid=`cat $pidfile`
    
    if pgrep -F $pidfile # updated on 2015.6.17
    then
        echo "django $app_name with pid $pid"
    else
        echo "django service NOT running"
        return 1
    fi
}

help() {
        
    echo "Usage :sh `basename $0 ` [start|stop|status|reload|restart]"
    exit 1

}


# Check user input argv

[ -z $1 ] && help

#server=$2
#server=tinyboat

case "$1" in
    start)
        start 
        ;;
    restart)
        stop;
        sleep 1
        start
        ;;
    stop)
        stop && echo "django $app_name stopped"
        ;;
    status)
        status
        ;;
    reload)
        reload && echo "reload OK."
        ;;
    *)
        help
        ;;
esac

