from django.urls import path
from .views import FaceRegisterAPIView, TicketFaceAuthAPIView

urlpatterns = [
    path('api/v1/tickets/<int:ticket_id>/register/', FaceRegisterAPIView.as_view()),
    path('api/v1/tickets/<int:ticket_id>/auth/', TicketFaceAuthAPIView.as_view()),
]