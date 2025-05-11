from django.core.management.base import BaseCommand
from API.models import Hospitals
from django.db.models import Q

class Command(BaseCommand):
    help = 'Load hospitals from a text file'

    def handle(self, *args, **options):
        keyword = 'شبانه'
        hospitals = Hospitals.objects.filter(Q(name__icontains = keyword))
        print(f"{len(hospitals)} hospitals to update")
        for hospital in hospitals:
            hospital.medical_class = "مرکز درمانی شبانه روزی"
            hospital.save()
            self.stdout.write(self.style.SUCCESS(f"updated hospital class of {hospital.id} to {hospital.medical_class}"))