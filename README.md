# Remory Backend

AI 기억 플랫폼의 FastAPI 백엔드 서비스입니다.

## 기능

사용자가 특정 대상(target)의 음성, 사진, 기억 데이터를 업로드하여 AI 기반 가상 페르소나를 만들고, 그 페르소나와 대화하며 스토리북을 생성·공유하는 서비스입니다.

### 핵심 기능

- **User**: 서비스 사용자 계정 관리 (회원가입, 로그인, JWT 인증)
- **Target**: 가상 페르소나 대상 프로필 생성 및 관리
- **Media**: 사진/음성 파일 업로드 및 메타데이터 관리
- **Persona**: Target 기반 가상 페르소나 프로필 생성
- **Chat**: 페르소나와의 텍스트/음성 대화
- **Interview**: AI 인터뷰 세션으로 정보 수집
- **StoryBook**: 대화/사진/인터뷰를 바탕으로 스토리북 생성
- **Sharing**: 개인/그룹 공유 기능
- **Consent**: 음성/사진/페르소나 생성 동의 관리

## 기술 스택

- **Framework**: FastAPI 0.104.x
- **Python**: 3.12.x
- **Database**: MySQL
- **ORM**: SQLAlchemy 2.x
- **Migration**: Alembic
- **Auth**: JWT (python-jose)
- **Password**: bcrypt (passlib)

## 프로젝트 구조

```
backend/
├── app/
│   ├── main.py                 # FastAPI 진입점
│   ├── deps.py                 # 의존성 주입
│   ├── core/
│   │   ├── settings.py         # 환경 설정
│   │   ├── database.py         # DB 연결
│   │   └── security.py         # JWT/패스워드
│   ├── models/                 # SQLAlchemy 모델
│   ├── schemas/                # Pydantic 스키마
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/      # API 엔드포인트
│   │       └── router.py       # 라우터 통합
│   ├── services/               # 비즈니스 로직
│   └── utils/                  # 유틸리티
├── migrations/                 # Alembic 마이그레이션
├── uploads/                    # 파일 저장소
│   ├── images/
│   └── voices/
├── tests/                      # 테스트
├── requirements.txt            # 의존성
├── .env.example               # 환경 설정 예시
└── README.md
```

## 설치 및 실행

### 1. 환경 설정

```bash
# 가상 환경 생성
python -m venv .venv

# 가상 환경 활성화 (Windows)
.venv\Scripts\activate

# 가상 환경 활성화 (Mac/Linux)
source .venv/bin/activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env.example 을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일 수정 (MySQL 정보, JWT 키 등)
```

### 4. 데이터베이스 설정

```bash
# MySQL 데이터베이스 생성
mysql -u root -p -e "CREATE DATABASE remory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Alembic 마이그레이션 (필요시)
alembic upgrade head
```

### 5. 앱 실행

```bash
# 개발 서버 실행
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python app/main.py
```

서버는 `http://localhost:8000` 에서 실행됩니다.

### 6. API 문서

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 테스트 실행

```bash
# pytest 설치
pip install pytest pytest-asyncio

# 테스트 실행
pytest tests/

# 특정 테스트 실행
pytest tests/test_api.py::TestAuth::test_signup
```

## API 엔드포인트

### 인증 (Auth)
- `POST /api/v1/auth/sign-up` - 회원가입
- `POST /api/v1/auth/login` - 로그인
- `POST /api/v1/auth/refresh-token` - 토큰 갱신

### Target Management
- `POST /api/v1/targets` - Target 생성
- `GET /api/v1/targets` - Target 목록 조회
- `GET /api/v1/targets/{target_id}` - Target 상세 조회
- `PUT /api/v1/targets/{target_id}` - Target 수정
- `DELETE /api/v1/targets/{target_id}` - Target 삭제

### Media (준비 중)
- `POST /api/v1/media/upload/image` - 이미지 업로드
- `POST /api/v1/media/upload/audio` - 음성 업로드
- `GET /api/v1/media/{media_id}` - 미디어 조회
- `DELETE /api/v1/media/{media_id}` - 미디어 삭제

### Persona (준비 중)
- `POST /api/v1/personas` - Persona 생성
- `GET /api/v1/personas/{persona_id}` - Persona 조회
- `PUT /api/v1/personas/{persona_id}` - Persona 수정

### Chat (준비 중)
- `POST /api/v1/chats` - 대화방 생성
- `POST /api/v1/chats/{chat_id}/messages` - 메시지 전송
- `GET /api/v1/chats/{chat_id}/messages` - 메시지 목록 조회

### 기타 API는 순차적으로 추가될 예정입니다.

## 코드 규칙

### 아키텍처
- **Router**: HTTP 요청/응답 처리만 담당
- **Service**: 비즈니스 로직 담당
- **Model**: SQLAlchemy ORM 모델
- **Schema**: Pydantic 요청/응답 스키마

### 파일 업로드
- 이미지: `backend/uploads/images/`
- 음성: `backend/uploads/voices/`
- DB에는 파일 경로와 메타데이터만 저장

### 예외 처리
- `RemoryException` 상속 구조 사용
- `to_http_exception()` 으로 변환하여 반환

### 데이터 삭제
- 실제 삭제가 아닌 논리 삭제 (`is_deleted=True`) 사용
- 삭제 요청 내역 기록

## Environment Variables

```env
# Database
MYSQL_USER=remory
MYSQL_PASSWORD=your_secure_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=remory_db

# JWT
SECRET_KEY=your-super-secret-key-change-this-in-production
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
```

