from django.core.management.base import BaseCommand
from API.models import Hospitals
from django.db.models import Q

class Command(BaseCommand):
    help = 'Load hospitals from a text file'

    def handle(self, *args, **options):
        # insurance = 'ایران'
        # Hospitals.objects.filter(pk__lte=30).update(insurance=insurance)
        keyword = 'اصفحان'
        insurance_name = ['البرز' , 'ایران' , 'آسیا' , 'کوثر' , 'نیروهای مسلح']
        city = ['مشهد' , 'شیراز' , 'تهران' , 'کرج' ,'اصفهان']
        for i in insurance_name:
            for j in city:
                
                hospitals = Hospitals.objects.filter(insurance = i,city = j)
                if not hospitals.exists:
                    self.stdout.write(self.style.SUCCESS(f'this one does not exists: insuracne {i} , city {j}'))
        # for hospital in hospitals:
            
        #     self.stdout.write(self.style.SUCCESS(f'Successfully updated: {hospital.city}'))