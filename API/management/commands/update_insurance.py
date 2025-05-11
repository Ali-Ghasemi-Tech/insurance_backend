from django.core.management.base import BaseCommand
from API.models import Hospitals
from django.db.models import Q

class Command(BaseCommand):
    help = 'Load hospitals from a text file'

    def handle(self, *args, **options):
        # insurance = 'ایران'
        # Hospitals.objects.filter(pk__lte=30).update(insurance=insurance)
        keyword =  "درمانگاه بیمارستان"
        # hospital = Hospitals.objects.get(id = 32)
        # hospital.name = "ابان"
        # hospital.save()
        hospitals = Hospitals.objects.filter(Q(name__icontains = keyword) )
        for hospital in hospitals:
            print(hospital.id)
            # if hospital.medical_class in hospital.name:
            #     print('this is working')
            # index = hospital.name.index(keyword) 
            # if len(hospital.name) - 1 != index:
                
            #     if hospital.name[index + 1] == " " and hospital.name[index - 1] == " ":
            #         hospital.name = hospital.name.replace(keyword , "")
            hospital.name = hospital.name.replace(keyword, 'بیمارستان')
            hospital.save()
            print(hospital.name)
            self.stdout.write(self.style.SUCCESS(f'Successfully updated: {hospital.name} , {hospital.medical_class}'))

        
