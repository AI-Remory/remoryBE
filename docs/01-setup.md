# 01. Setup

## 목차

- [목표](#목표)
- [로컬 개발 환경](#로컬-개발-환경)
- [환경 변수](#환경-변수)
- [.env 동기화 확인](#env-동기화-확인)
- [MySQL](#mysql)
- [Alembic](#alembic)
- [Uploads](#uploads)
- [서버 실행](#서버-실행)
- [Pytest](#pytest)
- [자주 나는 오류](#자주-나는-오류)

## 목표

Remory 백엔드를 로컬에서 실행하고 테스트하기 위한 절차다. API 상세는 [02-backend-api.md](02-backend-api.md), 배포는 [08-deployment.md](08-deployment.md)를 기준으로 한다.

## 로컬 개발 환경

| 항목 | 기준 |
| --- | --- |
| Python | 3.12 권장. 현재 로컬 venv는 `python3.12` 구조다. |
| 패키지 | `requirements.txt` |
| DB | MySQL + PyMySQL |
| 실행 앱 | `app.main:app` |
| 테스트 DB | pytest fixture의 SQLite in-memory |

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 환경 변수

`.env`는 `.env.example`을 복사해서 만든다. `app/core/settings.py::Settings`에 없는 키가 `.env`에 있으면 pydantic-settings가 `ValidationError: Extra inputs are not permitted`를 발생시킨다.

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `APP_NAME` | `Remory API` | FastAPI title |
| `DEBUG` | `True` | local reload/debug 기준. 운영은 `False` |
| `ENVIRONMENT` | `development` | 환경 구분 문자열 |
| `MYSQL_USER` | `remory` | MySQL 사용자 |
| `MYSQL_PASSWORD` | `password` | MySQL 비밀번호 |
| `MYSQL_HOST` | `localhost` | MySQL host |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_DB` | `remory_db` | MySQL database |
| `SECRET_KEY` | 개발용 문자열 | JWT 서명 키. 운영 필수 교체 |
| `ALGORITHM` | `HS256` | JWT 알고리즘 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | access token 만료 분 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | refresh token 만료 일 |
| `CORS_ORIGINS` | localhost 5173/3000 | JSON 배열 문자열 |
| `GEMINI_API_KEY` | 빈 문자열 | Gemini API key |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model |
| `STT_PROVIDER` | `mock` | STT provider |
| `WHISPER_MODEL_SIZE` | `base` | whisper model size |
| `TTS_PROVIDER` | `mock` | TTS provider |
| `VOICE_CLONE_PROVIDER` | `mock` | voice clone provider |
| `OPENVOICE_CHECKPOINT_PATH` | 빈 문자열 | OpenVoice checkpoint path |
| `VOICE_SAMPLE_MIN_COUNT` | `1` | voice profile 최소 샘플 수 |
| `VOICE_SAMPLE_MIN_TOTAL_DURATION_MS` | `100` | voice profile 최소 총 길이 |
| `VOICE_SAMPLE_MIN_FILE_SIZE_BYTES` | `1024` | voice sample 최소 파일 크기 |
| `VOICE_PROFILE_MIN_QUALITY_SCORE` | `0.5` | voice profile 최소 품질 점수 |
| `UPLOAD_DIR` | `./uploads` | 업로드 루트 |
| `MAX_UPLOAD_SIZE` | `52428800` | 파일 최대 크기, 50MB |
| `MONTHLY_USER_VOICE_GENERATION_LIMIT` | `1000` | 사용자 월 음성 생성 한도 |
| `MONTHLY_PERSONA_VOICE_GENERATION_LIMIT` | `500` | persona 월 음성 생성 한도 |
| `MONTHLY_USER_STT_REQUEST_LIMIT` | `500` | 사용자 월 STT 요청 한도 |
| `MONTHLY_USER_VOICE_CALL_SECONDS_LIMIT` | `3600` | 사용자 월 음성 통화 초 |
| `RATE_LIMIT_REQUESTS_PER_MINUTE_DEFAULT` | `60` | 일반 endpoint 분당 요청 제한 |
| `RATE_LIMIT_REQUESTS_PER_MINUTE_VOICE` | `10` | 음성 endpoint 분당 요청 제한 |
| `VOICE_WS_MAX_ACTIVE_CONNECTIONS_PER_USER` | `2` | 사용자별 WebSocket 동시 연결 |
| `VOICE_WS_MAX_UTTERANCES_PER_MINUTE` | `20` | WebSocket 분당 utterance |
| `VOICE_WS_MAX_CHUNK_BYTES` | `262144` | WebSocket chunk 최대 bytes |
| `VOICE_WS_MAX_CHUNKS_PER_UTTERANCE` | `100` | utterance당 chunk 수 |

`RATE_LIMIT_PER_MINUTE_DEFAULT`, `RATE_LIMIT_PER_MINUTE_VOICE`는 현재 `Settings`에 없는 키이므로 `.env`에 넣지 않는다.

## .env 동기화 확인

Linux/macOS:

```bash
grep -E "^[A-Z_]+=" .env.example | cut -d= -f1 | sort > /tmp/env_example_keys.txt
grep -E "^[A-Z_]+=" .env | cut -d= -f1 | sort > /tmp/env_keys.txt
comm -23 /tmp/env_example_keys.txt /tmp/env_keys.txt
comm -13 /tmp/env_example_keys.txt /tmp/env_keys.txt
```

첫 번째 `comm`은 `.env.example`에는 있지만 `.env`에는 없는 키, 두 번째 `comm`은 `.env`에만 있는 키다. 두 번째 출력이 있으면 Alembic/FastAPI 시작 전에 제거한다.

PowerShell:

```powershell
$example = Select-String -Path .env.example -Pattern '^[A-Z_]+=' | ForEach-Object { ($_ -split '=')[0] } | Sort-Object
$envKeys = Select-String -Path .env -Pattern '^[A-Z_]+=' | ForEach-Object { ($_ -split '=')[0] } | Sort-Object
Compare-Object $example $envKeys
```

## MySQL

```sql
CREATE DATABASE remory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'remory'@'%' IDENTIFIED BY 'change-me';
GRANT ALL PRIVILEGES ON remory_db.* TO 'remory'@'%';
FLUSH PRIVILEGES;
```

`app/core/settings.py`의 `DATABASE_URL`은 다음 형태로 생성된다.

```text
mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4
```

## Alembic

```bash
alembic current
alembic upgrade head
```

마이그레이션 파일은 `migrations/versions`에 있다. 로컬 초기화 시 새 migration을 만들지 말고 기존 revision을 적용한다.

## Uploads

테스트 fixture와 서비스가 사용하는 업로드 하위 디렉터리를 미리 만든다.

```bash
mkdir -p uploads/images uploads/voices uploads/photo_memories uploads/verifications uploads/chat_audio uploads/chat_tts
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force uploads\images, uploads\voices, uploads\photo_memories, uploads\verifications, uploads\chat_audio, uploads\chat_tts
```

## 서버 실행

```bash
uvicorn app.main:app --reload
```

기본 확인:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Pytest

```bash
pytest
```

테스트는 `tests/conftest.py`에서 FastAPI dependency를 SQLite in-memory DB로 override한다. 실제 MySQL 연결 없이 API 테스트를 실행한다.

## 자주 나는 오류

### pydantic Settings ValidationError

원인: `.env`에 `Settings`가 모르는 키가 있다. 예: `RATE_LIMIT_PER_MINUTE_DEFAULT`, `RATE_LIMIT_PER_MINUTE_VOICE`.

해결:

```bash
grep -E "^[A-Z_]+=" .env.example | cut -d= -f1 | sort > /tmp/env_example_keys.txt
grep -E "^[A-Z_]+=" .env | cut -d= -f1 | sort > /tmp/env_keys.txt
comm -13 /tmp/env_example_keys.txt /tmp/env_keys.txt
```

출력된 키를 `.env`에서 제거하고 다시 `alembic current`를 실행한다.

### MySQL 연결 실패

`.env`의 `MYSQL_*` 값, MySQL 계정 권한, DB 생성 여부를 확인한다.

### CORS 오류

프론트 origin을 `CORS_ORIGINS` JSON 배열 문자열에 추가한다. 예: `["https://app.example.com"]`.

### 업로드 실패

`UPLOAD_DIR` 하위 디렉터리가 존재하고 서버 프로세스가 쓸 수 있는지 확인한다.

### 401 Unauthorized

`Authorization: Bearer <access_token>` 헤더가 누락되었거나 access token이 만료된 상태다. `/api/v1/auth/refresh-token`으로 token pair를 갱신한다.
