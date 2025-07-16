from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Ticket
from .serializers import TicketSerializer
from django.shortcuts import get_object_or_404
from django.db import connection
from django.db import transaction
from user.models import User  
import boto3
import base64
import io
from PIL import Image
import os
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiTypes, OpenApiExample
from django.http import JsonResponse
import qrcode
from io import BytesIO


class FaceRegisterAPIView(APIView):
    @extend_schema(
        summary="티켓 얼굴 등록 상태 변경",
        description="티켓에 얼굴 등록 여부(face_verified)만 받아 상태를 변경합니다. user_id는 토큰(JWT) 인증에서 추출합니다.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'face_verified': {'type': 'boolean', 'description': '얼굴 등록 여부'},
                },
                'required': ['face_verified']
            }
        },
        parameters=[
            OpenApiParameter(name='ticket_id', description='티켓 ID', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "code": 200,
                            "message": "얼굴 등록 상태가 정상적으로 업데이트 되었습니다",
                            "data": {
                                "ticket_id": 1,
                                "user_id": 2,
                                "face_verified": True,
                                "verified_at": "2024-07-16 12:00:00"
                            }
                        },
                        status_codes=["200"]
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="입력값 오류",
                examples=[
                    OpenApiExample(
                        "BadRequest",
                        value={"message": "face_verified가 필요합니다", "data": None},
                        status_codes=["400"]
                    )
                ]
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="권한 없음",
                examples=[
                    OpenApiExample(
                        "Forbidden",
                        value={"message": "해당 사용자의 티켓 권한 없음", "data": None},
                        status_codes=["403"]
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="티켓 없음",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"message": "티켓 없음", "data": None},
                        status_codes=["404"]
                    )
                ]
            ),
            500: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="서버 오류",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"message": "내부 서버 오류", "result": None},
                        status_codes=["500"]
                    )
                ]
            ),
        }
    )
    def patch(self, request, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return Response(
                {
                    "message": "티켓 없음",
                    "data": None
                },
                status=status.HTTP_404_NOT_FOUND,
                content_type="application/json; charset=UTF-8"
            )

        try:
            face_verified = request.data.get('face_verified')
            if face_verified is None:
                return Response(
                    {
                        "message": "face_verified가 필요합니다",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type="application/json; charset=UTF-8"
                )

            # 티켓의 user_id와 로그인 유저 비교
            if ticket.user_id != request.user.id:
                return Response(
                    {
                        "message": "해당 사용자의 티켓 권한 없음",
                        "data": None
                    },
                    status=status.HTTP_403_FORBIDDEN,
                    content_type="application/json; charset=UTF-8"
                )

            ticket.face_verified = face_verified
            ticket.verified_at = timezone.now()
            ticket.save()

            verified_at_local = timezone.localtime(ticket.verified_at)
            verified_at_str = verified_at_local.strftime('%Y-%m-%d %H:%M:%S')

            return Response(
                {
                    "code": 200,
                    "message": "얼굴 등록 상태가 정상적으로 업데이트 되었습니다",
                    "data": {
                        "ticket_id": ticket.id,
                        "user_id": ticket.user_id,
                        "face_verified": ticket.face_verified,
                        "verified_at": verified_at_str
                    }
                },
                status=status.HTTP_200_OK,
                content_type="application/json; charset=UTF-8"
            )
        except Exception:
            return Response(
                {
                    "message": "내부 서버 오류",
                    "result": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type="application/json; charset=UTF-8"
            )


class TicketFaceVerifyView(APIView):
    @extend_schema(
        summary="티켓 얼굴 인증",
        description="AWS Rekognition 결과(face_matches)로 티켓 얼굴 인증 처리. user_id는 토큰(JWT) 인증에서 추출합니다.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'face_matches': {'type': 'integer', 'description': '얼굴 유사도(%)'},
                },
                'required': ['face_matches']
            }
        },
        parameters=[
            OpenApiParameter(name='pk', description='티켓 PK', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "얼굴 인증 성공", "face_verified": True, "verified_at": "2024-07-16 12:00:00"},
                        status_codes=["200"]
                    ),
                    OpenApiExample(
                        "Fail",
                        value={"message": "얼굴 인증 실패", "face_verified": False},
                        status_codes=["200"]
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="입력값 오류",
                examples=[
                    OpenApiExample(
                        "BadRequest",
                        value={"error": "face_matches가 필요합니다."},
                        status_codes=["400"]
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="티켓 없음",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"error": "티켓을 찾을 수 없습니다."},
                        status_codes=["404"]
                    )
                ]
            ),
        }
    )
    def patch(self, request, pk):
        face_matches = request.data.get('face_matches')  # 예: 95
        if face_matches is None:
            return Response({'error': 'face_matches가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({'error': '티켓을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 티켓의 user_id와 로그인 유저 비교
        if ticket.user_id != request.user.id:
            return Response({'error': '해당 사용자의 티켓 권한 없음.'}, status=status.HTTP_403_FORBIDDEN)

        if face_matches >= 95:
            ticket.face_verified = True
            ticket.verified_at = timezone.now()
            ticket.save()
            return Response({
                'message': '얼굴 인증 성공', 
                'face_verified': True, 
                'verified_at': ticket.verified_at
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': '얼굴 인증 실패', 
                'face_verified': False
            }, status=status.HTTP_200_OK)


class TicketFaceAuthAPIView(APIView):
    @extend_schema(
        summary="티켓 얼굴 등록 상태 조회",
        description="티켓의 얼굴 등록 상태, 인증 여부, 인증 시각 등을 조회합니다.",
        parameters=[
            OpenApiParameter(name='ticket_id', description='티켓 ID', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "code": 200,
                            "message": "얼굴 등록 상태 열람 성공",
                            "data": {
                                "ticket_id": 1,
                                "user_id": 2,
                                "face_verified": True,
                                "verified_at": "2024-07-16 12:00:00"
                            }
                        },
                        status_codes=["200"]
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="티켓 없음",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"code": 404, "message": "티켓 없음.", "data": None},
                        status_codes=["404"]
                    )
                ]
            ),
            500: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="서버 오류",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"message": "내부 서버 오류", "result": None},
                        status_codes=["500"]
                    )
                ]
            ),
        }
    )
    def get(self, request, ticket_id):
        try:
            try:
                ticket = Ticket.objects.get(id=ticket_id)
            except Ticket.DoesNotExist:
                return Response(
                    {
                        "code": 404,
                        "message": "티켓 없음.",
                        "data": None
                    },
                    status=status.HTTP_404_NOT_FOUND,
                    content_type="application/json; charset=UTF-8"
                )

            # 서울 시간대로 변환 (pytz 없이)
            verified_at = ticket.verified_at
            if verified_at:
                verified_at_local = timezone.localtime(verified_at)
                verified_at_str = verified_at_local.strftime('%Y-%m-%d %H:%M:%S')
            else:
                verified_at_str = None

            return Response(
                {
                    "code": 200,
                    "message": "얼굴 등록 상태 열람 성공",
                    "data": {
                        "ticket_id": ticket.id,
                        "user_id": ticket.user_id,
                        "face_verified": ticket.face_verified,
                        "verified_at": verified_at_str
                    }
                },
                status=status.HTTP_200_OK,
                content_type="application/json; charset=UTF-8"
            )
        except Exception:
            return Response(
                {
                    "message": "내부 서버 오류",
                    "result": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content_type="application/json; charset=UTF-8"
            )

            # 나의 티켓 전체 조회
class MyTicketListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="나의 티켓 목록 조회",
        description="JWT 인증된 유저의 모든 티켓 목록을 반환합니다.",
        responses=TicketSerializer(many=True)
    )
    def get(self, request):
        user_id = request.user.id
        tickets = Ticket.objects.filter(user_id=user_id)
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)

