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


###############################################
# 얼굴 관련 API 모음 (등록/인증/상태조회/DB/AWS)
###############################################

# --- 1. AWS Rekognition 얼굴 등록 ---
# [POST] /api/v1/tickets/<ticket_id>/aws-register/
# - JWT 토큰 인증 필요
# - base64 이미지(image) 전달
# - AWS Rekognition에 user_{user_id}_ticket_{ticket_id}로 등록
# - 성공 시 FaceId, ExternalImageId 반환
class AWSFaceRecognitionRegister(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="AWS Rekognition 얼굴 등록",
        description="AWS Rekognition에 얼굴을 등록합니다. ExternalImageId는 user_{user_id}_ticket_{ticket_id}로 지정.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'image': {'type': 'string', 'description': 'base64 인코딩 얼굴 이미지'},
                },
                'required': ['image']
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
                        value={"message": "얼굴 등록 성공", "FaceId": "...", "ExternalImageId": "user_1_ticket_2"},
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
                        value={"message": "image가 필요합니다."},
                        status_codes=["400"]
                    )
                ]
            ),
        }
    )
    def post(self, request, ticket_id):
        image_base64 = request.data.get('image')
        if not image_base64:
            return Response({"message": "image가 필요합니다."}, status=400)
        try:
            import base64, os, boto3
            image_bytes = base64.b64decode(image_base64)
            user_id = request.user.id
            external_image_id = f"user_{user_id}_ticket_{ticket_id}"
            rekognition = boto3.client(
                'rekognition',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name='ap-northeast-2'
            )
            collection_id = 'my-tickets'
            response = rekognition.index_faces(
                CollectionId=collection_id,
                Image={'Bytes': image_bytes},
                ExternalImageId=external_image_id,
                DetectionAttributes=['DEFAULT']
            )
            faces = response.get('FaceRecords', [])
            if faces:
                return Response({
                    "message": "얼굴 등록 성공",
                    "FaceId": faces[0]['Face']['FaceId'],
                    "ExternalImageId": faces[0]['Face']['ExternalImageId']
                }, status=200)
            else:
                return Response({"message": "얼굴 등록 실패", "response": response}, status=400)
        except Exception as e:
            return Response({"message": "AWS Rekognition 처리 중 오류", "error": str(e)}, status=500)

# --- 2. AWS Rekognition 얼굴 인증 ---
# [POST] /api/v1/tickets/<ticket_id>/aws-auth/
# - JWT 토큰 인증 필요
# - base64 이미지(image) 전달
# - AWS Rekognition에서 user_{user_id}_ticket_{ticket_id}로 등록된 얼굴과만 비교
# - 성공 시 FaceId, ExternalImageId, Similarity 반환
class AWSFaceRecognitionAuth(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="AWS Rekognition 얼굴 인증",
        description="AWS Rekognition에서 user_{user_id}_ticket_{ticket_id}로 등록된 얼굴과만 비교하여 인증합니다.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'image': {'type': 'string', 'description': 'base64 인코딩 얼굴 이미지'},
                },
                'required': ['image']
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
                        value={"message": "얼굴 인증 성공", "FaceId": "...", "ExternalImageId": "user_1_ticket_2", "Similarity": 99.9},
                        status_codes=["200"]
                    ),
                    OpenApiExample(
                        "Fail",
                        value={"message": "얼굴 인증 실패", "Similarity": 0},
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
                        value={"message": "image가 필요합니다."},
                        status_codes=["400"]
                    )
                ]
            ),
        }
    )
    def post(self, request, ticket_id):
        image_base64 = request.data.get('image')
        if not image_base64:
            return Response({"message": "image가 필요합니다."}, status=400)
        try:
            import base64, os, boto3
            image_bytes = base64.b64decode(image_base64)
            user_id = request.user.id
            external_image_id = f"user_{user_id}_ticket_{ticket_id}"
            rekognition = boto3.client(
                'rekognition',
                aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                region_name='ap-northeast-2'
            )
            collection_id = 'my-tickets'
            response = rekognition.search_faces_by_image(
                CollectionId=collection_id,
                Image={'Bytes': image_bytes},
                MaxFaces=5,
                FaceMatchThreshold=95
            )
            face_matches = response.get('FaceMatches', [])
            # ExternalImageId가 정확히 일치하는 것만 필터링
            filtered = [f for f in face_matches if f['Face'].get('ExternalImageId') == external_image_id]
            if filtered:
                best = max(filtered, key=lambda f: f['Similarity'])
                return Response({
                    "message": "얼굴 인증 성공",
                    "FaceId": best['Face']['FaceId'],
                    "ExternalImageId": best['Face']['ExternalImageId'],
                    "Similarity": best['Similarity']
                }, status=200)
            else:
                return Response({"message": "얼굴 인증 실패", "Similarity": 0}, status=200)
        except Exception as e:
            return Response({"message": "AWS Rekognition 처리 중 오류", "error": str(e)}, status=500)

