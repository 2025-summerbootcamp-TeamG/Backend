from django.db import models

# Create your models here.


class Event(models.Model):
    name = models.CharField(max_length=50)
    artist = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()
    genre = models.CharField(max_length=30)
    age_rating = models.CharField(max_length=20)
    max_reserve = models.IntegerField(null=True, blank=True)
    image_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'event'  


class EventTime(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    event_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'event_time'  


class Zone(models.Model):
    event_time = models.ForeignKey(EventTime, on_delete=models.CASCADE)
    price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    rank = models.CharField(max_length=5)
    total_count = models.IntegerField()
    available_count = models.IntegerField()

    class Meta:
        db_table = 'zone'  


class Seat(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    seat_status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'seat'  