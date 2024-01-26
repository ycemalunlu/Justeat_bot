from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.db import IntegrityError
from .models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import time

def get_credentials():
    with open('credentials.txt', 'r') as file:
        # Read lines from the file
        lines = file.readlines()

    email = lines[0].strip()
    password = lines[1].strip()

    return [email, password]
    
def epoch_conv(epoch):
    epoch = epoch / 1000.0
    str_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(epoch))
    return str_time

@csrf_exempt  # Use this decorator if you want to disable CSRF protection for this view (useful for testing purposes)
def index(request):
   
    email = get_credentials()[0]
    password = get_credentials()[1]
    
    # x = True
    # while x is True:
    #     get_response_data = get_data(email, password)
    #     if len(get_response_data.get('availableShifts')) >=1: print("stop"); break
    #     time.sleep(0.5)
    #     print(get_response_data)
    # print(get_response_data.get('availableShifts'))
    
    get_response_data = get_data(email, password)
    availableShifts = [(epoch_conv(availableShift["shiftTime"]["start"]), epoch_conv(availableShift["shiftTime"]["end"])) for availableShift in get_response_data.get('availableShifts')]
    if len(availableShifts) == 0: availableShifts = "No available shifts found"
    scheduledShifts = [(epoch_conv(scheduledShift["shiftTime"]["start"]), epoch_conv(scheduledShift["shiftTime"]["end"]))  for scheduledShift in get_response_data.get('scheduledShifts')]
  
    test = get_response_data
    
    # return JsonResponse({"get_response_data": get_response_data})
    return render(request, "index.html", { 
        "availableShifts": availableShifts,
        "scheduledShifts": scheduledShifts,
        "test": test
    })
    
        
    
def get_data(email, password):
    url = "https://api-courier-produk.skipthedishes.com/v4/couriers/two-fa-login"
    headers = {
        "accept": "application/json",
        "app-token": "377f3398-38b8-42e7-873b-378023ca3cab",
        "content-type": "text/plain;charset=UTF-8",
    }
    data = {
        "email": email,
        "password": password
    }
    
    # Convert data to JSON string
    body = json.dumps(data)

    try:
        response = requests.post(url, headers=headers, data=body)
        response_data = response.json()
        
        # Extract relevant data from the response
        user_id = response_data.get('id')
        user_token = response_data.get('token')

        # Make the GET request to the new URL
        get_url = f"https://api-courier-produk.skipthedishes.com/v2/couriers/{user_id}/shifts/scheduled"
        params = {
            'includeAvailable': 'true',
            'timezone': 'Europe/London',
            'hasCourierRefreshedOpenShifts': 'true',
        }
        get_headers = {
            'app-token': '377f3398-38b8-42e7-873b-378023ca3cab',
            'user-token': user_token,
        }

        get_response = requests.get(get_url, headers=get_headers, params=params)
        get_response_data = get_response.json()
        
    except requests.RequestException as e:
        get_response_data = {"error": str(e)}

    return get_response_data



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return redirect(reverse("index"))
        else:
            return render(request, "login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return redirect(reverse("index"))
    else:
        return render(request, "register.html")



