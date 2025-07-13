from rest_framework import serializers
from .models import Event, EventTime, Zone

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class EventTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTime
        fields = '__all__'

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'

class EventListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk')
    title = serializers.CharField(source='artist')
    location = serializers.CharField()
    date = serializers.SerializerMethodField()
    thumbnail = serializers.CharField(source='image_url')
    price = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'location', 'date', 'thumbnail', 'price', 'status', 'tag'
        ]

    def get_date(self, obj):
        event_time = EventTime.objects.filter(event=obj).order_by('event_date').first()
        return event_time.event_date.isoformat() if event_time else None

    def get_price(self, obj):
        zones = Zone.objects.filter(event_time__event=obj)
        return zones.order_by('price').first().price if zones.exists() else 0

    def get_status(self, obj):
        return "예약가능"

    def get_tag(self, obj):
        return "인기" 