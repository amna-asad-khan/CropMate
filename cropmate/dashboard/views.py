from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, SignupForm
from .models import CropRecommendation

import json
import requests
import pickle
import os
import numpy as np
from datetime import datetime

# Load ML Model once at app start
CROP_MODEL = None
try:
    model_path = os.path.join(os.path.dirname(__file__), 'Model', 'RF.pkl')
    with open(model_path, 'rb') as f:
        CROP_MODEL = pickle.load(f)
except Exception as e:
    print(f"Warning: Failed to load ML model: {e}")

# ============================================================================
# CITY DATA
# ============================================================================
CITIES = {
    'Karachi': (24.8607, 67.0011), 'Lahore': (31.5204, 74.3587),
    'Islamabad': (33.6844, 73.0479), 'Rawalpindi': (33.5651, 73.0169),
    'Faisalabad': (31.4504, 73.1350), 'Multan': (30.1575, 71.5249),
    'Peshawar': (34.0151, 71.5249), 'Quetta': (30.1798, 66.9750),
}

# ============================================================================
# AUTHENTICATION
# ============================================================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=form.cleaned_data['email'])
                user = authenticate(request, username=user.username, password=form.cleaned_data['password'])
                if user:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('dashboard:dashboard')
            except User.DoesNotExist:
                pass
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'dashboard/login.html', {'form': form})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Account created! Please log in.')
            return redirect('root')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()
    
    return render(request, 'dashboard/signup.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Logged out successfully, {username}.')
    return redirect('root')


# ============================================================================
# DASHBOARD
# ============================================================================
@login_required
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')


@login_required
def sensors_view(request):
    return render(request, 'dashboard/sensors.html')


@login_required
def settings_view(request):
    return render(request, 'dashboard/settings.html')


# ============================================================================
# WEATHER
# ============================================================================
@login_required
def weather_view(request):
    city = request.GET.get('city', 'Lahore')
    
    # Check if city exists
    if city not in CITIES:
        return render(request, 'dashboard/weather.html', {
            'error_message': f"City '{city}' not found.",
            'popular_cities': list(CITIES.keys()),
            'selected_city': city
        })
    
    # Get weather data
    try:
        lat, lon = CITIES[city]
        url = f"Your API URL with lat={lat} and lon={lon}"
        
        response = requests.get(url, timeout=5)
        data = response.json()
        
        # Current weather
        current = data['current']
        daily = data['daily']
        
        weather_data = {
            'city': city,
            'temp': round(current['temperature_2m'], 1),
            'feels_like': round(current['apparent_temperature'], 1),
            'humidity': current['relative_humidity_2m'],
            'wind_speed': round(current['wind_speed_10m'], 1),
            'pressure': round(current['pressure_msl'], 0),
            'clouds': current['cloud_cover'],
            'rain_1h': round(current['precipitation'], 1),
            'condition': get_condition(current['weather_code']),
            'icon': get_icon(current['weather_code']),
        }
        
        # 7-day forecast
        forecast_data = []
        for i in range(7):
            forecast_data.append({
                'date': daily['time'][i],
                'day_name': datetime.strptime(daily['time'][i], '%Y-%m-%d').strftime('%A'),
                'temp_max': round(daily['temperature_2m_max'][i], 1),
                'temp_min': round(daily['temperature_2m_min'][i], 1),
                'condition': get_condition(daily['weather_code'][i]),
                'icon': get_icon(daily['weather_code'][i]),
                'rain': round(daily['precipitation_sum'][i], 1),
            })
        
        context = {
            'weather_data': weather_data,
            'forecast_data': forecast_data,
            'popular_cities': list(CITIES.keys()),
            'selected_city': city,
        }
        
    except Exception as e:
        context = {
            'error_message': 'Unable to fetch weather data.',
            'popular_cities': list(CITIES.keys()),
            'selected_city': city
        }
    
    return render(request, 'dashboard/weather.html', context)


def get_condition(code):
    """Convert weather code to readable condition"""
    conditions = {
        0: 'Clear', 1: 'Clear', 2: 'Cloudy', 3: 'Overcast',
        45: 'Foggy', 51: 'Drizzle', 61: 'Rain', 71: 'Snow',
        80: 'Rain Showers', 95: 'Thunderstorm'
    }
    return conditions.get(code, 'Clear')


def get_icon(code):
    """Convert weather code to icon"""
    icons = {
        0: '01d', 1: '02d', 2: '03d', 3: '04d',
        45: '50d', 51: '09d', 61: '10d', 71: '13d',
        80: '09d', 95: '11d'
    }
    return icons.get(code, '01d')


# ============================================================================
# AI AGRONOMIST
# ============================================================================
@login_required
def agronomist_view(request):
    return render(request, 'dashboard/agronomist.html')


@login_required
@require_http_methods(["POST"])
def ask_agronomist(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({'success': False, 'error': 'No message provided'})
        
        # Call Groq API directly using requests
        api_key = "API here"
        url = "Your Groq API URL"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful farming expert. Give short, practical advice about crops, soil, pests, and farming. Keep answers under 3 sentences. And for irrelevent questions, other then farm just say I'm an agriculture expert and can't answer that."},
                {"role": "user", "content": message}
            ],
            "model": "llama-3.1-8b-instant",
            "temperature": 0.8,
            "max_tokens": 150
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        answer = result['choices'][0]['message']['content']
        return JsonResponse({'success': True, 'response': answer})
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Unable to get AI response. Please try again.'})


# ============================================================================
# RECOMMENDATIONS
# ============================================================================
@login_required
def recommendations_view(request):
    prediction_result = None
    input_data = {}
    
    if request.method == 'POST':
        try:
            # Extract and validate inputs
            fields = ['nitrogen', 'phosphorus', 'potassium', 'temperature', 'humidity', 'ph', 'rainfall']
            data = {f: float(request.POST.get(f, 0)) for f in fields}
            input_data = data

            if CROP_MODEL:
                prediction_result = CROP_MODEL.predict(np.array([list(data.values())]))[0]
                
                # Save to history
                CropRecommendation.objects.create(
                    user=request.user,
                    recommended_crop=prediction_result,
                    **data
                )
            else:
                messages.error(request, "Prediction service is temporarily unavailable.")
            
        except Exception as e:
            messages.error(request, f"Error calculating recommendation: {str(e)}")

    context = {
        'prediction_result': prediction_result,
        'input_data': input_data,
        'recent_recommendations': CropRecommendation.objects.filter(user=request.user)[:5]
    }
    return render(request, 'dashboard/recommendations.html', context)


# ============================================================================
# SETTINGS
# ============================================================================
@login_required
def update_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        user = request.user
        
        # Check if username/email already exists
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, 'Username already taken.')
            return redirect('dashboard:settings')
        
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Email already in use.')
            return redirect('dashboard:settings')
        
        # Update
        user.username = username
        user.email = email
        user.save()
        messages.success(request, 'Profile updated!')
    
    return redirect('dashboard:settings')


@login_required
def change_password(request):
    if request.method == 'POST':
        password1 = request.POST.get('new_password1')
        password2 = request.POST.get('new_password2')
        
        # Validate
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('dashboard:settings')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return redirect('dashboard:settings')
        
        # Update password
        user = request.user
        user.set_password(password1)
        user.save()
        
        # Keep user logged in
        user = authenticate(username=user.username, password=password1)
        if user:
            login(request, user)
        
        messages.success(request, 'Password changed!')
    
    return redirect('dashboard:settings')
