import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Hospitals
import logging

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
            hospitals = Hospitals.objects.filter(insurance=insurance_name.trim())
            if not hospitals.exists():
                return Response(
                    {'error': 'No hospitals found for this insurance'},
                    status=status.HTTP_404_NOT_FOUND
                )

            locations = []
            
            for hospital in hospitals:
                try:
                    response = requests.get(
                        'https://api.neshan.org/v1/search',
                        headers={'Api-Key': settings.NESHAN_API_KEY},
                        params={
                            'term': hospital.name,
                            'lat': lat,
                            'lng': lng
                        }
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    if data.get('items') and len(data['items']) > 0:
                        locations.append(data['items'][0])
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Neshan API error for {hospital.name}: {str(e)}")
                    continue

            return Response({'locations': locations})

        except Hospitals.DoesNotExist:
            return Response(
                {'error': 'Insurance not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
  
