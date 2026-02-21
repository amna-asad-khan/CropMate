from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('weather/', views.weather_view, name='weather'),
    path('sensors/', views.sensors_view, name='sensors'),
    path('agronomist/', views.agronomist_view, name='agronomist'),
    path('ask-agronomist/', views.ask_agronomist, name='ask_agronomist'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/update-profile/', views.update_profile, name='update_profile'),
    path('settings/change-password/', views.change_password, name='change_password'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]





