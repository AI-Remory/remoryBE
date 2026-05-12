# Remory Backend

Remory is a FastAPI backend for preserving memories as AI personas, chats, storybooks, and voice interactions.

## Core Features

- User authentication with JWT access and refresh tokens
- Target profiles with media upload, verification, and consent gates
- AI persona generation, persona chat, interview, photo memory, and storybook flows
- Share links, memory groups, deletion requests, audit logs, reports, and admin review tools
- Gemini-backed LLM flow with mock fallback, STT/TTS/voice clone services, and Remory WebSocket voice chat

## Tech Stack

- Python 3.12
- FastAPI, Uvicorn
- SQLAlchemy, Alembic
- MySQL
- Pytest
- Gemini, faster-whisper, MeloTTS, OpenVoice-ready service interfaces with mock defaults

## Quick Start

```powershell
cd D:\IdeaProjects\remory\backend
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest -v
```

Swagger UI: `http://localhost:8000/docs`

## Documentation

| Document | Purpose |
| --- | --- |
| [00-overview.md](docs/00-overview.md) | Service concept, domains, and user flow |
| [01-setup.md](docs/01-setup.md) | Local setup, `.env`, MySQL, Alembic, pytest, troubleshooting |
| [02-backend-api.md](docs/02-backend-api.md) | Backend API reference for `/api/v1` |
| [03-frontend-integration.md](docs/03-frontend-integration.md) | Frontend API usage, uploads, screen flow, errors |
| [04-auth-and-permission.md](docs/04-auth-and-permission.md) | JWT, roles, owner-only and admin-only rules |
| [05-verification-consent-flow.md](docs/05-verification-consent-flow.md) | Verification, consent, persona, and voice cloning gates |
| [06-realtime-voice-chat.md](docs/06-realtime-voice-chat.md) | WebSocket voice chat protocol and flow |
| [07-test-scenario.md](docs/07-test-scenario.md) | Pytest, API test order, demo scenario, GitHub Actions |
| [08-deployment.md](docs/08-deployment.md) | Vultr/Ubuntu deployment, systemd, Nginx, CORS |
| [09-development-roadmap.md](docs/09-development-roadmap.md) | Completed, in-progress, and planned work |
