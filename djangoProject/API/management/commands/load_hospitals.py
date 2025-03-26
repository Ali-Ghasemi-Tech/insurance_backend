from django.core.management.base import BaseCommand
from API.models import Hospitals

class Command(BaseCommand):
    help = 'Load hospitals from a text file'

    def handle(self, *args, **options):
        Hospitals.objects.all().delete()
        with open('../hospitals.txt', 'r' , encoding="utf_8") as f:
            for line in f:
                name = line.strip()
                Hospitals.objects.create(name=name)