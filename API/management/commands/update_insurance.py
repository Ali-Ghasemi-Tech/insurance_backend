from django.core.management.base import BaseCommand
from API.models import Hospitals
from django.db.models import Q

class Command(BaseCommand):
    help = 'Load hospitals from a text file'

    def handle(self, *args, **options):
        # insurance = 'ایران'
        # Hospitals.objects.filter(pk__lte=30).update(insurance=insurance)
        keyword = 'دندانپزشك '
        
        hospitals = Hospitals.objects.filter(Q(name__icontains = keyword))
        for hospital in hospitals:
            # if hospital.medical_class in hospital.name:
            #     print('this is working')
            hospital.medical_class = 'دندان پزشکی'
            hospital.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated: {hospital.name} , {hospital.medical_class}'))

        
