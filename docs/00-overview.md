# 00. Overview

## 목차

- [서비스 개요](#서비스-개요)
- [현재 백엔드 구조](#현재-백엔드-구조)
- [주요 도메인](#주요-도메인)
- [대표 사용자 흐름](#대표-사용자-흐름)
- [문서 구조](#문서-구조)

## 서비스 개요

Remory 백엔드는 사용자의 기억 자료를 저장하고, 대상자(Target)에 대한 검증/동의를 거쳐 AI persona, 대화, 음성 프로필, 사진 기억, 스토리북, 공유 기능을 제공한다.

현재 구현은 FastAPI `/api/v1` REST API와 `/api/v1/ws/personas/{persona_id}/voice` WebSocket을 제공한다. API 계약은 `app/api/v1/endpoints`, `app/schemas`, `tests`를 기준으로 한다.

## 현재 백엔드 구조

```text
app/
  api/v1/endpoints/       # FastAPI routers
  core/                   # settings, database, security
  models/                 # SQLAlchemy models
  schemas/                # Pydantic request/response schemas
  services/               # business logic
  utils/                  # exceptions/constants
migrations/versions/      # Alembic revisions
tests/                    # API/service tests
uploads/                  # local uploaded files
```

## 주요 도메인

| 도메인 | 실제 구현 |
| --- | --- |
| Auth/User | 회원가입, 로그인, refresh token rotation, logout, `/me` |
| Target | 대상자 CRUD, 상세 조회, soft delete |
| Consent | 동의 로그 생성/조회/철회 |
| Verification | target 검증 요청 생성/조회, admin 승인/거절/추가정보/철회 |
| Media | target 이미지/음성 업로드, 목록, 삭제 |
| Persona | persona 생성/상태/상세, voice profile 생성/평가/확인 |
| Chat | persona chat 생성, text/audio message, message 목록 |
| Interview | AI interview session/question/answer |
| Photo Memory | 사진 기억 업로드/조회/삭제 |
| StoryBook | 생성, 목록, 상세, chapter, regenerate |
| Sharing/Group | share link, public share, memory group, group member/storybook |
| Deletion | 사용자 삭제 요청, admin 처리 |
| Report/Audit | 신고, admin 신고 처리, audit log |
| Usage/Rate Limit | 월 사용량, rate limit event, admin 한도 변경 |
| Realtime Voice | 인증된 WebSocket 음성 대화 |

## 대표 사용자 흐름

1. `POST /api/v1/auth/register` 또는 `POST /api/v1/auth/login`으로 token pair를 받는다.
2. `POST /api/v1/targets`로 대상자를 생성한다.
3. 필요한 consent를 `POST /api/v1/consents`로 기록한다.
4. `POST /api/v1/targets/{target_id}/media`로 사진/음성을 업로드한다.
5. `POST /api/v1/targets/{target_id}/verification-requests`로 검증 요청을 제출한다.
6. admin이 `/api/v1/admin/verification-requests/{request_id}/approve`로 승인한다.
7. `POST /api/v1/targets/{target_id}/persona`로 persona를 만든다.
8. `/api/v1/personas/{persona_id}/chats`, `/api/v1/chats/{chat_id}/messages`, WebSocket 음성 대화를 사용한다.
9. interview/photo memory를 기반으로 storybook을 만들고 share link 또는 group으로 공유한다.

## 문서 구조

| 문서 | 내용 |
| --- | --- |
| [01-setup.md](01-setup.md) | 로컬 개발 환경과 `.env` |
| [02-backend-api.md](02-backend-api.md) | API 명세와 response shape |
| [03-frontend-integration.md](03-frontend-integration.md) | 프론트 연동 기준 |
| [04-auth-and-permission.md](04-auth-and-permission.md) | 인증/권한 |
| [05-verification-consent-flow.md](05-verification-consent-flow.md) | 검증/동의 흐름 |
| [06-realtime-voice-chat.md](06-realtime-voice-chat.md) | WebSocket 음성 대화 |
| [07-test-scenario.md](07-test-scenario.md) | 테스트 실행과 시나리오 |
| [08-deployment.md](08-deployment.md) | 배포 |
| [09-development-roadmap.md](09-development-roadmap.md) | 구현 상태와 로드맵 |
