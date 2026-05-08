# Remory Backend - 설정 및 실행 가이드

## ✨ 프로젝트 완성 상태

FastAPI + MySQL + SQLAlchemy 기반의 완전한 AI 기억 플랫폼 백엔드 프로젝트가 구축되었습니다.

### 구현된 기능

#### 1. 계정 관리 (Auth)
- ✅ 회원가입 (`POST /api/v1/auth/sign-up`)
- ✅ 로그인 (`POST /api/v1/auth/login`)
- ✅ JWT 기반 인증
- ✅ 비밀번호 해싱 (bcrypt)

#### 2. Target 관리 (완전 구현)
- ✅ Target 생성 (`POST /api/v1/targets`)
- ✅ Target 목록 조회 (`GET /api/v1/targets`)
- ✅ Target 상세 조회 (`GET /api/v1/targets/{target_id}`)
- ✅ Target 수정 (`PUT /api/v1/targets/{target_id}`)
- ✅ Target 삭제 (`DELETE /api/v1/targets/{target_id}`)

#### 3. 준비 중인 API
- 📋 Media (사진/음성 업로드)
- 📋 Persona (페르소나 생성/관리)
- 📋 Chat (대화 관리)
- 📋 Interview (AI 인터뷰)
- 📋 StoryBook (스토리북 생성)
- 📋 Sharing (공유 기능)
- 📋 Consent (동의 관리)

---

## 🚀 빠른 시작 가이드

### 1단계: 의존성 설치

```bash
# 가상 환경 활성화
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2단계: 환경 설정

```bash
# .env 파일 생성 (1-2번 중 하나 선택)

# 옵션 A: 예제 파일 복사
cp .env.example .env

# 옵션 B: 직접 생성
cat > .env << EOF
# Database
MYSQL_USER=remory
MYSQL_PASSWORD=your_secure_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=remory_db

# JWT
SECRET_KEY=your-ultra-secure-secret-key-change-this-in-production-12345
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
APP_NAME=Remory API
DEBUG=True
ENVIRONMENT=development

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# File Upload
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=52428800
EOF
```

### 3단계: MySQL 데이터베이스 설정

```bash
# MySQL 서버 실행 (로컬)
# Windows: MySQL 서비스 시작
# Mac: brew services start mysql
# Linux: sudo systemctl start mysql

# 데이터베이스 생성
mysql -u root -p << EOF
CREATE DATABASE remory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'remory'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON remory_db.* TO 'remory'@'localhost';
FLUSH PRIVILEGES;
EXIT
EOF
```

### 4단계: 애플리케이션 실행

```bash
# 개발 서버 시작 (자동 리로드 활성화)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 직접 실행
python app/main.py

# 또는 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5단계: API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🧪 테스트 실행

```bash
# 테스트 패키지 설치 (필요시)
pip install pytest pytest-asyncio httpx

# 전체 테스트 실행
pytest tests/

# 특정 테스트 클래스만 실행
pytest tests/test_api.py::TestAuth

# 특정 테스트만 실행
pytest tests/test_api.py::TestAuth::test_signup

# 상세 출력 옵션
pytest tests/ -v

# 커버리지 확인
pip install pytest-cov
pytest tests/ --cov=app --cov-report=html
```

---

## 📁 프로젝트 파일 구조

