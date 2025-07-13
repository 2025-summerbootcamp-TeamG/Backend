from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Event, EventTime, Zone, Seat
from .serializers import EventListSerializer

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
            }, status=200)
        except Zone.DoesNotExist:
            return Response({
                "statusCode": 404,
                "message": "해당 존의 좌석 정보를 찾을 수 없습니다.",
                "data": None
            }, status=404)
            