# settings.py
# active directory authentication module
AD_DNS_NAME = 'FS86.VWF.VWFS-AD'	 # FQDN of your DC (using just the Domain Name to utilize all DC's)
# If using non-SSL use these
#AD_LDAP_PORT=389
#AD_LDAP_URL='ldap://%s:%s' % (AD_DNS_NAME,AD_LDAP_PORT)
# If using SSL use these:
AD_LDAP_PORT=389
#AD_LDAP_URL='ldaps://%s:%s' % (AD_DNS_NAME,AD_LDAP_PORT)
AD_LDAP_URL='ldap://%s:%s' % (AD_DNS_NAME,AD_LDAP_PORT)
AD_SEARCH_DN = 'DC=fs86,DC=vwf,DC=vwfs-ad'
AD_NT4_DOMAIN = 'FS86.VWF.VWFS-AD'
AD_SEARCH_FIELDS = ['mail','givenName','sn','sAMAccountName','memberOf']
#AD_MEMBERSHIP_ADMIN = ['AdminGroup']	# this ad group gets superuser status in django
# only members of this group can access
#AD_MEMBERSHIP_REQ = AD_MEMBERSHIP_ADMIN + ['Group1',
#                                           'Group2',
#                                           'Group3']
#AD_CERT_FILE = '/path/to/ca/cert'	# this is the certificate of the Certificate Authority issuing your DCs certificate
AD_DEBUG=True #Set to false for prod, Slows things down ALOT
AD_DEBUG_FILE='/tmp/ldap.debug'


#AUTHENTICATION_BACKENDS = (
#    'autocd.backend.ActiveDirectoryAuthenticationBackend'
    #'django.contrib.auth.backends.ModelBackend' #Comment out to prevent authentication from DB
#)


# backend.py
from ldap3 import (Server, Connection, ALL, NTLM, SUBTREE)
import os
import sys
import re
import datetime

#from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
#from django.contrib.auth.backends import ModelBackend #Need to include this as it has been disabled

#Need to have this class inherit from ModelBackend to have permissions inherit to groups.
#class ActiveDirectoryAuthenticationBackend(ModelBackend):
class ActiveDirectoryAuthenticationBackend():

    """
    This authentication backend authenticates against Active directory.
    It updates the user objects according to the settings in the AD and is
    able to map specific groups to give users admin rights.
    """

    def __init__(self):
        """ initialise a debuging if enabled """
        #self.debug = settings.AD_DEBUG
        self.debug = AD_DEBUG
        if len(AD_DEBUG_FILE) > 0 and self.debug:
        #if len(settings.AD_DEBUG_FILE) > 0 and self.debug:
        #    self.debugFile = settings.AD_DEBUG_FILE
            self.debugFile = AD_DEBUG_FILE
            # is the debug file accessible?
            if not os.path.exists(self.debugFile):
                open(self.debugFile,'w').close()
            elif not os.access(self.debugFile, os.W_OK):
                raise IOError("Debug File is not writable")
        else:
            self.debugFile = None

    def authenticate(self,username=None,password=None):
        try:
            if len(password) == 0:
                return None
            #ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,settings.AD_CERT_FILE)
            s = Server(AD_DNS_NAME, port = AD_LDAP_PORT, get_info = None)
            c = Connection(s,
                    auto_bind = True,
                    client_strategy = 'SYNC',
                    user = 'cnvwfs02\\'+ username,
                    password = password,
                    authentication = NTLM,
                    check_names = True,
                    )
        #    print (username, password)
            c.unbind()
            return self.get_or_create_user(username,password)

        except ImportError:
            self.debug_write('import error in authenticate')
        except Exception as err:
            print("ERROR: User auth exception", err)
            return None
        #    self.debug_write('%s: Invalid Credentials' % username)

    def get_or_create_user(self, username, password):
        """ create or update the User object """
        # get user info from AD
        #userInfo = self.get_user_info(username, password)

        # is there already a user?
        try:
            print("Username ok", username)
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            info=sys.exc_info()
            print(info[0],":",info[1])
            entries = self.get_user_info(username, password)
            #print ("INFO:entryes", entries)
            mail = str(entries['mail']).lower()
            sn = str(entries['sn'])
            givenName = str(entries['givenName'])
            user = User(username=username,email=mail, first_name=sn, last_name=givenName)
#            self.debug_write('create new user %s' % username)
            user.is_staff = True
            user.is_superuser = False
            user.set_password('ldap a authenticated')
            user.save()

        return user
            #if userInfo is not None:
            #    user = User(username=username, password=password)
            #    self.debug_write('create new user %s' % username)
            #    user.save() #Creates initial user so groups can be manipulated
            #else:
            #    return None
    def get_user_info(self, username,password):
        adFltr = "(&(sAMAccountName=" + username  + "))"
        if (username and password):
            s = Server(AD_DNS_NAME, port = AD_LDAP_PORT, get_info = None)
            c = Connection(s,
                    auto_bind = True,
                    client_strategy = 'SYNC',
                    user = 'cnvwfs02\\'+ username,
                    password = password,
                    authentication = NTLM,
                    check_names = True,
                    )
            c.search(search_base=AD_SEARCH_DN,
                    search_filter=adFltr,
                    search_scope=SUBTREE,
                    attributes=AD_SEARCH_FIELDS,
                    size_limit=0,
                    time_limit=30
                    )
            return c.entries[0]
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


if __name__ == '__main__':

    auth = ActiveDirectoryAuthenticationBackend()
    print(auth.authenticate('testuser','example here'))
