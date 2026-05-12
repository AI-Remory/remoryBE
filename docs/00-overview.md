# 00. Overview

## 목차

- [서비스 개요](#서비스-개요)
- [문제의식](#문제의식)
- [최종 서비스 방향](#최종-서비스-방향)
- [주요 도메인](#주요-도메인)
- [전체 사용자 흐름](#전체-사용자-흐름)
- [문서 구조](#문서-구조)

## 서비스 개요

Remory는 가족, 지인, 자기 자신의 기억을 target 단위로 수집하고, 사진/음성/인터뷰 데이터를 기반으로 AI persona, chat, storybook, 공유 경험을 제공하는 기억 보존 서비스다.

백엔드는 FastAPI 기반이며 `/api/v1` REST API와 WebSocket 음성 대화 API를 제공한다. 민감 데이터가 포함되는 서비스이므로 소유권, 검증, 동의, 삭제 요청, audit log가 핵심 도메인으로 포함된다.

## 문제의식

Remory가 다루는 데이터는 일반 콘텐츠보다 민감하다.

- 가족 관계, 사적 기억, 사진, 음성 데이터가 포함된다.
- voice cloning은 명시적 동의와 관계 검증 없이는 허용하면 안 된다.
- AI persona 응답은 사용자에게 실제 사람처럼 느껴질 수 있으므로 AI 생성 여부와 사용 범위를 분명히 관리해야 한다.
- 공유 링크와 그룹 공유는 읽기 권한과 민감 정보 노출 방지가 중요하다.
- 사용자가 삭제를 요청하면 DB record, 로컬 파일, 공유 링크, audit trail 정책이 일관돼야 한다.

## 최종 서비스 방향

서비스 방향은 단순한 챗봇이 아니라, 기억 수집부터 보존/공유까지 이어지는 흐름이다.

1. 사용자가 target을 만든다.
2. 관계/권한 검증과 consent를 남긴다.
3. 사진, 음성, 인터뷰 답변을 수집한다.
4. target 기반 persona와 voice profile을 만든다.
5. persona와 텍스트/음성으로 대화한다.
6. 인터뷰와 사진 기억을 storybook으로 생성한다.
7. share link 또는 group으로 공유한다.
8. 필요한 경우 report, deletion request, admin review로 운영한다.

## 주요 도메인

| Domain | Summary |
| --- | --- |
| User/Auth | 회원가입, 로그인, JWT, role |
| Target | 기억 대상 프로필 |
| TargetMedia | target의 image/voice 파일 |
| ConsentLog | 기능별 동의 이력과 철회 상태 |
| TargetVerificationRequest | 관계/권한 검증 요청과 admin review |
| Persona | target 기반 AI persona |
| PersonaChat/PersonaMessage | persona 대화와 message 저장 |
| PersonaVoiceProfile | voice cloning 가능 상태와 review metadata |
| AIInterviewSession | 기억 수집 질문/답변 |
| PhotoMemory | 사진 기반 기억 |
| StoryBook/StoryChapter | 인터뷰/사진 기반 storybook |
| ShareLink | 공개 링크 공유 |
| MemoryGroup | 그룹 공유 |
| DeletionRequest | 삭제 요청과 파일 정리 |
| AuditLog | 민감 작업 추적 |
| RateLimit/UsageLimit | 음성/STT/통화 사용량 제한 |
| Report | 신고 및 admin 처리 |
| VoiceCallSession | WebSocket 음성 대화 session |

## 전체 사용자 흐름

```text
Register/Login
  -> Create Target
  -> Create ConsentLog
  -> Submit TargetVerificationRequest
  -> Admin approves verification
  -> Upload image/voice TargetMedia
  -> Create Persona
  -> Create/Evaluate/Confirm PersonaVoiceProfile
  -> Start PersonaChat or WebSocket voice call
  -> Create Interview or PhotoMemory
  -> Generate StoryBook
  -> Share by link or group
  -> Report or DeletionRequest when needed
```

운영 흐름:

```text
Admin reviews verification
Admin reviews reports
Admin reviews voice profiles
Admin monitors audit logs, rate limit events, and usage limits
```

## 문서 구조

- 설치와 실행: [01-setup.md](01-setup.md)
- API 목록: [02-backend-api.md](02-backend-api.md)
- 프론트 연동: [03-frontend-integration.md](03-frontend-integration.md)
- 인증/권한: [04-auth-and-permission.md](04-auth-and-permission.md)
- 검증/동의 정책: [05-verification-consent-flow.md](05-verification-consent-flow.md)
- 실시간 음성 대화: [06-realtime-voice-chat.md](06-realtime-voice-chat.md)
- 테스트 시나리오: [07-test-scenario.md](07-test-scenario.md)
- 배포: [08-deployment.md](08-deployment.md)
- 개발 로드맵: [09-development-roadmap.md](09-development-roadmap.md)
