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


class FaceRegisterAPIView(APIView):
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
            user_id = request.data.get('user_id')  # 요청에서 user_id 받기

            if face_verified is None or user_id is None:
                return Response(
                    {
                        "message": "face_verified와 user_id가 필요합니다",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                    content_type="application/json; charset=UTF-8"
                )

            # 티켓의 user_id와 요청의 user_id 비교
            if str(ticket.user_id) != str(user_id):
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
    def patch(self, request, pk):
        # AWS Rekognition 결과에서 Face Matches와 User ID 추출
        face_matches = request.data.get('face_matches')  # 예: 95
        user_id = request.data.get('user_id')

        if face_matches is None or user_id is None:
            return Response({'error': 'face_matches와 user_id가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({'error': '티켓을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

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
    def get(self, request):
        # 인증 구현 전까지 user id를 쿼리 파라미터로 받음
        user_id = request.query_params.get('user_id')
        tickets = Ticket.objects.filter(user_id=user_id)
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)

# 티켓 상세정보 조회
class TicketDetailView(APIView):
    def get(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)
        serializer = TicketSerializer(ticket)
        return Response(serializer.data)

# 티켓 취소
class TicketCancelView(APIView):
    def patch(self, request, ticket_id):
        ticket = get_object_or_404(Ticket, id=ticket_id)
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
    def post(self, request, purchase_id):
        data = request.data
        user_id = data.get("user_id")
        ticket_user_emails = data.get("ticket_user_emails")

        if not user_id or not isinstance(ticket_user_emails, list):
            return Response({"error": "user_id and ticket_user_emails are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 이메일로 유저 조회
                users = User.objects.filter(email__in=ticket_user_emails)
                if users.count() != len(ticket_user_emails):
                    return Response({"error": "Some emails do not match any user"}, status=status.HTTP_400_BAD_REQUEST)

                email_to_user_id = {user.email: user.id for user in users}
                shared_user_ids = [email_to_user_id[email] for email in ticket_user_emails]

                # 모든 티켓 가져오기 (본인 user_id로 등록된)
                tickets = list(Ticket.objects.select_for_update().filter(purchase__id=purchase_id, user_id=user_id).order_by('id'))

                if len(tickets) != 1 + len(shared_user_ids):
                    return Response({
                        "error": "공유 티켓 수가 맞지 않음",
                        "details": {
                            "current_tickets_count": len(tickets),
                            "shared_users_count": len(shared_user_ids),
                            "required_tickets": 1 + len(shared_user_ids),
                            "purchase_id": purchase_id,
                            "user_id": user_id
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

                # 첫 번째 티켓은 본인 소유 유지
                my_ticket = tickets[0]
                tickets_to_share = tickets[1:1+len(shared_user_ids)]

                # 티켓 업데이트
                now = timezone.now()
                for ticket, new_user_id in zip(tickets_to_share, shared_user_ids):
                    ticket.user_id = new_user_id
                    ticket.updated_at = now
                    ticket.save()

                return Response({"message": "Tickets shared successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AWSFaceRecognitionView(APIView):
    def post(self, request):
        try:
            action = request.data.get('action')
            user_id = request.data.get('user_id')
            ticket_id = request.data.get('ticket_id')
            image_data = request.data.get('image')

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


def face_register_page(request):
    return render(request, 'face_register.html')
