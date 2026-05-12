# 01. Setup

## 목차

- [목표](#목표)
- [로컬 개발 환경](#로컬-개발-환경)
- [환경 변수](#환경-변수)
- [MySQL](#mysql)
- [Alembic](#alembic)
- [서버 실행](#서버-실행)
- [Pytest](#pytest)
- [AI/Speech 설정](#aispeech-설정)
- [자주 나는 오류](#자주-나는-오류)

## 목표

이 문서는 Remory 백엔드를 로컬에서 실행하고 테스트하기 위한 설정 절차를 정리한다. API 상세는 [02-backend-api.md](02-backend-api.md), 프론트 연동은 [03-frontend-integration.md](03-frontend-integration.md)를 본다.

## 로컬 개발 환경

권장 환경:

- Python 3.12
- MySQL 8.x
- Windows PowerShell 또는 Linux/macOS shell
- FastAPI 개발 서버: Uvicorn

설치:

```powershell
cd D:\IdeaProjects\remory\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
cd /path/to/remory/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 환경 변수

`.env.example`을 복사해 `.env`를 만든다.

```powershell
copy .env.example .env
```

핵심 설정:

```env
APP_NAME=Remory API
DEBUG=True
ENVIRONMENT=development

MYSQL_USER=remory
MYSQL_PASSWORD=password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=remory_db

SECRET_KEY=change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=52428800

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
STT_PROVIDER=mock
WHISPER_MODEL_SIZE=base
TTS_PROVIDER=mock
VOICE_CLONE_PROVIDER=mock
```

주의:

- `.env`는 커밋하지 않는다.
- 실제 Gemini 키, 운영 JWT secret, DB 비밀번호는 `.env` 또는 서버 secret으로만 관리한다.
- 테스트 환경에서는 `ENVIRONMENT=test`가 mock LLM/STT/TTS/VoiceClone을 강제한다.

## MySQL

로컬 MySQL 실행 후 데이터베이스와 사용자를 만든다.

```sql
CREATE DATABASE remory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'remory'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON remory_db.* TO 'remory'@'localhost';
FLUSH PRIVILEGES;
```

Windows에서 MySQL 서비스가 내려가 있으면 서비스 앱 또는 PowerShell에서 MySQL 서비스를 시작한다. Linux에서는 일반적으로 다음 명령을 사용한다.

```bash
sudo systemctl start mysql
```

## Alembic

마이그레이션 적용:

```powershell
alembic upgrade head
```

상태 확인:

```powershell
alembic current
alembic heads
```

모델 변경 시:

```powershell
alembic revision --autogenerate -m "describe schema change"
alembic upgrade head
```

마이그레이션 파일은 `migrations/versions/`에 생성되며 코드 변경과 함께 커밋해야 한다.

## 서버 실행

개발 서버:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

대체 실행:

```powershell
python app/main.py
```

확인:

- Health: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Pytest

전체 테스트:

```powershell
pytest -v
```

일부 테스트:

```powershell
pytest tests/test_05_chat.py -v
pytest tests/test_19_realtime_voice.py -v
```

테스트는 FastAPI `TestClient`, in-memory SQLite, mock AI/Speech 서비스를 사용한다. 테스트 전후로 `uploads/images`, `uploads/voices`, `uploads/photo_memories`, `uploads/verifications`, `uploads/chat_audio`, `uploads/chat_tts` 산출물을 정리한다.

## AI/Speech 설정

로컬 개발 기본값은 mock provider다.

| Variable | Values | Local default |
| --- | --- | --- |
| `GEMINI_API_KEY` | Gemini API key | empty means mock LLM |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.0-flash` |
| `STT_PROVIDER` | `mock`, `faster_whisper` | `mock` |
| `TTS_PROVIDER` | `mock`, `melotts` | `mock` |
| `VOICE_CLONE_PROVIDER` | `mock`, `openvoice` | `mock` |

MeloTTS/OpenVoice/faster-whisper는 lazy import와 fallback을 사용한다. 모델이나 패키지가 없어도 서버 시작이 실패하지 않아야 한다.

## 자주 나는 오류

### MySQL 연결 실패

- MySQL 서버가 실행 중인지 확인한다.
- `.env`의 `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`를 확인한다.
- DB와 사용자 권한이 생성됐는지 확인한다.

### 포트 충돌

```powershell
python -m uvicorn app.main:app --reload --port 8001
```

### 모듈 import 오류

```powershell
.\.venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

### Alembic 오류

- `alembic heads`가 하나인지 확인한다.
- DB 접속 권한을 확인한다.
- 모델만 바꾸고 migration을 누락하지 않았는지 확인한다.

### Pytest 실패

- 가상환경이 활성화됐는지 확인한다.
- `pytest -v`로 상세 로그를 본다.
- 실패가 업로드 파일 잔여물 때문이면 `uploads/` 하위 테스트 산출물을 정리한다.
