from django.shortcuts import render


from django.shortcuts import render,render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
#from groups.models import Groups,Hosts

#from accounts.models import UserProfiles, Privileges
from accounts.models import UserPrivileges

# Create your views here.

def login_view(request):
    msg = []
    if request.POST:
        if len(request.POST.get('next')) > 0:
            _next = request.POST.get('next')
        else:
            _next = "/autocd/"
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return HttpResponseRedirect(_next)
            else:
                msg.append("Disabled account")
        else:
            msg.append("Password error")
    return render(request, 'login.html', {'errors': msg})

@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/accounts/login')
