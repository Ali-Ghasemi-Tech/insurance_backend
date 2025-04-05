import requests
import httpx
import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.cache import caches

from rest_framework import status
from django.conf import settings
from .models import Hospitals
import logging
from django.http import HttpResponse
from time import sleep
from adrf import views
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

cache = caches['default']
@sync_to_async
def get_hospitals(insurance_name , city):
    logger.info(
        f"Request received - Insurance: '{insurance_name}', City: '{city}'"
    )
    cache_key = f"hospitals_{insurance_name}_{city}"
    result = cache.get(cache_key)
    if result is None:
        logger.info(
            f"Cache MISS for Insurance: '{insurance_name}', City: '{city}'. Fetching from DB."
        )
        hospitals = Hospitals.objects.filter(insurance=insurance_name , city = city)
        cache.set(cache_key, list(hospitals) if hospitals.exists else None, 86400)  
        logger.info(
            f"Fetched {len(result) if result else 0} records from DB for Insurance: '{insurance_name}', City: '{city}'."
        )
        return list(hospitals) if hospitals.exists() else None
    logger.info(
            f"Cache HIT for Insurance: '{insurance_name}', City: '{city}'. Returning cached data."
        )
    return result
    

class HospitalLocationsView(views.APIView):
    """
    Class-based view to handle insurance-based hospital location searches
    """
    
    async def get(self, request, *args, **kwargs):
        sem = asyncio.Semaphore(10)

        insurance_name = request.query_params.get('insurance_name')
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not all([insurance_name, lat, lng]):
            return Response(
                {'error': 'Missing required parameters: insurance_name, lat, lng'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cache_key = f"hospitals_{insurance_name}_{lat}_{lng}"
        cached_response = await sync_to_async(cache.get)(cache_key)
        if cached_response is not None:
            logger.info(f"Returning cached response for {cache_key}")
            return Response(cached_response)


        try:
            province = 'تهران'
            city = 'تهران'
            # get user province and city
            try:
                response = requests.get(
                    "https://map.ir/reverse/fast-reverse",
                    headers={'x-api-key': settings.MAP_IR_API_KEY},
                    params={'lat':lat , 'lon':lng}
                )
                response.raise_for_status()
                province = response.json().get('province')
                city = response.json().get('city')
                if city == '':
                    city = None
                elif province == '':
                    province == None
                
            except Exception as e:
                logger.error(f"Neshan API failed for province selection: {str(e)}")
                
            hospital_list = await get_hospitals(insurance_name = insurance_name , city= city or province)

            if not hospital_list:
                return Response({'error': 'no hospitals found for this insurance'} , status=status.HTTP_404_NOT_FOUND)
            
            locations = []
            failed_hospitals = []
            
            # find hospitals around the user locaion
            async with httpx.AsyncClient(timeout=10.0) as client:
                
                    
                async def fetch_hospital_location(hospital):
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
                    async with sem:
                        try:
                            request = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24select=nearby&%24filter=province eq {province}&lat={lat}&lon={lng}'
                            
                            if city:
                                request = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24select=nearby&%24filter=city eq {city}&lat={lat}&lon={lng}'
                                
                            response = await client.get(request,
                                headers={'x-api-key': settings.MAP_IR_API_KEY},
                            )
                            response.raise_for_status()
                            data = response.json()
                            if data.get('value'):
                                for item in data['value']:
                                    if item['fclass'] in ['hospital' , 'hospital_section'] and not any(word in item['title'] for word in ['دام پزشکی', 'دامپزشکی']):
                                        return item
                            return None
                        except Exception as e:
                            logger.error(f"map.ir api failed to fetch data: {str(e)}")
                            failed_hospitals.append(hospital.name)  # Track failed hospitals
                            return None
                
            # with ThreadPoolExecutor(max_workers=10) as executor:
            #     # Submit all hospitals to the executor
            #     futures = {executor.submit(fetch_hospital_location, hospital): hospital.name 
            #                for hospital in hospitals_list}
                
            #     # Process results as they complete
            #     for i, future in enumerate(as_completed(futures)):
            #         hospital_name = futures[future]
            #         try:
            #             result = future.result()
            #             if result:
            #                 locations.append(result)
            #             # Log progress and remaining hospitals
            #             remaining = len(hospitals_list) - (i + 1)
            #             logger.info(f"Processed {hospital_name}. Remaining: {remaining}")
            #         except Exception as e:
            #             logger.error(f"Error processing {hospital_name}: {str(e)}")
            
                tasks = [fetch_hospital_location(hospital) for hospital in hospital_list]
                total = len(tasks)
                processed = 0
                
                for future in asyncio.as_completed(tasks):
                    result = await future
                    processed += 1
                    
                    remaining = total - processed
                    if result:
                        locations.append(result)
                    # else:
                    #     failed_hospitals.append(hospital_name)
                    # logger.info(f"Processed {hospital_name} - Remaining: {remaining}")

            # Include failed hospitals in the response (optional)
            response_data = {
                'locations': locations,
                'failed_hospitals': failed_hospitals,
            }
            await sync_to_async(cache.set)(cache_key, response_data, 3600)

            return Response(response_data)   

        except Hospitals.DoesNotExist:
            return Response(
                {'error': 'Insurance not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
  

