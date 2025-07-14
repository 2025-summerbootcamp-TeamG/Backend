from django.urls import path
from .views import FaceRegisterAPIView, TicketFaceAuthAPIView, MyTicketListView, TicketDetailView, TicketCancelView

urlpatterns = [
    path('api/v1/tickets/<int:ticket_id>/register/', FaceRegisterAPIView.as_view()),
    path('api/v1/tickets/<int:ticket_id>/auth/', TicketFaceAuthAPIView.as_view()),
    path('tickets/', MyTicketListView.as_view(), name='ticket-list'),
    path('tickets/<int:ticket_id>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<int:ticket_id>/cancel/', TicketCancelView.as_view(), name='ticket-cancel'),
]