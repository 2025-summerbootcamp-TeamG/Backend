FROM python:3.10-slim

# .pyc같이 불필요한 캐시 파일이 생기지 않도록 방지
ENV PYTHONDONTWRITEBYTECODE 1 
# 파이썬 출력을 버퍼링 없이 즉시 출력하게 함 
ENV PYTHONUNBUFFERED 1

# 컨테이너 내부에서 작업 디렉토리로 /app을 설정
WORKDIR /app

# 필요한 시스템 패키지 설치 (mysqlclient 빌드에 필요) c 코드 컴파일 해야함
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean

# requirements 파일을 컨테이너로 복사하고 pip최신으로 업그레이드하고, 의존성 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 프로젝트의 모든 파일을 컨테이너의 /app 디렉토리로 복사
COPY . .

# 컨테이너가 시작될 때 실행할 명령어 
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ticket_backend.wsgi:application"]
