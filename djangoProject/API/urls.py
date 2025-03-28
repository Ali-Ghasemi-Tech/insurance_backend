from django.urls import path , include
from .views import HospitalLocationsView, TaskStatusView
from rest_framework import routers


urlpatterns = [
    path('' , HospitalLocationsView.as_view() , name='hospital_api'),
    path('task-status/<int:task_id>/' , TaskStatusView.as_view() , name ='task_status')
]