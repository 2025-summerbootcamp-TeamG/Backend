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
  ├── user/
  ├── events
  └── tickets/

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
