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
    title = serializers.CharField(source='name')           # 타이틀은 행사명!
    artist = serializers.CharField()                       # 출연진 정보
    location = serializers.CharField()
    date = serializers.SerializerMethodField()
    thumbnail = serializers.CharField(source='image_url')
    price = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'artist', 'location', 'date', 'thumbnail', 'price', 'status', 'tag'
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

class EventListResponseSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    limit = serializers.IntegerField()
    totalCount = serializers.IntegerField()
    events = EventListSerializer(many=True)
    message = serializers.CharField(required=False)


class EventScheduleSerializer(serializers.Serializer):
    date = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    
class EventDetailResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    artist = serializers.CharField()
    date = serializers.CharField(allow_null=True)
    location = serializers.CharField()
    price = serializers.CharField()
    thumbnail = serializers.CharField()
    tag = serializers.CharField()
    description = serializers.CharField()
    schedules = serializers.ListField(child=serializers.DictField())
    max_reserve = serializers.IntegerField()

class EventSeatsDataSerializer(serializers.Serializer):
    schedules = EventScheduleSerializer(many=True)


class SeatInfoSerializer(serializers.Serializer):
    seat_id = serializers.IntegerField()
    seat_number = serializers.CharField()
    price = serializers.IntegerField()
    seat_status = serializers.CharField()
    event_time_id = serializers.IntegerField()
    available_count = serializers.IntegerField()

class EventSeatsResponseSerializer(serializers.Serializer):
    statusCode = serializers.IntegerField()
    message = serializers.CharField()

    data = serializers.ListField(child=EventSeatsDataSerializer())

    data = SeatInfoSerializer(many=True, allow_null=True)


class BuyTicketsRequestSerializer(serializers.Serializer):
    seat_id = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="선택한 좌석 ID 리스트"
    )
    event_time_id = serializers.IntegerField(help_text="예매하려는 공연 시간 ID")

class BuyTicketsResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    purchase_id = serializers.IntegerField()
    ticket_ids = serializers.ListField(child=serializers.IntegerField())


class PayTicketResponseSerializer(serializers.Serializer):
    message = serializers.CharField() 


class PayTicketRequestSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.CharField()

class PayTicketResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
