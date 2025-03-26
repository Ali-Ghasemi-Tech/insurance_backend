from rest_framework import viewsets
from .models import Hospitals
from .serializer import ItemSerializer
from rest_framework import permissions

class HospitalViews(viewsets.ModelViewSet):
  permission_classes = [permissions.AllowAny]
  queryset = Hospitals.objects.all()
  serializer_class = ItemSerializer