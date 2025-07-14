from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Ticket
from .serializers import TicketSerializer
from django.shortcuts import get_object_or_404
from django.db import connection


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