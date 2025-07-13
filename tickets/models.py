from django.db import models

# Create your models here.
class Ticket(models.Model):
    user_id = models.IntegerField()  # 또는 ForeignKey(User, ...) 등
    face_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    # ... (DB의 ticket 테이블에 맞는 필드 추가) ...
    class Meta:
        db_table = 'ticket'
    
    def __str__(self):
        return f"Ticket {self.id}"