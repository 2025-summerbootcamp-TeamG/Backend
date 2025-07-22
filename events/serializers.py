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
    name = serializers.CharField()           # 타이틀은 행사명!
    artist = serializers.CharField()                       # 출연진 정보
    location = serializers.CharField()
    date = serializers.SerializerMethodField()
    thumbnail = serializers.CharField(source='image_url')
    price = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    view_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    genre = serializers.CharField()

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'artist', 'location', 'date', 'thumbnail', 'price', 'status', 'view_count', 'created_at', 'genre'
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
    event_time_id = serializers.IntegerField()
    date = serializers.CharField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    zone_ids = serializers.ListField(child=serializers.IntegerField(), read_only=True)

    def to_representation(self, instance):
        # instance는 EventTime 인스턴스여야 함
        from .models import Zone
        data = {
            'event_time_id': instance.id,
            'date': instance.event_date.isoformat() if hasattr(instance, 'event_date') else '',
            'start_time': instance.start_time.strftime("%H:%M") if hasattr(instance, 'start_time') else '',
            'end_time': instance.end_time.strftime("%H:%M") if hasattr(instance, 'end_time') else '',
            'zone_ids': [zone.id for zone in Zone.objects.filter(event_time=instance)]
        }
        return data

class EventDetailResponseSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    schedules = serializers.SerializerMethodField()
    thumbnail = serializers.CharField(source='image_url')
    max_reserve = serializers.CharField()

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'artist', 'date', 'location', 'price', 'thumbnail',
            'description', 'schedules', 'max_reserve', 'view_count'
        ]

    def get_date(self, obj):
        if not hasattr(obj, 'eventtime_set'):
            return None
        first_time = obj.eventtime_set.order_by('event_date').first()
        return first_time.event_date.isoformat() if first_time else None

    def get_schedules(self, obj):
        if not hasattr(obj, 'eventtime_set'):
            return []
        event_times = obj.eventtime_set.order_by('event_date', 'start_time')
        return EventScheduleSerializer(event_times, many=True).data

    def get_price(self, obj):
        if not hasattr(obj, 'eventtime_set'):
            return "₩0"
        prices = []
        for et in obj.eventtime_set.all():
            prices += [z.price for z in et.zone_set.all()]
        if not prices:
            return "₩0"
        min_price = min(prices)
        max_price = max(prices)
        if min_price == max_price:
            return f"₩{min_price:,}"
        return f"₩{min_price:,} ~ ₩{max_price:,}"

class EventSeatsDataSerializer(serializers.Serializer):
    schedules = EventScheduleSerializer(many=True)


class SeatInfoSerializer(serializers.Serializer):
    seat_id = serializers.IntegerField()
    seat_number = serializers.CharField()
    price = serializers.IntegerField()
    seat_status = serializers.CharField()
    event_time_id = serializers.IntegerField()
    available_count = serializers.IntegerField()
    date = serializers.CharField()

class EventSeatsResponseSerializer(serializers.Serializer):
    statusCode = serializers.IntegerField()
    message = serializers.CharField()
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
