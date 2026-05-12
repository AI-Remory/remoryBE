# 02. Backend API

## 목차

- [공통 규칙](#공통-규칙)
- [Auth](#auth)
- [Target](#target)
- [Consent](#consent)
- [Verification](#verification)
- [Persona](#persona)
- [Chat](#chat)
- [Interview](#interview)
- [PhotoMemory](#photomemory)
- [StoryBook](#storybook)
- [ShareLink](#sharelink)
- [Group](#group)
- [Deletion](#deletion)
- [Voice](#voice)
- [Admin](#admin)
- [Report](#report)

## 공통 규칙

Base URL:

```text
http://localhost:8000
```

모든 v1 API prefix:

```text
/api/v1
```

인증이 필요한 API는 Bearer JWT를 사용한다.

```http
Authorization: Bearer {access_token}
```

일반 오류 응답:

```json
{
  "detail": "Target not found (ID: 123)"
}
```

주요 상태 코드:

| Status | Meaning |
| --- | --- |
| `400` | 잘못된 요청, 파일 업로드 실패, 비즈니스 처리 오류 |
| `401` | 토큰 없음, 만료, 형식 오류 |
| `403` | 소유자 아님, 동의/검증 미충족, 권한 부족 |
| `404` | 리소스 없음 |
| `422` | body/form/enum validation 실패 |
| `429` | rate limit 또는 usage limit 초과 |

파일 업로드는 `multipart/form-data`를 사용한다. 로컬 파일 저장은 기존 `uploads/` 구조를 유지한다.

## Auth

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | No | 회원가입, access/refresh token 발급 |
| `POST` | `/api/v1/auth/sign-up` | No | register alias |
| `POST` | `/api/v1/auth/login` | No | 로그인 |
| `GET` | `/api/v1/auth/me` | Yes | 현재 사용자 조회 |
| `POST` | `/api/v1/auth/refresh-token` | No | refresh token으로 access token 재발급 |
| `POST` | `/api/v1/auth/logout` | No | refresh token blacklist 처리 |

Register/Login response는 `access_token`, `refresh_token`, `token_type`, `user`를 포함한다.

## Target

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/targets` | Yes | target 생성 |
| `GET` | `/api/v1/targets?skip=0&limit=20` | Yes | 내 target 목록 |
| `GET` | `/api/v1/targets/{target_id}` | Yes | 내 target 상세 |
| `PUT` | `/api/v1/targets/{target_id}` | Yes | target 수정 |
| `DELETE` | `/api/v1/targets/{target_id}` | Yes | target soft delete |
| `POST` | `/api/v1/targets/{target_id}/media` | Yes | image/voice 업로드 |
| `GET` | `/api/v1/targets/{target_id}/media` | Yes | target media 목록 |
| `DELETE` | `/api/v1/media/{media_id}` | Yes | media 삭제 |

Target media upload form:

```text
media_type=image | voice
file=@photo.jpg | @voice.mp3
```

## Consent

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/consents` | Yes | consent history row 생성 |
| `GET` | `/api/v1/consents` | Yes | 내 consent 목록 |
| `GET` | `/api/v1/targets/{target_id}/consents` | Yes | target별 consent 목록 |
| `PATCH` | `/api/v1/consents/{consent_id}/revoke` | Yes | consent 철회 |

권장 consent type:

- `target_profile_consent`
- `photo_upload_consent`
- `voice_upload_consent`
- `voice_cloning_consent`
- `ai_persona_creation_consent`
- `ai_response_notice_consent`
- `storybook_share_consent`
- `group_share_consent`
- `data_retention_consent`
- `third_party_ai_processing_consent`

## Verification

사용자 API:

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/targets/{target_id}/verification-requests` | Yes | 검증 문서 제출 |
| `GET` | `/api/v1/targets/{target_id}/verification-requests` | Yes | target 검증 요청 목록 |
| `GET` | `/api/v1/verification-requests/{request_id}` | Yes | 검증 요청 상세 |

Admin API:

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/admin/verification-requests` | Admin | 검증 요청 목록 |
| `GET` | `/api/v1/admin/verification-requests/{request_id}` | Admin | 검증 요청 상세 |
| `GET` | `/api/v1/admin/verification-requests/{request_id}/file` | Admin | 검증 파일 다운로드 |
| `PATCH` | `/api/v1/admin/verification-requests/{request_id}/approve` | Admin | 승인 |
| `PATCH` | `/api/v1/admin/verification-requests/{request_id}/reject` | Admin | 거절 |
| `PATCH` | `/api/v1/admin/verification-requests/{request_id}/need-more-info` | Admin | 추가 정보 요청 |
| `PATCH` | `/api/v1/admin/verification-requests/{request_id}/revoke` | Admin | 승인 철회 |

`TargetVerificationRequest.status`: `PENDING`, `NEED_MORE_INFO`, `APPROVED`, `REJECTED`, `EXPIRED`, `REVOKED`.

## Persona

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/targets/{target_id}/persona` | Yes | target 기반 persona 생성 |
| `GET` | `/api/v1/personas/{persona_id}` | Yes | persona 상세 |
| `GET` | `/api/v1/personas/{persona_id}/status` | Yes | persona 상태 |
| `POST` | `/api/v1/personas/{persona_id}/voice-profile` | Yes | voice profile 생성/갱신 |
| `GET` | `/api/v1/personas/{persona_id}/voice-profile` | Yes | voice profile 조회 |
| `POST` | `/api/v1/personas/{persona_id}/voice-profile/evaluate` | Yes | voice sample 평가 |
| `PATCH` | `/api/v1/personas/{persona_id}/voice-profile/user-confirm` | Yes | 사용자 확인 |

Persona 생성 조건은 [05-verification-consent-flow.md](05-verification-consent-flow.md)에 정리되어 있다.

## Chat

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/personas/{persona_id}/chats` | Yes | persona chat 생성 |
| `GET` | `/api/v1/personas/{persona_id}/chats` | Yes | persona chat 목록 |
| `POST` | `/api/v1/chats/{chat_id}/messages` | Yes | 텍스트 메시지 전송, persona 응답 생성 |
| `POST` | `/api/v1/chats/{chat_id}/audio` | Yes | 음성 업로드, STT, persona 응답 생성 |
| `GET` | `/api/v1/chats/{chat_id}/messages` | Yes | chat messages 조회 |

Audio upload form:

```text
file=@voice.wav
generate_audio=true | false
```

## Interview

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/interviews` | Yes | interview session 생성 |
| `GET` | `/api/v1/interviews/{session_id}` | Yes | session 상세 |
| `POST` | `/api/v1/interviews/{session_id}/questions` | Yes | AI 질문 생성 |
| `POST` | `/api/v1/interviews/{session_id}/answers` | Yes | 답변 저장 |

`session_type`: `TARGET_PROFILE`, `PHOTO_MEMORY`, `SELF_STORY`.

## PhotoMemory

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/photo-memories` | Yes | 사진 기억 업로드/생성 |
| `GET` | `/api/v1/photo-memories` | Yes | 내 photo memory 목록 |
| `GET` | `/api/v1/photo-memories/{photo_memory_id}` | Yes | 상세 |
| `DELETE` | `/api/v1/photo-memories/{photo_memory_id}` | Yes | 삭제 |

## StoryBook

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/storybooks` | Yes | storybook 생성 |
| `GET` | `/api/v1/storybooks` | Yes | 목록 |
| `GET` | `/api/v1/storybooks/{storybook_id}` | Yes | 상세 |
| `GET` | `/api/v1/storybooks/{storybook_id}/chapters` | Yes | chapter 목록 |
| `POST` | `/api/v1/storybooks/{storybook_id}/regenerate` | Yes | 재생성 |

Gemini가 실패하거나 JSON 파싱이 실패하면 mock storybook content로 fallback한다.

## ShareLink

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/storybooks/{storybook_id}/share-links` | Yes | 공유 링크 생성 |
| `GET` | `/api/v1/storybooks/{storybook_id}/share-links` | Yes | 공유 링크 목록 |
| `GET` | `/api/v1/share/{token}` | No | 공개 공유 storybook 조회 |
| `PATCH` | `/api/v1/share-links/{share_link_id}/disable` | Yes | 공유 링크 비활성화 |

공개 조회 응답은 owner 내부 정보와 민감한 파일 경로를 노출하지 않는 읽기 전용 형태여야 한다.

## Group

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/groups` | Yes | memory group 생성 |
| `GET` | `/api/v1/groups` | Yes | 내 group 목록 |
| `GET` | `/api/v1/groups/{group_id}` | Yes | group 상세 |
| `POST` | `/api/v1/groups/{group_id}/members` | Yes | member 추가 |
| `GET` | `/api/v1/groups/{group_id}/members` | Yes | member 목록 |
| `POST` | `/api/v1/groups/{group_id}/storybooks/{storybook_id}` | Yes | group에 storybook 공유 |
| `GET` | `/api/v1/groups/{group_id}/storybooks` | Yes | group 공유 storybook 목록 |

## Deletion

| Method | Path | Auth | 설명 |
| --- | --- | --- | --- |
| `POST` | `/api/v1/deletion-requests` | Yes | 삭제 요청 생성 |
| `GET` | `/api/v1/deletion-requests` | Yes | 내 삭제 요청 목록 |
| `GET` | `/api/v1/deletion-requests/{request_id}` | Yes | 삭제 요청 상세 |
| `PATCH` | `/api/v1/deletion-requests/{request_id}/cancel` | Yes | 삭제 요청 취소 |

Admin deletion:

- `GET /api/v1/admin/deletion-requests`
- `GET /api/v1/admin/deletion-requests/{request_id}`
- `PATCH /api/v1/admin/deletion-requests/{request_id}/approve-and-process`
- `PATCH /api/v1/admin/deletion-requests/{request_id}/reject`

## Voice

Voice profile:

- `POST /api/v1/personas/{persona_id}/voice-profile`
- `GET /api/v1/personas/{persona_id}/voice-profile`
- `POST /api/v1/personas/{persona_id}/voice-profile/evaluate`
- `PATCH /api/v1/personas/{persona_id}/voice-profile/user-confirm`

Realtime voice chat:

- `WS /api/v1/ws/personas/{persona_id}/voice?token={access_token}`

자세한 WebSocket protocol은 [06-realtime-voice-chat.md](06-realtime-voice-chat.md)를 본다.

Usage/rate limit:

- user monthly voice generation
- user monthly STT request
- user monthly voice call seconds
- persona monthly voice generation
- persona monthly voice call seconds

## Admin

Admin-only API는 `User.role == ADMIN`만 접근한다.

| Area | Paths |
| --- | --- |
| Verification | `/api/v1/admin/verification-requests...` |
| Deletion | `/api/v1/admin/deletion-requests...` |
| AuditLog | `/api/v1/admin/audit-logs` |
| UsageLimit | `/api/v1/admin/usage-limits`, `/api/v1/admin/users/{user_id}/usage-limit`, `/api/v1/admin/personas/{persona_id}/usage-limit` |
| RateLimitEvent | `/api/v1/admin/rate-limit-events` |
| Reports | `/api/v1/admin/reports...` |
| VoiceProfile review | `/api/v1/admin/voice-profiles...` |

## Report

User:

- `POST /api/v1/reports`
- `GET /api/v1/reports`
- `GET /api/v1/reports/{report_id}`

Admin:

- `GET /api/v1/admin/reports`
- `GET /api/v1/admin/reports/{report_id}`
- `PATCH /api/v1/admin/reports/{report_id}/reviewing`
- `PATCH /api/v1/admin/reports/{report_id}/resolve`
- `PATCH /api/v1/admin/reports/{report_id}/reject`
- `PATCH /api/v1/admin/reports/{report_id}/action-taken`
