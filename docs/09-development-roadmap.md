# 09. Development Roadmap

## 목차

- [현재 상태](#현재-상태)
- [구현 완료](#구현-완료)
- [운영 전 점검](#운영-전-점검)
- [향후 작업](#향후-작업)
- [개발 규칙](#개발-규칙)

## 현재 상태

이 문서는 실제 코드 기준의 상태만 기록한다. API 상세는 [02-backend-api.md](02-backend-api.md), 설정은 [01-setup.md](01-setup.md)를 기준으로 한다.

현재 구현은 FastAPI REST API, WebSocket voice API, SQLAlchemy 모델, Alembic migration, pytest 테스트를 포함한다. AI/STT/TTS/Voice Clone provider는 기본값이 `mock`이며, Gemini key/model은 환경변수로 설정한다.

## 구현 완료

| 영역 | 완료 항목 |
| --- | --- |
| Auth/User | register, sign-up alias, login, me, refresh-token, logout, user role |
| Target/Media | target CRUD, media upload/list/delete |
| Consent/Verification | consent log, revoke, target verification request, admin review |
| Persona | persona 생성/상세/상태, voice profile 생성/평가/user confirm/admin review |
| Chat | persona chat, text message, audio message, message 목록 |
| Interview | session, question, answer |
| Photo Memory | multipart photo memory 생성, 목록, 상세, 삭제 |
| StoryBook | 생성, 목록, 상세, chapters, regenerate |
| Sharing/Group | share link, public share, group/member/storybook |
| Deletion | deletion request, cancel, admin approve/reject |
| Report/Audit | user report, admin report workflow, audit log |
| Usage/Rate Limit | usage limits, persona usage limits, rate limit events |
| Realtime Voice | WebSocket protocol, STT/LLM/TTS/voice clone flow, call session |
| Testing | API/service pytest suite |

## 운영 전 점검

| 항목 | 확인 |
| --- | --- |
| `.env` | `.env.example`과 key 동기화, extra key 제거 |
| 보안 | `SECRET_KEY` 교체, `DEBUG=False`, CORS 운영 origin 제한 |
| DB | `alembic current`, `alembic upgrade head` 성공 |
| 파일 | `uploads/*` 생성 및 쓰기 권한 |
| API | `/health`, `/docs`, 주요 auth/target/persona flow |
| WebSocket | Nginx upgrade 설정과 token query 인증 |
| 테스트 | `pytest` 또는 변경 범위 테스트 통과 |

## 향후 작업

코드에 이미 존재하는 확장 지점:

- `STT_PROVIDER`, `TTS_PROVIDER`, `VOICE_CLONE_PROVIDER`의 mock 외 실제 provider 운영 검증
- `GEMINI_API_KEY`, `GEMINI_MODEL` 운영 모델/쿼터 관리
- admin dashboard에서 verification, deletion, report, usage limit UI 연결
- upload storage를 local filesystem에서 object storage로 이전하는 경우 file path/url 정책 정리
- WebSocket 음성 chunk capture/playback UX와 retry 정책 정리
- pydantic settings extra key를 CI에서 검출하는 문서/스크립트 검증 추가

## 개발 규칙

- API 문서는 `app/api/v1/endpoints`, `app/schemas`, `tests` 변경과 함께 갱신한다.
- 환경변수는 `app/core/settings.py::Settings`에 추가한 뒤 `.env.example`, [01-setup.md](01-setup.md), [08-deployment.md](08-deployment.md)를 함께 갱신한다.
- migration이 필요한 모델 변경은 Alembic revision을 추가하고 배포 문서의 migration 순서를 지킨다.
- response shape는 FastAPI `response_model` 기준으로 문서화한다.
- 존재하지 않는 API, field, 환경변수를 문서에 추가하지 않는다.
