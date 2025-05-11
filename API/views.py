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
def get_hospitals(insurance_name , city = "تهران" , medical_class = "بیمارستان"):
    logger.info(
        f"Request received - Insurance: '{insurance_name}', City: '{city}' , Class: '{medical_class}'"
    )
    cache_key = f"hospitals_{insurance_name}_{city}_{medical_class}"
    result = cache.get(cache_key)
    if result is None:
        logger.info(
            f"Cache MISS for Insurance: '{insurance_name}', City: '{city}' , Class: '{medical_class}'. Fetching from DB."
        )
        hospitals = Hospitals.objects.filter(insurance=insurance_name , city = city , medical_class = medical_class)
        if hospitals.exists:
            cache.set(cache_key, list(hospitals), 86400)  
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
        selected_city = request.query_params.get('city')
        selected_class = request.query_params.get('medical_class')

        if not all([insurance_name, lat, lng]):
            return Response(
                {'error': 'Missing required parameters: insurance_name, lat, lng , city'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cache_key = f"hospitals_{insurance_name}_{lat}_{lng}_{selected_class}"
        cached_response = await sync_to_async(cache.get)(cache_key)
        if cached_response is not None:
            logger.info(f"Returning cached response for {cache_key}")
            return Response(cached_response)


        try:
            province = 'تهران'
            city = 'تهران'
            
            if selected_city != 'مکان فعلی من':
                city = selected_city
                province = selected_city
            else:
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
                    return Response({'error': 'could not find your current location'} , status= status.HTTP_404_NOT_FOUND)
                
            hospital_list = await get_hospitals(insurance_name = insurance_name , city= city or province , medical_class=selected_class )

            if not hospital_list:
                return Response({'error': f'هیچ {selected_class.strip()} برای بیمه {insurance_name.strip()} در شهر {city.strip()} یافت نشد.'}  , status=status.HTTP_404_NOT_FOUND)
            
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
                            request = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24filter=province eq {province}&lat={lat}&lon={lng}'
                            
                            if city:
                                request = f'https://map.ir/search/v2/autocomplete/?text={hospital.name}&%24filter=city eq {city}&lat={lat}&lon={lng}'
                                
                            response = await client.get(request,
                                headers={'x-api-key': settings.MAP_IR_API_KEY},
                            )
                            response.raise_for_status()
                            data = response.json()
                            if data.get('value'):
                                for item in data['value']:
                                    if selected_class in item['title']:
                                        return item
                            return None
                        except Exception as e:
                            logger.error(f"map.ir api failed to fetch data: {str(e)}")
                            failed_hospitals.append(hospital.name)  # Track failed hospitals
                            return Response({'error': 'سرور برای پیدا کردن اطلاعات مورد نظر شکست خورد.'} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
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
                searched_hospitals =[]
                for hospital in hospital_list:
                    
                    searched_hospitals.append(hospital.name) 
                
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
                'searched hospitals' : searched_hospitals
            }
            await sync_to_async(cache.set)(cache_key, response_data, 3600)

            return Response(response_data)   

        except Hospitals.DoesNotExist:
             return Response({'error': f'هیچ {selected_class.strip()} برای بیمه {insurance_name.strip()} در شهر {city.strip()} یافت نشد.'} , status=status.HTTP_404_NOT_FOUND)
  

