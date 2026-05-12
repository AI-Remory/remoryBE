# Remory Backend

Remory는 사용자의 기억 자료를 기반으로 대상자 프로필, AI 페르소나, 대화, 사진 기억, 스토리북, 공유, 음성 대화를 제공하는 FastAPI 백엔드입니다.

## 핵심 기능

- JWT 회원가입, 로그인, refresh token rotation, logout
- Target, media upload, verification request, consent log
- Persona 생성, chat/message, voice profile 생성/검수, realtime voice WebSocket
- AI interview, photo memory, storybook, share link, memory group
- deletion request, report, audit log, usage limit/rate limit admin API

## 기술 스택

| 영역 | 사용 기술 |
| --- | --- |
| API | FastAPI, Pydantic v2 |
| DB | SQLAlchemy, Alembic, MySQL(PyMySQL) |
| Auth | JWT, passlib/bcrypt |
| File | python-multipart, aiofiles, local uploads |
| AI/Speech | google-genai, mock STT/TTS/Voice Clone 기본값 |
| Test | pytest, FastAPI TestClient, SQLite in-memory |

## 빠른 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p uploads/images uploads/voices uploads/photo_memories uploads/verifications uploads/chat_audio uploads/chat_tts
alembic upgrade head
uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
New-Item -ItemType Directory -Force uploads\images, uploads\voices, uploads\photo_memories, uploads\verifications, uploads\chat_audio, uploads\chat_tts
alembic upgrade head
uvicorn app.main:app --reload
```

API 상세는 [docs/02-backend-api.md](docs/02-backend-api.md), 운영/배포는 [docs/08-deployment.md](docs/08-deployment.md)를 기준으로 봅니다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [00-overview.md](docs/00-overview.md) | 서비스 개요와 도메인 흐름 |
| [01-setup.md](docs/01-setup.md) | 로컬 개발, 환경변수, MySQL, Alembic, pytest |
| [02-backend-api.md](docs/02-backend-api.md) | 실제 `/api/v1` API 명세와 response shape |
| [03-frontend-integration.md](docs/03-frontend-integration.md) | 프론트 연동 규칙, 업로드, 에러 처리 |
| [04-auth-and-permission.md](docs/04-auth-and-permission.md) | JWT, USER/ADMIN, owner-only 접근 |
| [05-verification-consent-flow.md](docs/05-verification-consent-flow.md) | 검증, 동의, persona/voice gate |
| [06-realtime-voice-chat.md](docs/06-realtime-voice-chat.md) | WebSocket 음성 대화 프로토콜 |
| [07-test-scenario.md](docs/07-test-scenario.md) | 테스트 실행과 검증 시나리오 |
| [08-deployment.md](docs/08-deployment.md) | Ubuntu/systemd/Nginx 배포 |
| [09-development-roadmap.md](docs/09-development-roadmap.md) | 현재 구현 상태와 향후 작업 |