```
backend/
├── app/
│   ├── main.py                    # FastAPI 진입점
│   ├── deps.py                    # 의존성 주입
│   │
│   ├── core/
│   │   ├── settings.py            # ⚙️ 환경 설정
│   │   ├── database.py            # 🗄️ MySQL 연결
│   │   └── security.py            # 🔐 JWT & 패스워드
│   │
│   ├── models/                    # 📊 SQLAlchemy ORM 모델
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── target.py
│   │   ├── media.py
│   │   ├── persona.py
│   │   ├── chat.py
│   │   ├── interview.py
│   │   ├── storybook.py
│   │   ├── sharing.py
│   │   ├── consent.py
│   │   └── deletion.py
│   │
│   ├── schemas/                   # ✨ Pydantic 요청/응답 스키마
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── target.py
│   │   ├── media.py
│   │   ├── persona.py
│   │   ├── chat.py
│   │   ├── interview.py
│   │   ├── storybook.py
│   │   ├── sharing.py
│   │   └── consent.py
│   │
│   ├── services/                  # 🧠 비즈니스 로직
│   │   ├── user_service.py
│   │   ├── target_service.py
│   │   ├── file_service.py        # 파일 업로드/삭제
│   │   └── ai_service.py          # Mock AI (실제 API 호출로 확장 가능)
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/         # 🔌 API 엔드포인트
│   │       │   ├── auth.py        # ✅ 완성
│   │       │   ├── target.py      # ✅ 완성
│   │       │   ├── media.py       # 📋 준비 중
│   │       │   ├── persona.py     # 📋 준비 중
│   │       │   ├── chat.py        # 📋 준비 중
│   │       │   ├── interview.py   # 📋 준비 중
│   │       │   ├── storybook.py   # 📋 준비 중
│   │       │   ├── sharing.py     # 📋 준비 중
│   │       │   └── consent.py     # 📋 준비 중
│   │       └── router.py          # 라우터 통합
│   │
│   └── utils/
│       ├── exceptions.py          # 공통 예외 클래스
│       └── constants.py           # 상수
│
├── migrations/                    # 🔄 Alembic 마이그레이션
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── uploads/                       # 📁 파일 저장소
│   ├── images/                    # 업로드된 사진
│   └── voices/                    # 업로드된 음성
│
├── tests/                         # 🧪 테스트
│   ├── conftest.py
│   └── test_api.py
│
├── requirements.txt               # 🔧 Python 의존성
├── .env.example                   # 📝 환경 설정 예시
├── alembic.ini                    # 🔄 Alembic 설정
├── pytest.ini                     # 🧪 pytest 설정
└── README.md                      # 📖 문서
```

---

## 🔌 API 엔드포인트 요약

### 인증 (Auth) - ✅ 완성
```
POST   /api/v1/auth/sign-up           회원가입
POST   /api/v1/auth/login             로그인
POST   /api/v1/auth/refresh-token     토큰 갱신 (준비 중)
```

### Target 관리 - ✅ 완성
```
POST   /api/v1/targets                Target 생성
GET    /api/v1/targets                Target 목록
GET    /api/v1/targets/{id}           Target 상세
PUT    /api/v1/targets/{id}           Target 수정
DELETE /api/v1/targets/{id}           Target 삭제
```

### 기타 API (준비 중)
```
Media:       POST /api/v1/media/upload/image, audio
Persona:     POST /api/v1/personas, GET, PUT
Chat:        POST /api/v1/chats, messages endpoint
Interview:   POST /api/v1/interviews
StoryBook:   POST /api/v1/storybooks
Sharing:     POST /api/v1/share-links, groups
Consent:     POST /api/v1/consent
```

---

## 🛠 개발 워크플로우

### 새로운 API 엔드포인트 추가하기

#### 1. Schema 정의 (`app/schemas/`)
```python
# 예: media.py
class MediaUploadRequest(BaseModel):
    media_type: str
    description: Optional[str] = None

class MediaResponse(TimestampMixin):
    id: int
    file_path: str
    file_size: int
```

#### 2. Service 작성 (`app/services/`)
```python
# 예: media_service.py
class MediaService:
    @staticmethod
    def save_media(db: Session, user_id: int, file_path: str):
        media = TargetMedia(...)
        db.add(media)
        db.commit()
        return media
```

#### 3. Router 구현 (`app/api/v1/endpoints/`)
```python
# 예: media.py
@router.post("/media/upload")
async def upload_media(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 처리 로직
    return MediaResponse(...)
```

#### 4. Router 등록 (`app/api/v1/router.py`)
```python
from app.api.v1.endpoints import media
api_v1_router.include_router(media.router)
```

---

## 🔐 보안 설정

