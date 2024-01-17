from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import time

def epoch_conv(epoch):
    epoch = epoch / 1000.0
    str_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime(epoch))
    return str_time

@csrf_exempt  # Use this decorator if you want to disable CSRF protection for this view (useful for testing purposes)
def index(request):
   
    email = ""
    password = ""
    
    x = True
    while x is True:
        get_response_data = get_data(email, password)
        if len(get_response_data.get('availableShifts')) >=1: print("stop"); break
        time.sleep(0.5)
        print(get_response_data)
    # print(get_response_data.get('availableShifts'))
    

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