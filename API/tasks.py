# # hospitals/tasks.py
# from celery import shared_task
# import requests
# from django.conf import settings
# import logging

# logger = logging.getLogger(__name__)

# @shared_task(bind=True, max_retries=3)
# def fetch_hospital_location(self, hospital_name, lat, lng):
#     try:
#         response = requests.get(
#             'https://api.neshan.org/v1/search',
#             headers={'Api-Key': settings.NESHAN_API_KEY},
#             params={'term': hospital_name, 'lat': lat, 'lng': lng},
#             timeout=10
#         )
#         response.raise_for_status()
#         data = response.json()
#         return data.get('items', [])[0] if data.get('items') else None
#     except Exception as e:
#         logger.error(f"Failed for {hospital_name}: {str(e)}")
#         self.retry(countdown=2 ** self.request.retries)