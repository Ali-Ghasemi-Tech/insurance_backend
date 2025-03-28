import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Hospitals
import logging
import redis
from django.http import HttpResponse
from .tasks import fetch_hospital_location
from celery.result import AsyncResult





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

            task_ids = []
            
            for hospital in hospitals:
                try:
                    task = fetch_hospital_location.delay(hospital.name, lat, lng)
                    task_ids.append(task.id)
                    return Response({'task_ids': task_ids},
                        status=status.HTTP_202_ACCEPTED  # "Accepted" status code
                    )
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Neshan API error for {hospital.name}: {str(e)}")
                    continue

            return Response(
            {'task_ids': task_ids},
            status=status.HTTP_202_ACCEPTED  # "Accepted" status code
        )

        except Hospitals.DoesNotExist:
            return Response(
                {'error': 'Insurance not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
  
class TaskStatusView(APIView):
    def get(self, request, task_id):
        task = AsyncResult(task_id)
        return Response({
            'status': task.status,
            'result': task.result if task.ready() else None,
            'error': str(task.info) if task.failed() else None
        })
