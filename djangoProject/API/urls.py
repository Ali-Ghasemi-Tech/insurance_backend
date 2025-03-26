from django.urls import path , include
from .views import HospitalViews
from rest_framework import routers

router = routers.DefaultRouter()
router.register('' , HospitalViews)

urlpatterns = [
    path('' , include(router.urls))
]