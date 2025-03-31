from django.core.management.base import BaseCommand
from API.models import Hospitals
from django.db.models import Q

class Command(BaseCommand):
    help = 'Load hospitals from a text file'

    def handle(self, *args, **options):
        # insurance = 'ایران'
        # Hospitals.objects.filter(pk__lte=30).update(insurance=insurance)
        keyword = 'بيمارستان'
        
        hospitals = Hospitals.objects.filter(~Q(name__icontains=keyword))
        for hospital in hospitals:
            hospital.name =f"{keyword} {hospital.name}"
            hospital.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated: {hospital.name}'))

        
