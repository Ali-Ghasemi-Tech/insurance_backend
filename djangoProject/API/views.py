import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from concurrent.futures import ThreadPoolExecutor, as_completed

from rest_framework import status
from django.conf import settings
from .models import Hospitals
import logging
from django.http import HttpResponse
from time import sleep





logger = logging.getLogger(__name__)

class HospitalLocationsView(APIView):
    """
    Class-based view to handle insurance-based hospital location searches
    """
    
    def get(self, request, *args, **kwargs):
        insurance_name = request.query_params.get('insurance_name')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not all([insurance_name, lat, lng]):
            return Response(
                {'error': 'Missing required parameters: insurance_name, lat, lng'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            hospitals = Hospitals.objects.filter(insurance=insurance_name)
            if not hospitals.exists():
                return Response(
                    {'error': 'No hospitals found for this insurance'},
                    status=status.HTTP_404_NOT_FOUND
                )

            hospitals_list = list(hospitals)
            locations = []
            failed_hospitals = []
            city = 'تهران'
            try:
                    response = requests.get(
                        "https://map.ir/reverse/fast-reverse",
                        headers={'x-api-key': settings.MAP_IR_API_KEY},
                        params={'lat':lat , 'lon':lng}
                    )
                    response.raise_for_status()
                    data = response.json()
                    if data:
                        city = data['city']
            
            except Exception as e:
                logger.error(f"Neshan API failed for city selection: {str(e)}")
                
            def fetch_hospital_location(hospital):
                # try:
                #     response = requests.get(
                #         'https://api.neshan.org/v1/search',
                #         headers={'Api-Key': settings.NESHAN_API_KEY},
                #         params={'term': hospital.name, 'lat': lat, 'lng': lng},
                #         timeout=10  # Add timeout
                #     )
                #     response.raise_for_status()
                #     data = response.json()
                #     if data.get('items'):
                #         for item in data['items']:
                #             if item['type'] == 'hospital':
                #                 return item
                #     return None
                # except Exception as e:
                #     logger.error(f"Neshan API failed for {hospital.name}: {str(e)}")
                #     failed_hospitals.append(hospital.name)  # Track failed hospitals
                #     return None
                
                try:
                    response = requests.get(
                        f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24select=nearby&%24filter=city eq {city}&lat={lat}&lon={lng}',
                        headers={'x-api-key': settings.MAP_IR_API_KEY},
                        verify=False
                    )
                    response.raise_for_status()
                    data = response.json()
                    if data.get('value'):
                        for item in data['value']:
                            if item['fclass'] in ['hospital' , 'hospital_section']:
                                return item
                    return None
                except Exception as e:
                    logger.error(f"map.ir api failed to fetch data: {str(e)}")
                    failed_hospitals.append(hospital.name)  # Track failed hospitals
                    return None
                
            with ThreadPoolExecutor(max_workers=30) as executor:
                # Submit all hospitals to the executor
                futures = {executor.submit(fetch_hospital_location, hospital): hospital.name 
                           for hospital in hospitals_list}
                
                # Process results as they complete
                for i, future in enumerate(as_completed(futures)):
                    hospital_name = futures[future]
                    try:
                        result = future.result()
                        if result:
                            locations.append(result)
                        # Log progress and remaining hospitals
                        remaining = len(hospitals_list) - (i + 1)
                        logger.info(f"Processed {hospital_name}. Remaining: {remaining}")
                    except Exception as e:
                        logger.error(f"Error processing {hospital_name}: {str(e)}")

            # Include failed hospitals in the response (optional)
            response_data = {
                'locations': locations,
                'failed_hospitals': failed_hospitals,
            }
            return Response(response_data)   

        except Hospitals.DoesNotExist:
            return Response(
                {'error': 'Insurance not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
  

