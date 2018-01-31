

[ -n "$1" ] && action=$1 
./django_site.sh $action
./qcluster_start.sh $action

