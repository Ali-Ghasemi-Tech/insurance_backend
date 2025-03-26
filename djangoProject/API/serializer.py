from rest_framework import serializers

from .models import Hospitals


class ItemSerializer(serializers.ModelSerializer):
    insurance_name = serializers.CharField(max_length = 200)
    
    class Meta:

        model = Hospitals

        fields = ('insurance' , 'name')
        
class NeshanSerializer(serializers.Serializer):
    hospital_name = serializers.CharField()
    lat = serializers.DecimalField()
    lan = serializers.DecimalField()
    