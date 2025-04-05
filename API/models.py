from django.db import models
from django.db.models import Model


# Create your models here.
class Hospitals(models.Model):
    name = models.CharField(max_length=100)
    insurance = models.CharField(max_length=256 , null= True)
    city = models.CharField(max_length=256 , default= None)
    phone = models.CharField(max_length=256, blank= True , null= True)
    services = models.TextField(null= True , blank= True)
    address = models.TextField(null= True , blank=True)