# 2025 Summer Bootcamp TeamG - Backend (Django + MySQL + AWS Rekognition)

## 프로젝트 구조

```
Backend/
  ├── manage.py
  ├── requirements.txt
  ├── dockerfile
  ├── docker-compose.yml
  ├── .gitignore
  ├── ticket_backend/
  └── facepass/
```

---

## 시작하기

### 1. 필수 프로그램 설치 (최초 1회)

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 (Windows/Mac)
- (선택) Python 3.10+ (로컬 개발 시)

---

### 2. 저장소 클론

```bash
git clone https://github.com/2025-summerbootcamp-TeamG/Backend.git
cd Backend
```

---

### 3. 환경 변수 파일(.env) 생성

- `.env` 파일은 **반드시 직접 만들어야 합니다** (예시: 아래 참고)
- 민감정보는 절대 깃허브에 올리지 마세요!  
- 예시:
  ```
  # .env 예시
  # AWS
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# MySQL (장고 설정과 동일하게)
MYSQL_DATABASE=ticketing
MYSQL_USER=ticketuser
MYSQL_PASSWORD=ticketpass
MYSQL_ROOT_PASSWORD=rootpass
  ```

---

### 4. 도커로 실행

```bash
docker-compose up --build
```
- Django 서버: http://localhost:8000
- MySQL: localhost:3306 (컨테이너 내부에서는 `db`로 접근)

---

### 5.  마이그레이션 및 슈퍼유저 생성 (최초 1회 초기 세팅 할 때 하면 됨, 깃 클론한 팀원은 실행 X)
- migrate : Django가 DB에 필요한 테이블을 자동으로 생성함 
- createsuperuser : /admin페이지에 로그인할 수 있는 최초 관리자 계정 생성
- 아직 실행 안함

```bash
docker-compose exec web bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 주요 기술 스택

- Django 4.2+
- Django REST Framework
- MySQL 8.0
- AWS Rekognition (boto3)
- Docker, docker-compose

---

## 주요 설정 파일 설명

### dockerfile

- Django + MySQL 연동을 위한 Python 3.10 기반 컨테이너 환경을 정의합니다.
- 주요 내용:
  - 시스템 패키지(gcc, libmysqlclient 등) 설치
  - requirements.txt로 파이썬 패키지 설치
  - 소스코드 복사 및 gunicorn으로 서버 실행

```dockerfile
FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONUNBUFFERED 1
WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "ticket_backend.wsgi:application"]
```

### docker-compose.yml

- Django 웹 서버와 MySQL DB를 한 번에 실행하는 오케스트레이션 파일입니다.
- 주요 내용:
  - `web`: Django + gunicorn 컨테이너
  - `db`: MySQL 8.0 컨테이너 (환경변수로 DB 초기화)
  - 볼륨, 포트, .env 연동 등 설정

```yaml
version: '3.9'
services:
  web:
    build: .
    container_name: django-backend
    command: gunicorn ticket_backend.wsgi:application --bind 0.0.0.0:8000
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
  db:
    image: mysql:8.0
    container_name: mysql-db
    restart: always
    environment:
      MYSQL_DATABASE: ticketing
      MYSQL_USER: ticketuser
      MYSQL_PASSWORD: ticketpass
      MYSQL_ROOT_PASSWORD: rootpass
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
volumes:
  mysql_data:
```

### requirements.txt

- Django 서버와 AWS Rekognition, MySQL 연동에 필요한 파이썬 패키지 목록입니다.
- 주요 패키지:
  - Django, gunicorn, boto3, Pillow, djangorestframework, python-decouple, python-dotenv, mysqlclient 등

```txt
Django>=4.2,<5.0
gunicorn>=20.1.0    # Python 웹 프레임워크를 운영환경에서 안정적으로 실행하기 위한 WSGI서버
boto3>=1.28         # AWS Rekognition 호출용
Pillow>=10.0        # 이미지 업로드/처리
 djangorestframework # REST API 작성
python-decouple     # .env 파일 관리
python-dotenv       # .env 직접 불러오기
mysqlclient         # MySQL 연동
```

---

## 개발/운영 참고

- **requirements.txt**: 주요 파이썬 패키지 목록
- **dockerfile**: Django + MySQL 연동 및 gunicorn 실행 환경
- **docker-compose.yml**: 웹/DB 컨테이너 오케스트레이션
- **.gitignore**: `.env`, `.venv` 등 민감/불필요 파일 무시

---

## 브랜치 전략 & 커밋 메시지

- main: 배포/릴리즈
- develop: 개발 기본 브랜치
- feature/이름: 기능 개발 브랜치

- 커밋 메시지 예시:
  - feat: 새로운 기능
  - fix: 버그 수정
  - docs: 문서 수정
  - style: 코드 포맷팅 등

---

## 문제 해결

- **도커 실행 오류**
  - Docker Desktop 실행 여부 확인
  - 포트(8000, 3306) 충돌 시 다른 앱 종료
- **DB 연결 오류**
  - .env의 DB 정보 확인
  - docker-compose 재시작
- **환경 변수 누락**
  - .env 파일이 있는지, 값이 올바른지 확인

---

## 기타

- AWS Rekognition 연동/테스트는 추후 안내 예정
- 추가 패키지 설치 시 requirements.txt에 꼭 반영
- 궁금한 점은 팀 채널/깃허브 이슈로 문의

---
