from rest_framework import serializers
from .models import Ticket

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'


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


