"""
URL configuration for ticket_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from events.views import EventListAPIView, EventDetailAPIView, EventSeatsAPIView

urlpatterns = [
    path('admin/', admin.site.urls),

    # 이벤트 관련 API
    path('api/v1/events/view/', EventListAPIView.as_view(), name='event-list'),
    path('api/v1/events/<int:event_id>', EventDetailAPIView.as_view(), name='event-detail'),
    path('api/v1/events/<int:zone_id>/seats/', EventSeatsAPIView.as_view(), name='event-seats'),

    # 티켓 관련 API (기존)
    path('', include('tickets.urls')),

    # 사용자 인증(회원가입/로그인/로그아웃) API
    path('user/signup/', UserSignupView.as_view(), name='signup'),
    path('user/login/', UserLoginView.as_view(), name='login'),
    path('user/logout/', UserLogoutView.as_view(), name='logout'),

]