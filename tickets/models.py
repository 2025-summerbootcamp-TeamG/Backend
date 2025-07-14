from django.db import models

# Create your models here.
from django.db import models
from user.models import User
from events.models import Seat

from django.contrib.auth import get_user_model

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
class Ticket(models.Model):
    user_id = models.IntegerField()  # 또는 ForeignKey(User, ...) 등
    face_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    # ... (DB의 ticket 테이블에 맞는 필드 추가) ...
    class Meta:
        db_table = 'ticket'
    
    def __str__(self):
        return f"Ticket {self.id}"
        
class Ticket(models.Model):
    user_id = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    event_id = models.IntegerField()
    seat_number = models.CharField(max_length=20)
    ticket_status = models.CharField(max_length=20, default='booked')  # booked, canceled 등
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} - {self.event_id} - {self.seat_number}"

class Event(models.Model):
    artist = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()
    genre = models.CharField(max_length=50)
    age_rating = models.CharField(max_length=10)
    max_reserve = models.IntegerField()
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.artist} - {self.location}"