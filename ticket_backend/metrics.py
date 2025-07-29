from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse

# 커스텀 메트릭 예시: 얼굴인식 실패 카운터
face_recognition_failures = Counter('face_recognition_failures_total', 'Count of face recognition failures')

# 임의 메트릭: 현재 활성 사용자 수 (Gauge)
active_users = Gauge('active_users', 'Number of active users')

def metrics_view(request):
    # 여기서 generate_latest()가 모든 메트릭을 프로메테우스 형식으로 인코딩해서 반환
    metrics_page = generate_latest()
    return HttpResponse(metrics_page, content_type=CONTENT_TYPE_LATEST)
