from django.contrib import admin
from django.urls import path, include, re_path
from events.views import EventListAPIView, EventDetailAPIView, EventSeatsAPIView, BuyTicketsView, PayTicketView
from tickets.views import FaceRegisterAPIView, TicketFaceAuthAPIView, AWSFaceRecognitionView, face_register_page
from tickets.views import FaceListAPIView, FaceDeleteAPIView, ShareTicketsView
from user.views import UserSignupView, UserLoginView, UserLogoutView

from django.conf import settings
from django.conf.urls.static import static

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title="weheproject API",  # 타이틀
        default_version='v1',   # 버전
        description="API for weheproject",   # 설명
        terms_of_service="API약관",
        contact=openapi.Contact(email="이메일") # 입력하지않고 삭제해도 되는 부분
    ),
    public=True,
    permission_classes=(AllowAny,)
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
    path('api/v1/user/signup/', UserSignupView.as_view(), name='signup'),
    path('api/v1/user/login/', UserLoginView.as_view(), name='login'),
    path('api/v1/user/logout/', UserLogoutView.as_view(), name='logout'),

    path('api/v1/tickets/face-register/', face_register_page, name='face-register'),

    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)