### JWT 토큰
- **알고리즘**: HS256
- **만료 시간**: 30분 (`.env`에서 조정 가능)
- **비밀키**: 프로덕션에서는 강력한 비밀키 필수

### 비밀번호
- **알고리즘**: bcrypt
- **최소 길이**: 8자
- 절대 평문 저장 금지

### CORS
```python
# localhost 개발 환경에서만 허용
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

---

## 🗄 데이터베이스 마이그레이션 (Alembic)

```bash
# 마이그레이션 파일 자동 생성 (모델 변경 감지)
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 적용 (업그레이드)
alembic upgrade head

# 이전 버전으로 롤백
alembic downgrade -1

# 현재 상태 확인
alembic current
```

---

## ⚠️ 주의사항

### 1. 환경 변수 관리
- `.env` 파일은 절대 Git에 커밋하지 말 것
- `.gitignore`에 `.env` 포함됨
- 프로덕션 배포 시 환경 변수 안전하게 관리

### 2. 파일 업로드
- `backend/uploads/images` 및 `backend/uploads/voices` 디렉토리 자동 생성
- 실제 파일은 로컬 저장소 또는 S3로 관리
- DB에는 파일 경로와 메타데이터만 저장

### 3. 데이터 삭제
- 모든 삭제는 논리 삭제 (`is_deleted=True`)
- 실제 파일은 `DeletionRequest` 처리 시 삭제
- 감사 추적(Audit Trail) 기능 지원

### 4. AI 서비스
- `ai_service.py`는 Mock 함수 포함
- 실제 API 호출 시에는 OpenAI, Google TTS 등 통합
- Interface 분리로 쉬운 확장성

---

## 📦 주요 패키지

| 패키지 | 버전 | 용도 |
|--------|------|------|
| fastapi | 0.104.x | Web Framework |
| uvicorn | 0.24.x | ASGI Server |
| sqlalchemy | 2.0.x | ORM |
| alembic | 1.12.x | DB Migration |
| pydantic | 2.5.x | Data Validation |
| python-jose | 3.3.x | JWT Token |
| passlib | 1.7.x | Password Hashing |
| pymysql | 1.1.x | MySQL Driver |
| cryptography | 41.x | Encryption |

---

## 🐛 트러블슈팅

### MySQL 연결 실패
```
문제: "Can't connect to MySQL server"
해결:
1. MySQL 서비스 실행 확인
2. .env 파일의 DB 설정 확인
3. 사용자 권한 확인: GRANT ALL PRIVILEGES ON remory_db.*
```

### 포트 충돌
```
문제: "Address already in use"
해결: python -m uvicorn app.main:app --port 8001
```

### 의존성 오류
```
문제: 모듈 import 오류
해결: pip install --upgrade -r requirements.txt
```

### 테스트 실패
```
문제: pytest 오류
해결:
1. pip install pytest pytest-asyncio
2. pytest tests/ -v (상세 출력)
```

---

## 📚 다음 단계

### 우선순위
1. **Media API** 구현 (이미지/음성 업로드)
2. **Persona API** 구현 (페르소나 생성)
3. **Chat API** 구현 (대화 기능)
4. **AI Service** 통합 (실제 OpenAI API)

### 향후 개선
- [ ] WebSocket 지원 (실시간 대화)
- [ ] S3 연동 (파일 저장소)
- [ ] Redis 캐싱 (성능 향상)
- [ ] GraphQL API (선택적)
- [ ] 실시간 알림 (Notification)
- [ ] 이미지 처리 (Thumbnail, Resize)
- [ ] 중국어/일본어 지원

---

## 📞 지원

문제 발생 시 다음을 확인하세요:
1. `.env` 파일 설정 확인
2. MySQL 서비스 실행 확인
3. Python 버전 확인 (3.12.x)
4. 의존성 재설치 확인
5. 테스트 실행으로 기본 기능 확인

---

**마지막 업데이트**: 2026-05-09
**프로젝트 상태**: 🟢 개발 중 (MVP 기본 구조 완성)

