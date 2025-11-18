from django.shortcuts import render ,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .EmailBackEnd import EmailBackEnd
# Create your views here.
def Login(request):
    return render(request,'login.html')


def doLogin(request):
    if request.method == "POST":
        email = request.POST.get('email')
        
        # Check if email is present in the request POST data
        if email is not None:
            email_lower = email.lower()
            user = EmailBackEnd.authenticate(
                request,
                username=email_lower,
                password=request.POST.get('password')
            )
            
            if user is not None:
                login(request, user)
                user_type = user.user_type
                
                # Redirect based on user type
                if user_type == '1':
                    return redirect('AdminHome')
                elif user_type == '2':
                    return redirect('#1')
                else:
                    return redirect('#7')
            else:
                messages.error(request, ' Email or Password is invalid! ')
                return redirect('Login')
        else:
            messages.error(request, ' Email is required! ')
            return redirect('Login')
    else:
        messages.error(request, ' Email or Password is invalid! ')
        return redirect('Login')
    

def doLogout(request):
    logout(request)
    return redirect('Login')


