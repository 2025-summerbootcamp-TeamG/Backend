from django.db import models

# Create your models here.
from user.models import User
from events.models import Seat

class Purchase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purchase_status = models.CharField(max_length=20)  # 예: 결제 전, 완료, 취소 등
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    purchaser = models.CharField(max_length=20, null=True)
    phone_number = models.CharField(max_length=30, null=True)
    email = models.CharField(max_length=50, null=True)

    class Meta:
        db_table = 'purchase' 


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE)
    ticket_status = models.CharField(max_length=20)  # 예: booked, canceled, etc
    booked_at = models.DateTimeField(null=True, blank=True)
    face_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'ticket'
    
    def __str__(self):
        return f"Ticket {self.id}"