## 다음 개발 일정

- [ ] Media API (이미지/음성 업로드)
- [ ] Persona API (페르소나 생성/조회)
- [ ] Chat API (대화 관리)
- [ ] Interview API (AI 인터뷰)
- [ ] StoryBook API (스토리북 생성)
- [ ] Sharing API (공유 기능)
- [ ] Consent API (동의 관리)
- [ ] AI 서비스 통합 (OpenAI, TTS 등)
- [ ] 파일 업로드 최적화 (S3 연동)
- [ ] 실시간 WebSocket 지원

## 문제 해결 (Troubleshooting)

### MySQL 연결 실패
- MySQL 서버 실행 확인
- `.env` 파일의 DB 설정 확인
- 데이터베이스 생성 여부 확인

### 포트 이미 사용 중
- 다른 포트 사용: `--port 8001`
- 기존 프로세스 종료

### 마이그레이션 오류
- Alembic 버전 확인
- 마이그레이션 디렉토리 권한 확인
- `alembic current` 로 현재 상태 확인

## 라이선스

아직 미정

## 기여

개발 단계이므로 후에 업데이트 예정입니다.

---

## AI / Speech Pipeline Setup

This backend includes AI and voice service interfaces for Gemini LLM, STT, TTS, and voice cloning.
Frontend developers can use the API contracts without installing heavy local models when mock providers are enabled.

### Install

Run Python commands from the backend virtual environment:

```powershell
cd D:\IdeaProjects\remory\backend
.\.venv\Scripts\activate
pip install -r requirements.txt
```

The dependency file includes:

- `google-genai` for Gemini.
- `faster-whisper` for real STT.
- MeloTTS/OpenVoice integrations are optional and lazy-loaded so the server can run without them.

GPU is not required. faster-whisper should run in CPU mode for local development.

### Environment Variables

Add AI and voice settings to `.env`. Real external API keys must stay in `.env` only. Do not commit them to GitHub.

```env
# Gemini LLM
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

# Speech-to-text
STT_PROVIDER=mock
WHISPER_MODEL_SIZE=base

# Text-to-speech
TTS_PROVIDER=mock

# Voice cloning
VOICE_CLONE_PROVIDER=mock
```

Provider options:

| Variable | Values | Default local choice |
| --- | --- | --- |
| `STT_PROVIDER` | `mock`, `faster_whisper` | `mock` |
| `WHISPER_MODEL_SIZE` | `base`, `small` | `base` |
| `TTS_PROVIDER` | `mock`, `melotts` | `mock` |
| `VOICE_CLONE_PROVIDER` | `mock`, `openvoice` | `mock` |

`ENVIRONMENT=test` always forces mock providers. Tests should never require Gemini keys, faster-whisper model loading, MeloTTS, or OpenVoice.

### Gemini Behavior

Gemini is used by `GeminiLLMService` for:

- PersonaChat persona replies.
- AI interview question generation.
- StoryBook and StoryChapter generation.

Fallback behavior:

- If `ENVIRONMENT=test`, mock LLM output is used.
- If `GEMINI_API_KEY` is empty, mock LLM output is used.
- If Gemini fails, the backend falls back to mock output.
- StoryBook generation asks Gemini for JSON and falls back to mock storybook content if JSON parsing fails.

### PersonaChat Text and Audio Flow

Text message:

- Endpoint: `POST /api/v1/chats/{chat_id}/messages`
- Body can include `generate_audio: true`.
- The backend saves the user text, generates a persona reply through LLM, and optionally creates persona reply audio through TTS.
- Persona replies keep `is_ai_generated=true`.

Audio message:

- Endpoint: `POST /api/v1/chats/{chat_id}/audio`
- Content-Type: `multipart/form-data`
- Fields:
  - `file`: required audio file. MIME type must start with `audio/`.
  - `generate_audio`: optional boolean.
- The backend stores the upload under `uploads/chat_audio/{user_id}/`, transcribes it with STT, saves the user message as `message_type=AUDIO`, then generates the persona reply.

### StoryBook Flow

StoryBook create and regenerate endpoints call the same LLM storybook generation path:

- `POST /api/v1/storybooks`
- `POST /api/v1/storybooks/{storybook_id}/regenerate`

Gemini receives interview question/answer data and optional photo memory data. The expected internal generation shape is:

```json
{
  "title": "...",
  "summary": "...",
  "chapters": [
    {
      "title": "...",
      "summary": "...",
      "content": "..."
    }
  ]
}
```

The public response schema remains the API schema used by the existing StoryBook endpoints.

### Voice Profile API

Voice cloning MVP endpoints:

- `POST /api/v1/personas/{persona_id}/voice-profile`
- `GET /api/v1/personas/{persona_id}/voice-profile`

Rules:

- The logged-in user must own the persona.
- The persona target must have reference voice media.
- If no reference voice media exists, creation returns `400`.
- In test/mock mode, profile creation immediately returns a `READY` profile.
- Real OpenVoice execution is optional. Service-layer TODO checks remain for target verification approval and explicit voice cloning consent.

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/personas/{persona_id}/voice-profile" \
  -H "Authorization: Bearer <access_token>"
```

### Useful Commands

```powershell
cd D:\IdeaProjects\remory\backend
.\.venv\Scripts\activate
pytest -v
pytest tests/test_05_chat.py -v
pytest tests/test_08_storybook.py -v
```
