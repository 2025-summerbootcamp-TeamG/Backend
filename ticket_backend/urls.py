from django.contrib import admin
from django.urls import path, include, re_path
from events.views import EventListAPIView, EventDetailAPIView, EventSeatsAPIView, BuyTicketsView, PayTicketView
from tickets.views import FaceRegisterAPIView, TicketFaceAuthAPIView, AWSFaceRecognitionView, face_register_page
from tickets.views import FaceListAPIView, FaceDeleteAPIView, ShareTicketsView, TicketQRView, checkin_ticket_view
from user.views import UserSignupView, UserLoginView, UserLogoutView

from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/events/view/', EventListAPIView.as_view(), name='event-list'),
    path('api/v1/events/<int:event_id>/', EventDetailAPIView.as_view(), name='event-detail'),
    path('api/v1/events/<int:zone_id>/seats/', EventSeatsAPIView.as_view(), name='event-seats'),
    path('api/v1/events/<int:event_id>/tickets/buy', BuyTicketsView.as_view(), name = 'buy-ticket'),
    path('api/v1/events/<int:purchase_id>/tickets/pay/', PayTicketView.as_view(), name='pay-ticket'),
    path('api/v1/tickets/<int:ticket_id>/register/', FaceRegisterAPIView.as_view(), name='ticket-face-register'),
    path('api/v1/tickets/<int:purchase_id>/share/', ShareTicketsView.as_view(), name='share-tickets'),
    path('api/v1/tickets/<int:ticket_id>/auth/', TicketFaceAuthAPIView.as_view(), name='ticket-face-auth'),
    path('api/v1/tickets/face-recognition/', AWSFaceRecognitionView.as_view(), name='face-recognition'),
    path('api/v1/tickets/<int:ticket_id>/qr', TicketQRView.as_view(), name='ticket-qr'),
    path('api/v1/user/signup/', UserSignupView.as_view(), name='signup'),
    path('api/v1/user/login/', UserLoginView.as_view(), name='login'),
    path('api/v1/user/logout/', UserLogoutView.as_view(), name='logout'),

    path('api/v1/tickets/<int:ticket_id>/checkin', checkin_ticket_view, name='ticket-checkin'),

    path('api/v1/tickets/face-register/', face_register_page, name='face-register'),
    path('api/v1/tickets/face-list/', FaceListAPIView.as_view(), name='face-list'),
    path('api/v1/tickets/face-delete/', FaceDeleteAPIView.as_view(), name='face-delete'),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)