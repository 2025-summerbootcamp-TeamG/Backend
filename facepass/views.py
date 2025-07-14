from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Ticket
from .serializers import TicketSerializer
from django.shortcuts import get_object_or_404
from django.db import connection

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
        ticket.status = 'canceled'
        ticket.save()

        # purchase_id가 있으면 purchase_status도 '취소'로 변경
        purchase_id = getattr(ticket, 'purchase_id', None)
        if purchase_id:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE purchase SET purchase_status=%s WHERE id=%s", ['취소', purchase_id])

        serializer = TicketSerializer(ticket)
        return Response(serializer.data)
