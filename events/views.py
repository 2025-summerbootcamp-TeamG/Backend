from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Seat  
from tickets.models import Purchase, Ticket  
from user.models import User   


from rest_framework import viewsets
from django.db.models import Q
from .models import Event, EventTime, Zone, Seat
from .serializers import EventListSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class BuyTicketsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id):
        data = request.data
        user = request.user  # ✅ JWT에서 인증된 유저
        seat_ids = data.get('seat_id', [])
        event_time_id = data.get('event_time_id')

        # user_id는 이제 검증할 필요 없음
        if not seat_ids or not event_time_id:
            return Response({'error': 'seat_id list and event_time_id are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(seat_ids, list) or not seat_ids:
            return Response({'error': 'seat_id must be a non-empty list.'}, status=status.HTTP_400_BAD_REQUEST)

        # 좌석 존재 여부 확인
        seats = Seat.objects.filter(id__in=seat_ids)
        if seats.count() != len(seat_ids):
            return Response({'error': 'Some seats not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 이미 예약된 좌석 확인
        unavailable_seats = [seat.id for seat in seats if seat.seat_status != 'available']
        if unavailable_seats:
            return Response({'error': f'이미 선택된 좌석입니다: {unavailable_seats}'}, status=status.HTTP_400_BAD_REQUEST)

        # Purchase 생성
        purchase = Purchase.objects.create(
            user=user,
            purchase_status="결제 전",
            created_at=timezone.now(),
            updated_at=timezone.now(),
            is_deleted=False
        )

        # Ticket 생성
        tickets = []
        for seat in seats:
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


class PayTicketView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, purchase_id):
        data = request.data
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')

        # 필수값 확인
        if not all([name, phone, email]):
            return Response({'error': 'name, phone, email은 모두 필수입니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 인증된 유저와 purchase_id로 구매 정보 조회
            purchase = Purchase.objects.get(id=purchase_id, user=request.user, is_deleted=False)
        except Purchase.DoesNotExist:
            return Response({'error': '해당 구매 정보를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        # 정보 업데이트
        purchase.purchase_status = 'completed'
        purchase.updated_at = timezone.now()
        purchase.purchaser = name
        purchase.phone_number = phone
        purchase.email = email
        purchase.save()

        return Response({'message': '결제가 완료되었습니다.'}, status=status.HTTP_200_OK)


# Create your views here.
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()

class EventListAPIView(APIView):
    def get(self, request):
        try:
            keyword = request.GET.get('keyword', '')
            category = request.GET.get('category', '')
            sort = request.GET.get('sort', '')  # 'popular', 'new' 등
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 10))
            offset = (page - 1) * limit

            queryset = Event.objects.filter(is_deleted=False)

            if keyword:
                queryset = queryset.filter(
                    Q(artist__icontains=keyword) |
                    Q(location__icontains=keyword) |
                    Q(description__icontains=keyword)
                )
            if category:
                queryset = queryset.filter(genre=category)

            if sort == 'popular':
                queryset = queryset.order_by('-view_count')
            elif sort == 'new':
                queryset = queryset.order_by('-created_at')
            else:
                queryset = queryset.order_by('-created_at')

            total_count = queryset.count()
            events = queryset[offset:offset+limit]
            serializer = EventListSerializer(events, many=True)

            if total_count == 0:
                return Response({
                    "page": page,
                    "limit": limit,
                    "totalCount": 0,
                    "events": [],
                    "message": "검색 결과가 없습니다."
                }, status=status.HTTP_200_OK)

            return Response({
                "page": page,
                "limit": limit,
                "totalCount": total_count,
                "events": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class EventDetailAPIView(APIView):
    def get(self, request, event_id):
        try:
            event = Event.objects.get(pk=event_id, is_deleted=False)
            # 공연 일정 리스트
            schedules = EventTime.objects.filter(event=event).order_by('event_date', 'start_time')
            schedule_list = [
                {
                    "date": et.event_date.isoformat(),
                    "start_time": et.start_time.strftime("%H:%M"),
                    "end_time": et.end_time.strftime("%H:%M")
                }
                for et in schedules
            ]
            # 가격 범위 계산
            prices = []
            for et in schedules:
                prices += [z.price for z in et.zone_set.all()]
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0

            data = {
                "id": event.id,
                "title": event.artist,
                "date": schedules[0].event_date.isoformat() if schedules else None,
                "location": event.location,
                "price": f"₩{min_price:,} ~ ₩{max_price:,}" if min_price != max_price else f"₩{min_price:,}",
                "thumbnail": event.image_url,
                "tag": "인기",
                "description": event.description,
                "schedules": schedule_list,
            }
            return Response(data)
        except Event.DoesNotExist:
            return Response({"message": "행사를 찾을 수 없습니다."}, status=404)
            
class EventSeatsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, zone_id):
        try:
            zone = Zone.objects.get(pk=zone_id, is_deleted=False)
            seats = Seat.objects.filter(zone=zone)
            seats_data = []
            for seat in seats:
                seats_data.append({
                    "seat_id": seat.id,
                    "seat_number": seat.seat_number,
                    "price": zone.price,
                    "seat_status": seat.seat_status,
                    "event_time_id": zone.event_time.id,
                    "available_count": zone.available_count  # 잔여좌석
                })
            return Response({
                "statusCode": 200,
                "message": "좌석 정보를 성공적으로 불러왔습니다.",
                "data": seats_data
            }, status=status.HTTP_200_OK)
        except Zone.DoesNotExist:
            return Response({
                "statusCode": 404,
                "message": "해당 존의 좌석 정보를 찾을 수 없습니다.",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)