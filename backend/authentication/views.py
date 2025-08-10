from django.shortcuts import render
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm



def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            login(request, form.save())
            return redirect('cities_list')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register.html', {'form': form})
    

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            if "next" in request.POST:
                return redirect(request.POST.get("next"))
            else:
                return redirect("cities:weather_of_detected_city")

    else:
        form = AuthenticationForm()
    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect('cities:weather_of_detected_city')