# --- 3. DB 기반 얼굴 등록 상태 변경 ---
# [PATCH] /api/v1/tickets/<ticket_id>/register/
# - JWT 토큰 인증 필요
# - face_verified(boolean)만 입력
# - DB의 ticket 테이블에 face_verified, verified_at만 저장
class FaceRegisterAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="티켓 얼굴 등록 상태 변경 (DB 필드만)",
        description="티켓의 face_verified, verified_at 필드만 DB에 저장합니다. AWS 등 외부 연동 없음.",
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
                description="성공: DB에 face_verified, verified_at 저장",
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
                description="입력값 오류 (face_verified 없음)",
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
                description="권한 없음 (본인 티켓 아님)",
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
                        value={"message": "내부 서버 오류", "error": "에러 메시지"},
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
                {"message": "티켓 없음", "data": None},
                status=status.HTTP_404_NOT_FOUND
            )
        if ticket.user_id != request.user.id:
            return Response(
                {"message": "해당 사용자의 티켓 권한 없음", "data": None},
                status=status.HTTP_403_FORBIDDEN
            )
        face_verified = request.data.get('face_verified')
        if face_verified is None:
            return Response(
                {"message": "face_verified가 필요합니다", "data": None},
                status=status.HTTP_400_BAD_REQUEST
            )
        if isinstance(face_verified, str):
            face_verified = face_verified.lower() == 'true'
        try:
            ticket.face_verified = face_verified
            ticket.verified_at = timezone.now() if face_verified else None
            ticket.save()
            verified_at_str = timezone.localtime(ticket.verified_at).strftime('%Y-%m-%d %H:%M:%S') if ticket.verified_at else None
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
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "내부 서버 오류", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# --- 4. DB 기반 얼굴 등록 상태 조회 ---
# [GET] /api/v1/tickets/<ticket_id>/auth/
# - JWT 토큰 인증 필요
# - DB의 ticket 테이블에서 face_verified, verified_at만 조회
class TicketFaceAuthAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="티켓 얼굴 등록 상태 조회 (DB 필드만)",
        description="티켓의 face_verified, verified_at 필드만 DB에서 조회합니다. AWS 등 외부 연동 없음.",
        parameters=[
            OpenApiParameter(name='ticket_id', description='티켓 ID', required=True, type=int, location=OpenApiParameter.PATH),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="성공: DB에서 face_verified, verified_at 조회",
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
            403: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="권한 없음 (본인 티켓 아님)",
                examples=[
                    OpenApiExample(
                        "Forbidden",
                        value={"message": "해당 사용자의 티켓 권한 없음", "data": None},
                        status_codes=["403"]
                    )
                ]
            ),
            500: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="서버 오류",
                examples=[
                    OpenApiExample(
                        "ServerError",
                        value={"message": "내부 서버 오류", "error": "에러 메시지"},
                        status_codes=["500"]
                    )
                ]
            ),
        }
    )
    def get(self, request, ticket_id):
        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return Response(
                {"code": 404, "message": "티켓 없음.", "data": None},
                status=status.HTTP_404_NOT_FOUND
            )
        if ticket.user_id != request.user.id:
            return Response(
                {"message": "해당 사용자의 티켓 권한 없음", "data": None},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            verified_at = ticket.verified_at
            verified_at_str = timezone.localtime(verified_at).strftime('%Y-%m-%d %H:%M:%S') if verified_at else None
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
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "내부 서버 오류", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
