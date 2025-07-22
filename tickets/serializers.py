from rest_framework import serializers
from .models import Ticket
from user.models import User
from user.serializers import UserSignupSerializer
from .models import Purchase
from events.models import Seat, Zone, EventTime, Event
from events.serializers import EventSerializer, EventTimeSerializer, ZoneSerializer

class EventNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'artist', 'location', 'description', 'genre', 'age_rating', 'image_url', 'created_at', 'updated_at']

class EventTimeNestedSerializer(serializers.ModelSerializer):
    event = EventNestedSerializer()
    class Meta:
        model = EventTime
        fields = ['id', 'event_date', 'start_time', 'end_time', 'event']

class ZoneNestedSerializer(serializers.ModelSerializer):
    event_time = EventTimeNestedSerializer()
    class Meta:
        model = Zone
        fields = ['id', 'rank', 'price', 'event_time']

class SeatNestedSerializer(serializers.ModelSerializer):
    zone = ZoneNestedSerializer()
    class Meta:
        model = Seat
        fields = ['id', 'seat_number', 'seat_status', 'zone']

class PurchaseNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['id', 'purchase_status', 'created_at', 'updated_at', 'purchaser', 'phone_number', 'email']

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone']

class TicketSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    seat = SeatNestedSerializer()
    purchase = PurchaseNestedSerializer()
    user = UserSimpleSerializer()

    class Meta:
        model = Ticket
        fields = ['id', 'ticket_status', 'booked_at', 'face_verified', 'verified_at', 'created_at', 'updated_at', 'is_deleted', 'image_url', 'user', 'seat', 'purchase']

    def get_image_url(self, obj):
        try:
            return obj.seat.zone.event_time.event.image_url
        except Exception:
            return None


class FaceRegisterRequestSerializer(serializers.Serializer):
    face_verified = serializers.BooleanField()
    user_id = serializers.IntegerField()

class FaceRegisterResponseDataSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    face_verified = serializers.BooleanField()
    verified_at = serializers.CharField()

class FaceRegisterResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = FaceRegisterResponseDataSerializer(allow_null=True)

class FaceRegisterErrorSerializer(serializers.Serializer):
    message = serializers.CharField()
    data = serializers.CharField(allow_null=True)


class TicketFaceVerifyRequestSerializer(serializers.Serializer):
    face_matches = serializers.IntegerField()
    user_id = serializers.IntegerField()

class TicketFaceVerifySuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    face_verified = serializers.BooleanField()
    verified_at = serializers.DateTimeField()

class TicketFaceVerifyFailResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    face_verified = serializers.BooleanField()


class TicketFaceAuthDataSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    face_verified = serializers.BooleanField()
    verified_at = serializers.CharField(allow_null=True)

class TicketFaceAuthResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = TicketFaceAuthDataSerializer(allow_null=True)


class ShareTicketsRequestSerializer(serializers.Serializer):
    ticket_user_emails = serializers.ListField(
        child=serializers.EmailField(),
        help_text="공유할 유저의 이메일 리스트"
    )

class ShareTicketsSuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

class ShareTicketsErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()
    details = serializers.DictField(required=False)


class AWSFaceRecognitionRequestSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['register', 'verify'])
    user_id = serializers.IntegerField()
    ticket_id = serializers.IntegerField()
    image = serializers.CharField(help_text="Base64 인코딩된 이미지")

class AWSFaceRegisterDataSerializer(serializers.Serializer):
    ticket_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    face_verified = serializers.BooleanField()
    verified_at = serializers.CharField()
    external_image_id = serializers.CharField()

class AWSFaceRegisterResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AWSFaceRegisterDataSerializer(allow_null=True)

class AWSFaceRecognitionSuccessFaceMatchSerializer(serializers.Serializer):
    similarity = serializers.FloatField()
    face_id = serializers.CharField()
    external_image_id = serializers.CharField()

class AWSFaceRecognitionVerifySuccessSerializer(serializers.Serializer):
    message = serializers.CharField()
    similarity = serializers.FloatField()
    face_id = serializers.CharField()
    external_image_id = serializers.CharField()
    face_matches = AWSFaceRecognitionSuccessFaceMatchSerializer(many=True)

