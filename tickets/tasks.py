from celery import shared_task
from django.utils import timezone
from .models import Ticket

@shared_task
def auto_cancel_ticket(ticket_id):
    print(f"[Celery] 자동취소 태스크 실행: {ticket_id}")
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        print(f"[Celery] 현재 상태: {ticket.ticket_status}")
        if ticket.ticket_status in ['booked', 'reserved']:
            ticket.ticket_status = 'canceled'
            ticket.is_deleted = True
            ticket.save()
            # 좌석도 available로 변경
            seat = ticket.seat
            seat.seat_status = 'available'
            seat.save()
            print(f"[Celery] 티켓 {ticket_id} 취소 및 좌석 available 처리 완료")
        else:
            print(f"[Celery] 티켓 {ticket_id}는 이미 상태가 {ticket.ticket_status}라서 취소 안함")
    except Ticket.DoesNotExist:
        print(f"[Celery] 티켓 {ticket_id} 없음") 