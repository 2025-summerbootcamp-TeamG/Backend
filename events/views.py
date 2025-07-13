from django.shortcuts import render
# events/views.py
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Seat  
from tickets.models import Purchase, Ticket  
from user.models import User   


class BuyTicketsView(APIView):
    def post(self, request, event_id): # POST request 
        data = request.data
        user_id = data.get('user_id') 
        seat_ids = data.get('seat_id', [])
        event_time_id = data.get('event_time_id')

        if not user_id or not seat_ids or not event_time_id:
            return Response({'error': 'user_id, seat_id list, and event_time_id are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user_id is None:
            return Response({'error': 'user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(seat_ids, list) or not seat_ids:
            return Response({'error': 'seat_id must be a non-empty list.'}, status=status.HTTP_400_BAD_REQUEST)
        if event_time_id is None:
            return Response({'error': 'event_time_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 유저 존재 확인
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        seats = Seat.objects.filter(id__in=seat_ids)
        if seats.count() != len(seat_ids):
            return Response({'error': 'Some seats not found.'}, status=status.HTTP_404_NOT_FOUND)

        unavailable_seats = [seat.id for seat in seats if seat.seat_status != 'available']
        if unavailable_seats:
            return Response({'error': f'이미 선택된 좌석입니다: {unavailable_seats}'}, status=status.HTTP_400_BAD_REQUEST)
        # 1. Purchase 생성
        purchase = Purchase.objects.create(
            user=user,
            purchase_status="결제 전",
            created_at=timezone.now(),
            updated_at=timezone.now(),
            is_deleted=False
        )



        # 2. Seat 리스트 기반으로 Ticket 여러 개 생성
        tickets = []
        for seat_id in seat_ids:
            try:
                seat = Seat.objects.get(id=seat_id)
            except Seat.DoesNotExist:
                return Response({'error': f'Seat {seat_id} not found.'}, status=status.HTTP_404_NOT_FOUND)



            ticket = Ticket.objects.create(
                user=user,
                seat=seat,
                purchase=purchase,
                ticket_status='booked',
                face_verified=False,
                verified_at=None,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                is_deleted=False
            )
            seat.seat_status = 'booked'
            seat.save()

            tickets.append(ticket.id)

        return Response({
            'message': 'Tickets successfully created.',
            'purchase_id': purchase.id,
            'ticket_ids': tickets
        }, status=status.HTTP_201_CREATED)
