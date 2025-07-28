import os
from pathlib import Path
from dotenv import load_dotenv  
from datetime import timedelta
import logging

DEBUG=True

# .env 파일 로드
load_dotenv()

# BASE_DIR 설정
BASE_DIR = Path(__file__).resolve().parent.parent

# 보안 설정
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key")  # 실제 배포 시 .env에서 관리

DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]  # 개발 시는 * 허용 / 배포 시 도메인 지정

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

# 앱 등록
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',  # Django REST Framework
    'drf_spectacular',  # swagger
    'drf_spectacular_sidecar',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'tickets',  # tickets 앱 추가
    'user',
    'events',
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "BLACKLIST_AFTER_ROTATION": True,
    "ROTATE_REFRESH_TOKENS": True,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}



AUTH_USER_MODEL = 'user.User'

# 미들웨어
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ticket_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ticket_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.mysql",
        'NAME': os.environ.get("MYSQL_DATABASE", ""),
        'USER': os.environ.get("MYSQL_USER", ""),
        'PASSWORD': os.environ.get("MYSQL_PASSWORD", ""),
        'HOST': os.environ.get("MYSQL_HOST", "db"),
        'PORT': os.environ.get("MYSQL_PORT", "3306"),
    }
}


# 비밀번호 정책 (기본 유지)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 언어/시간대 설정
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Seoul'  # 한국 시간
USE_I18N = True
USE_TZ = True

# URL 슬래시 자동 추가 비활성화
APPEND_SLASH = False

# 정적 파일
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'

# 기본 PK 필드
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AWS Rekognition용 환경변수 불러오기
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")


SPECTACULAR_SETTINGS = {
    'TITLE': 'TeamG Face Ticketing API',
    'DESCRIPTION': 'API documentation for face ticketing project.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# (LOGGING 설정이 있다면 아래와 같이 수정)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}