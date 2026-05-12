# 09. Development Roadmap

## 목차

- [현재 상태](#현재-상태)
- [완료 작업](#완료-작업)
- [진행 작업](#진행-작업)
- [예정 작업](#예정-작업)
- [실서비스 확장 TODO](#실서비스-확장-todo)
- [음성 기능 TODO](#음성-기능-todo)
- [보안/운영 TODO](#보안운영-todo)
- [개발 규칙](#개발-규칙)

## 현재 상태

Remory backend는 MVP 핵심 도메인을 대부분 갖춘 상태다.

- FastAPI app/router/service/model/schema 구조
- JWT 인증과 USER/ADMIN role
- Target, Media, Consent, Verification, Persona
- PersonaChat, audio upload, STT/TTS mock flow
- Interview, PhotoMemory, StoryBook
- ShareLink, MemoryGroup
- DeletionRequest, AuditLog, Report
- UsageLimit, RateLimitEvent
- PersonaVoiceProfile quality/review flow
- Realtime voice WebSocket MVP
- Alembic migration과 pytest suite

## 완료 작업

### Auth/User

- 회원가입: `POST /api/v1/auth/register`
- sign-up alias: `POST /api/v1/auth/sign-up`
- 로그인: `POST /api/v1/auth/login`
- refresh token
- logout blacklist
- `GET /api/v1/auth/me`
- password hashing
- JWT access/refresh token
- admin role

### Target/Media

- Target CRUD
- owner-only 접근
- image/voice upload
- local `uploads/` 저장
- MIME type validation
- media delete

### Consent/Verification

- granular `ConsentLog`
- consent revoke
- legacy consent fallback
- target verification submit/list/detail
- admin approve/reject/need-more-info/revoke
- verification file admin-only download
- persona/voice policy gate

### Persona/Chat

- target 기반 persona 생성
- persona status/detail
- persona chat 생성/목록
- text message와 persona reply
- audio upload -> STT -> user message -> persona reply
- Gemini LLM service와 mock fallback

### Story/Share/Group

- AI interview session/question/answer
- photo memory upload/list/detail/delete
- storybook create/list/detail/chapters/regenerate
- share link create/list/public read/disable
- memory group create/list/detail/member/storybook share

### Deletion/Audit/Report

- deletion request create/list/detail/cancel
- admin deletion processing
- audit log creation/list/filter
- report create/list/detail
- admin report processing

### Voice

- PersonaVoiceProfile model
- voice sample quality checks
- voice profile create/evaluate/user-confirm
- admin voice profile approve/reject/revoke
- STT/TTS/VoiceClone service interfaces
- mock behavior under tests
- WebSocket voice chat endpoint
- VoiceCallSession model and migration
- voice call audit/rate/usage integration

## 진행 작업

현재 진행 관점의 우선순위:

- 문서 구조 정리와 최신화
- API contract와 실제 route 일치 여부 점검
- 배포 문서와 운영 체크리스트 보강
- WebSocket voice chat 프론트 연동 검증

## 예정 작업

### Product/API

- refresh token rotation 정책 강화
- pagination 응답 형태 통일
- public share response 최소화 재검토
- report category/action policy 정교화
- deletion request 비동기 처리 검토

### Frontend

- React/Vite/TypeScript API client
- auth route guard
- target/verification/consent wizard
- persona chat screen
- realtime voice chat screen
- storybook editor/viewer/share screen
- admin dashboard

### AI

- Gemini prompt 품질 개선
- storybook JSON schema validation 강화
- persona safety policy 고도화
- interview question diversity 개선

## 실서비스 확장 TODO

- Redis 기반 rate limit으로 확장
- background job queue 도입
- 파일 storage abstraction 검토
- object storage 전환은 현재 요구사항이 아니므로 보류
- DB index와 pagination 성능 점검
- observability: structured logs, metrics, tracing
- admin audit export
- data retention policy 자동화

## 음성 기능 TODO

현재 구현:

- chunked WebSocket turn-taking
- `audio_chunk -> end_utterance -> STT -> Gemini -> TTS/VoiceClone -> audio URL`

추후:

- streaming STT
- `partial_transcript` 실시간 전송
- streaming TTS
- audio response chunk event
- MediaRecorder browser compatibility test
- voice profile 품질 평가 고도화
- 실제 OpenVoice/MeloTTS runtime packaging
- 음성 파일 보관 기간/삭제 정책 구체화

## 보안/운영 TODO

- 운영 `SECRET_KEY` rotation 절차
- admin action 이중 확인
- verification file 보관/삭제 정책 명문화
- voice cloning consent UX 강화
- audit log retention
- CORS 운영 도메인 제한
- Nginx upload limit과 app `MAX_UPLOAD_SIZE` 일치
- backup/restore runbook
- incident response guide

## 개발 규칙

- API prefix는 `/api/v1`을 유지한다.
- model 변경 시 Alembic migration을 함께 만든다.
- 파일은 현재 local `uploads/` 구조를 유지한다.
- provider 추상화를 새로 과하게 만들지 않는다.
- 테스트 환경은 mock provider를 사용한다.
- owner-only/admin-only 정책을 route와 service에서 모두 확인한다.
- 신규 민감 기능은 AuditLog와 policy gate를 함께 고려한다.