class AWSFaceRecognitionVerifyFailSerializer(serializers.Serializer):
    message = serializers.CharField()
    face_matches = AWSFaceRecognitionSuccessFaceMatchSerializer(many=True)

class AWSFaceRecognitionErrorSerializer(serializers.Serializer):
    message = serializers.CharField()
    error = serializers.CharField()


class FaceListDataSerializer(serializers.Serializer):
    FaceId = serializers.CharField()
    ExternalImageId = serializers.CharField()

class FaceListResponseSerializer(serializers.Serializer):
    data = FaceListDataSerializer(many=True)

class FaceListErrorSerializer(serializers.Serializer):
    message = serializers.CharField()
    error = serializers.CharField()


class FaceDeleteRequestSerializer(serializers.Serializer):
    face_id = serializers.CharField()

class FaceDeleteSuccessSerializer(serializers.Serializer):
    message = serializers.CharField()

class FaceDeleteErrorSerializer(serializers.Serializer):
    message = serializers.CharField()
    error = serializers.CharField()


class TicketDetailSerializer(serializers.ModelSerializer):
    event_name = serializers.SerializerMethodField()
    event_date = serializers.SerializerMethodField()
    event_time = serializers.SerializerMethodField()
    event_location = serializers.SerializerMethodField()
    seat_rank = serializers.SerializerMethodField()
    seat_number = serializers.SerializerMethodField()
    reservation_number = serializers.SerializerMethodField()
    ticket_price = serializers.SerializerMethodField()
    reservation_fee = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    verified_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M", source="verified_at", allow_null=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'event_name', 'event_date', 'event_time', 'event_location',
            'seat_rank', 'seat_number', 'reservation_number',
            'ticket_price', 'reservation_fee', 'total_price',
            'face_verified', 'verified_at', 'image_url'
        ]
        extra_kwargs = {'id': {'source': 'ticket_id'}}

    def get_event_name(self, obj):
        return obj.seat.zone.event_time.event.name
    def get_event_date(self, obj):
        return obj.seat.zone.event_time.event_date.strftime('%Y-%m-%d')
    def get_event_time(self, obj):
        return obj.seat.zone.event_time.start_time.strftime('%H:%M')
    def get_event_location(self, obj):
        return obj.seat.zone.event_time.event.location
    def get_seat_rank(self, obj):
        return obj.seat.zone.rank
    def get_seat_number(self, obj):
        return obj.seat.seat_number
    def get_reservation_number(self, obj):
        return f"T{obj.seat.zone.event_time.event_date.strftime('%Y%m%d')}{obj.id:05d}"
    def get_ticket_price(self, obj):
        return obj.seat.zone.price
    def get_reservation_fee(self, obj):
        return 1000  # 정책에 따라 고정값
    def get_total_price(self, obj):
        return obj.seat.zone.price + 1000
    def get_image_url(self, obj):
        try:
            return obj.seat.zone.event_time.event.image_url
        except Exception:
            return None

class TicketListSerializer(serializers.ModelSerializer):
    event_name = serializers.SerializerMethodField()
    event_date = serializers.SerializerMethodField()
    event_start_time = serializers.SerializerMethodField()
    event_location = serializers.SerializerMethodField()
    seat_rank = serializers.SerializerMethodField()
    seat_number = serializers.SerializerMethodField()
    ticket_status = serializers.CharField()

    class Meta:
        model = Ticket
        fields = [
            'id',
            'event_name', 'event_date', 'event_start_time', 'event_location',
            'seat_rank', 'seat_number', 'ticket_status'
        ]

    def get_event_name(self, obj):
        return obj.seat.zone.event_time.event.name
    def get_event_date(self, obj):
        return obj.seat.zone.event_time.event_date.strftime('%Y-%m-%d')
    def get_event_start_time(self, obj):
        return obj.seat.zone.event_time.start_time.strftime('%H:%M')
    def get_event_location(self, obj):
        return obj.seat.zone.event_time.event.location
    def get_seat_rank(self, obj):
        return obj.seat.zone.rank
    def get_seat_number(self, obj):
        return obj.seat.seat_number
