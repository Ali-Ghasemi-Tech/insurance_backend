from django.urls import path , include
from .views import HospitalLocationsView
from rest_framework import routers


urlpatterns = [
    path('' , HospitalLocationsView.as_view() , name='hospital_api'),
]