# 티켓 상세정보 조회
class TicketDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="티켓 상세정보 조회",
        description="JWT 인증된 유저의 특정 티켓 상세정보를 반환합니다.",
        parameters=[
            OpenApiParameter(name='ticket_id', description='티켓 ID', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"id": 1, "user_id": 2, "ticket_status": "booked", "seat": 10, "purchase": 5, "face_verified": True, "verified_at": "2024-07-16 12:00:00", "created_at": "2024-07-16T12:00:00Z", "updated_at": "2024-07-16T12:00:00Z", "is_deleted": False},
                        status_codes=["200"]
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="티켓 없음",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"detail": "Not found."},
                        status_codes=["404"]
                    )
                ]
            ),
        }
    )
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id, user_id=request.user.id)
        serializer = TicketSerializer(ticket)
        return Response(serializer.data)

# 티켓 취소
class TicketCancelView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="티켓 취소",
        description="JWT 인증된 유저의 특정 티켓을 취소 처리합니다.",
        parameters=[
            OpenApiParameter(name='ticket_id', description='티켓 ID', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"id": 1, "user_id": 2, "ticket_status": "canceled", "seat": 10, "purchase": 5, "face_verified": True, "verified_at": "2024-07-16 12:00:00", "created_at": "2024-07-16T12:00:00Z", "updated_at": "2024-07-16T12:00:00Z", "is_deleted": False},
                        status_codes=["200"]
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="티켓 없음",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"detail": "Not found."},
                        status_codes=["404"]
                    )
                ]
            ),
        }
    )
    def patch(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id, user_id=request.user.id)
        ticket.ticket_status = 'canceled'
        ticket.save()

        # purchase_id가 있으면 purchase_status도 '취소'로 변경
        purchase_id = getattr(ticket, 'purchase_id', None)
        if purchase_id:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE purchase SET purchase_status=%s WHERE id=%s", ['취소', purchase_id])

        serializer = TicketSerializer(ticket)
        return Response(serializer.data)

class ShareTicketsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="티켓 공유",
        description="구매(purchase_id)한 티켓 중 일부를 이메일로 지정한 유저에게 공유합니다. 본인 소유 티켓은 첫 번째로 유지됩니다.",
        parameters=[
            OpenApiParameter(name='purchase_id', description='구매 ID', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'ticket_user_emails': {
                        'type': 'array',
                        'items': {'type': 'string', 'format': 'email'},
                        'description': '양도할 유저 이메일 리스트'
                    }
                },
                'required': ['ticket_user_emails']
            }
        },
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Tickets shared successfully"},
                        status_codes=["200"]
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="입력값 오류/이메일 불일치/티켓 수 불일치 등",
                examples=[
                    OpenApiExample(
                        "BadRequest",
                        value={"error": "ticket_user_emails는 리스트 형태여야 합니다."},
                        status_codes=["400"]
                    ),
                    OpenApiExample(
                        "EmailNotFound",
                        value={"error": "일부 이메일이 존재하지 않습니다."},
                        status_codes=["400"]
                    ),
                    OpenApiExample(
                        "TicketCountMismatch",
                        value={"error": "공유 티켓 수가 맞지 않음", "details": {"current_tickets_count": 2, "shared_users_count": 1, "required_tickets": 2, "purchase_id": 1, "user_id": 2}},
                        status_codes=["400"]
                    )
                ]
            ),
        }
    )
    def post(self, request, purchase_id):
        data = request.data
        user = request.user
        ticket_user_emails = data.get("ticket_user_emails")

        if not isinstance(ticket_user_emails, list):
            return Response({"error": "ticket_user_emails는 리스트 형태여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 이메일로 유저 조회
                users = User.objects.filter(email__in=ticket_user_emails)
                if users.count() != len(ticket_user_emails):
                    return Response({"error": "일부 이메일이 존재하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

                email_to_user_id = {user.email: user.id for user in users}
                shared_user_ids = [email_to_user_id[email] for email in ticket_user_emails]

                # 본인 소유의 해당 구매 티켓들 조회
                tickets = list(Ticket.objects.select_for_update().filter(
                    purchase__id=purchase_id,
                    user=user  # ✅ 변경된 부분
                ).order_by('id'))

                expected_ticket_count = 1 + len(shared_user_ids)
                if len(tickets) != expected_ticket_count:
                    return Response({
                        "error": "공유 티켓 수가 맞지 않음",
                        "details": {
                            "current_tickets_count": len(tickets),
                            "shared_users_count": len(shared_user_ids),
                            "required_tickets": expected_ticket_count,
                            "purchase_id": purchase_id,
                            "user_id": user.id
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

                # 본인 소유는 첫 번째 티켓 유지
                my_ticket = tickets[0]
                tickets_to_share = tickets[1:1 + len(shared_user_ids)]

                now = timezone.now()
                for ticket, new_user_id in zip(tickets_to_share, shared_user_ids):
                    ticket.user_id = new_user_id
                    ticket.updated_at = now
                    ticket.save()

                return Response({"message": "Tickets shared successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AWSFaceRecognitionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="AWS Rekognition 얼굴 등록/인증",
        description="action이 'register'면 얼굴 등록, 'verify'면 얼굴 인증을 수행합니다. (Base64 인코딩 이미지 필요) user_id는 토큰(JWT) 인증에서 추출합니다.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'action': {'type': 'string', 'enum': ['register', 'verify'], 'description': "'register' 또는 'verify'"},
                    'ticket_id': {'type': 'integer', 'description': '티켓 ID'},
                    'image': {'type': 'string', 'description': 'Base64 인코딩 이미지'}
                },
                'required': ['action', 'ticket_id', 'image']
            }
        },
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "RegisterSuccess",
                        value={
                            "code": 200,
                            "message": "얼굴 등록 상태가 정상적으로 업데이트 되었습니다",
                            "data": {
                                "ticket_id": 1,
                                "user_id": 2,
                                "face_verified": True,
                                "verified_at": "2024-07-16 12:00:00",
                                "external_image_id": "user_2_ticket_1"
                            }
                        },
                        status_codes=["200"]
                    ),
                    OpenApiExample(
                        "VerifySuccess",
                        value={
                            "message": "얼굴 인증 성공",
                            "similarity": 99.5,
                            "face_id": "faceid123",
                            "external_image_id": "user_2_ticket_1",
                            "face_matches": [
                                {"similarity": 99.5, "face_id": "faceid123", "external_image_id": "user_2_ticket_1"}
                            ]
                        },
                        status_codes=["200"]
                    ),
                    OpenApiExample(
                        "VerifyFail",
                        value={
                            "message": "얼굴 인증 실패: 해당 티켓에 등록된 얼굴과 일치하지 않습니다.",
                            "face_matches": []
                        },
                        status_codes=["400"]
                    ),
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="입력값 오류/얼굴 미감지 등",
                examples=[
                    OpenApiExample(
                        "BadRequest",
                        value={"message": "얼굴이 감지되지 않았습니다."},
                        status_codes=["400"]
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="티켓 없음",
                examples=[
                    OpenApiExample(
                        "NotFound",
                        value={"message": "티켓 없음", "data": None},
                        status_codes=["404"]
                    )
                ]
            ),
            500: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="서버 오류",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"message": "처리 중 오류 발생", "error": "에러 메시지"},
                        status_codes=["500"]
                    )
                ]
            ),
        }
    )
    def post(self, request):
        try:
            action = request.data.get('action')
            ticket_id = request.data.get('ticket_id')
            image_data = request.data.get('image')
            user_id = request.user.id

            rekognition = boto3.client(
                'rekognition',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name='ap-northeast-2'
            )

            if action == 'register':
                # Rekognition Collection에 얼굴 등록
                image_bytes = base64.b64decode(image_data)
                collection_id = 'my-tickets'  # 실제 생성한 Collection ID

                external_image_id = f'user_{user_id}_ticket_{ticket_id}'
                response = rekognition.index_faces(
                    CollectionId=collection_id,
                    Image={'Bytes': image_bytes},
                    ExternalImageId=external_image_id,
                    DetectionAttributes=['DEFAULT']
                )

                if response['FaceRecords']:
                    # 티켓 정보 업데이트
                    try:
                        ticket = Ticket.objects.get(id=ticket_id)
                        ticket.face_verified = True
                        ticket.verified_at = timezone.now()
                        ticket.save()

                        verified_at_local = timezone.localtime(ticket.verified_at)
                        verified_at_str = verified_at_local.strftime('%Y-%m-%d %H:%M:%S')

                        return Response(
                            {
                                "code": 200,
                                "message": "얼굴 등록 상태가 정상적으로 업데이트 되었습니다",
                                "data": {
                                    "ticket_id": ticket.id,
                                    "user_id": ticket.user_id,
                                    "face_verified": ticket.face_verified,
                                    "verified_at": verified_at_str,
                                    "external_image_id": external_image_id
                                }
                            },
                            status=status.HTTP_200_OK,
                            content_type="application/json; charset=UTF-8"
                        )
                    except Ticket.DoesNotExist:
                        return Response(
                            {
                                "message": "티켓 없음",
                                "data": None
                            },
                            status=status.HTTP_404_NOT_FOUND,
                            content_type="application/json; charset=UTF-8"
                        )
                else:
                    return Response({
                        'message': '얼굴이 감지되지 않았습니다.'
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif action == 'verify':
                # 얼굴 인증
                image_bytes = base64.b64decode(image_data)
                collection_id = 'my-tickets'

                response = rekognition.search_faces_by_image(
                    CollectionId=collection_id,
                    Image={'Bytes': image_bytes},
                    MaxFaces=5,  # 여러 개를 받아서 필터링
                    FaceMatchThreshold=95
                )

                # 요청값으로 ExternalImageId 생성
                external_image_id = f'user_{user_id}_ticket_{ticket_id}'
                # FaceMatches 중 ExternalImageId가 일치하는 것만 필터링
                matched_face = None
                for match in response.get('FaceMatches', []):
                    if match['Face'].get('ExternalImageId') == external_image_id:
                        matched_face = match
                        break

                # FaceMatches 전체를 가공해서 응답에 포함
                face_matches_list = [
                    {
                        'similarity': m['Similarity'],
                        'face_id': m['Face']['FaceId'],
                        'external_image_id': m['Face'].get('ExternalImageId', '')
                    } for m in response.get('FaceMatches', [])
                ]

                if matched_face:
                    similarity = matched_face['Similarity']
                    face_id = matched_face['Face']['FaceId']
                    return Response({
                        'message': '얼굴 인증 성공',
                        'similarity': similarity,
                        'face_id': face_id,
                        'external_image_id': external_image_id,
                        'face_matches': face_matches_list
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'message': '얼굴 인증 실패: 해당 티켓에 등록된 얼굴과 일치하지 않습니다.',
                        'face_matches': face_matches_list
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            return Response({
                'message': '처리 중 오류 발생',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 등록된 얼굴 목록 반환 API
class FaceListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="등록된 얼굴 목록 조회",
        description="AWS Rekognition Collection에 등록된 얼굴 목록을 반환합니다.",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "data": [
                                {"FaceId": "faceid123", "ExternalImageId": "user_2_ticket_1"},
                                {"FaceId": "faceid456", "ExternalImageId": "user_3_ticket_2"}
                            ]
                        },
                        status_codes=["200"]
                    )
                ]
            ),
            500: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="서버 오류",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"message": "목록 불러오기 실패", "error": "에러 메시지"},
                        status_codes=["500"]
                    )
                ]
            ),
        }
    )
    def get(self, request):
        try:
            rekognition = boto3.client(
                'rekognition',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name='ap-northeast-2'
            )
            collection_id = 'my-tickets'
            faces = []
            response = rekognition.list_faces(CollectionId=collection_id, MaxResults=60)
            faces.extend(response.get('Faces', []))
            # NextToken 처리 (최대 1000개까지)
            next_token = response.get('NextToken')
            while next_token:
                response = rekognition.list_faces(CollectionId=collection_id, NextToken=next_token, MaxResults=60)
                faces.extend(response.get('Faces', []))
                next_token = response.get('NextToken')
            # 필요한 정보만 추려서 반환
            data = [
                {
                    'FaceId': face['FaceId'],
                    'ExternalImageId': face.get('ExternalImageId', '')
                } for face in faces
            ]
            return Response({'data': data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': '목록 불러오기 실패', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 얼굴 삭제 API
class FaceDeleteAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="등록된 얼굴 삭제",
        description="AWS Rekognition Collection에서 FaceId로 얼굴을 삭제합니다.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'face_id': {'type': 'string', 'description': '삭제할 FaceId'}
                },
                'required': ['face_id']
            }
        },
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "삭제 성공"},
                        status_codes=["200"]
                    )
                ]
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="face_id 누락 등 입력값 오류",
                examples=[
                    OpenApiExample(
                        "BadRequest",
                        value={"message": "face_id가 필요합니다."},
                        status_codes=["400"]
                    )
                ]
            ),
            500: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="서버 오류",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"message": "삭제 실패", "error": "에러 메시지"},
                        status_codes=["500"]
                    )
                ]
            ),
        }
    )
    def post(self, request):
        face_id = request.data.get('face_id')
        if not face_id:
            return Response({'message': 'face_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rekognition = boto3.client(
                'rekognition',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name='ap-northeast-2'
            )
            collection_id = 'my-tickets'
            rekognition.delete_faces(CollectionId=collection_id, FaceIds=[face_id])
            return Response({'message': '삭제 성공'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': '삭제 실패', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TicketQRView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        summary="티켓 QR 코드 생성",
        description="티켓 ID로 QR 코드를 생성하여 base64 인코딩된 이미지를 반환합니다.",
        parameters=[
            OpenApiParameter(name='ticket_id', description='티켓 ID', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"qr_base64": "iVBORw0KGgoAAAANSUhEUgAA..."},
                        status_codes=["200"]
                    )
                ]
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="티켓 없음/권한 없음",
                examples=[
                    OpenApiExample(
                        "NotFoundOrForbidden",
                        value={"error": "티켓이 존재하지 않거나 접근 권한이 없습니다."},
                        status_codes=["404"]
                    )
                ]
            ),
        }
    )
    def get(self, request, ticket_id):
        user = request.user

        try:
            ticket = Ticket.objects.select_related('user', 'seat__zone__event_time').get(id=ticket_id, user=user)
        except Ticket.DoesNotExist:
            return JsonResponse({'error': '티켓이 존재하지 않거나 접근 권한이 없습니다.'}, status=404)

        #    
        qr_url = f"http://localhost:8000/api/v1/tickets/{ticket.id}/checkin"

        qr_img = qrcode.make(qr_url)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return JsonResponse({"qr_base64": image_data})



# 2. 스태프용 티켓 확인 페이지 (HTML 렌더링)
def checkin_ticket_view(request, ticket_id):
    try:
        ticket = Ticket.objects.select_related('user', 'seat__zone__event_time').get(id=ticket_id)
    except Ticket.DoesNotExist:
        return render(request, 'invalid_ticket.html', status=404)

    context = {
        'username': ticket.user.name,
        'event_date': ticket.seat.zone.event_time.event_date.strftime("%Y-%m-%d"),
        'seat_number': ticket.seat.seat_number,
        'zone': ticket.seat.zone.rank,
        'event_time': ticket.seat.zone.event_time.start_time.strftime("%H:%M"),
        'event_name': ticket.seat.zone.event_time.event.name,
    }

    return render(request, 'checkin_ticket.html', context)

def face_register_page(request):
    return render(request, 'face_register.html')
