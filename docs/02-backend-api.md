# 02. Backend API

## 목차

- [공통 규칙](#공통-규칙)
- [Response Shape](#response-shape)
- [프론트 렌더링 기준](#프론트-렌더링-기준)
- [Auth](#auth)
- [Target](#target)
- [Consent](#consent)
- [Verification](#verification)
- [Media](#media)
- [Persona](#persona)
- [Chat](#chat)
- [Interview](#interview)
- [Photo Memory](#photo-memory)
- [StoryBook](#storybook)
- [Sharing](#sharing)
- [Group](#group)
- [Deletion](#deletion)
- [Report](#report)
- [Admin](#admin)
- [Realtime Voice](#realtime-voice)
- [Enum 값](#enum-값)

## 공통 규칙

| 항목 | 값 |
| --- | --- |
| Base URL | `/api/v1` |
| Health | `GET /health` |
| 인증 | `Authorization: Bearer <access_token>` |
| JSON | `Content-Type: application/json` |
| Upload | `multipart/form-data` |
| DateTime | ISO-8601 문자열 |
| Pagination | `{ "total": number, "skip": number, "limit": number, "items": [...] }` |

FastAPI validation 실패는 기본 `422` shape를 반환한다.

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

서비스 예외는 `app/utils/exceptions.py`에서 `HTTPException(detail=<message>)`로 변환된다. 프론트는 문자열 `detail`과 FastAPI validation 배열 `detail`을 모두 처리해야 한다.

```json
{
  "detail": "Invalid credentials"
}
```

## Response Shape

### 단일 객체

`response_model`이 `TargetResponse`, `UserResponse`처럼 단일 schema이면 최상위가 곧 객체다.

```json
{
  "id": 1,
  "user_id": 1,
  "name": "Mom",
  "description": "Warm and thoughtful",
  "target_type": "parent",
  "profile_image_path": null,
  "is_deleted": false,
  "created_at": "2026-05-12T10:00:00",
  "updated_at": "2026-05-12T10:00:00"
}
```

### 배열

`response_model=list[...]` endpoint는 배열을 그대로 반환한다.

```json
[
  {
    "id": 1,
    "persona_id": 1,
    "title": "First chat",
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  }
]
```

### 페이지네이션

`PaginatedResponse[...]`는 `items`를 렌더링하고 `total`, `skip`, `limit`으로 pagination UI를 만든다.

```json
{
  "total": 1,
  "skip": 0,
  "limit": 20,
  "items": [
    {
      "id": 1,
      "name": "Mom",
      "target_type": "parent"
    }
  ]
}
```

### 인증 응답

회원가입/로그인은 token pair와 user 객체를 함께 반환한다.

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "nickname": "user",
    "created_at": "2026-05-12T10:00:00",
    "updated_at": "2026-05-12T10:00:00"
  }
}
```

### 204 응답

`DELETE /api/v1/targets/{target_id}`는 성공 시 body 없이 `204 No Content`다.

## 프론트 렌더링 기준

| API shape | 화면 처리 |
| --- | --- |
| 단일 객체 | 상세 화면 state에 그대로 저장한다. nullable 필드는 `null` 표시를 허용한다. |
| 배열 | 빈 배열이면 empty state를 보여준다. pagination control은 만들지 않는다. |
| `PaginatedResponse` | `items`만 리스트에 뿌리고 `total`, `skip`, `limit`으로 다음 요청 offset을 계산한다. |
| `AuthResponse` | `access_token`, `refresh_token`을 저장하고 `user`를 session profile로 저장한다. |
| `MessageResponse`류 | `message`를 toast/snackbar에 표시한다. |
| `multipart/form-data` | JSON body가 아니라 `FormData`로 전송한다. |
| 401 | refresh token으로 재발급 후 원 요청 재시도, 실패하면 로그아웃 |
| 403 | 권한 없음 안내 |
| 422 | `detail` 배열이면 필드별 validation 메시지로 매핑 |

## Auth

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/auth/register` | 없음 | `RegisterRequest(email*, nickname*, password*)` | `201 AuthResponse` |
| `POST /api/v1/auth/sign-up` | 없음 | `RegisterRequest` | `201 AuthResponse` |
| `POST /api/v1/auth/login` | 없음 | `LoginRequest(email*, password*)` | `AuthResponse` |
| `GET /api/v1/auth/me` | 필요 | 없음 | `UserResponse` |
| `POST /api/v1/auth/refresh-token` | 없음 | `RefreshTokenRequest(refresh_token*)` | `TokenResponse` |
| `POST /api/v1/auth/logout` | 없음 | `LogoutRequest(refresh_token*)` | `MessageResponse(message*)` |

### 회원가입

```http
POST /api/v1/auth/register
```

```json
{
  "email": "user@example.com",
  "nickname": "user",
  "password": "securepassword123"
}
```

성공 시 `AuthResponse`를 받는다. 실패 시 중복 이메일/닉네임 등은 `detail` 문자열로 표시된다.

## Target

| API | 인증 | Request/Query | Response |
| --- | --- | --- | --- |
| `POST /api/v1/targets` | 필요 | `TargetCreateRequest(name*, description, target_type)` | `201 TargetResponse` |
| `GET /api/v1/targets?skip=0&limit=20` | 필요 | query | `PaginatedResponse[TargetResponse]` |
| `GET /api/v1/targets/{target_id}` | 필요 | path | `TargetDetailResponse` |
| `PUT /api/v1/targets/{target_id}` | 필요 | `TargetUpdateRequest` | `TargetResponse` |
| `DELETE /api/v1/targets/{target_id}` | 필요 | path | `204 No Content` |

`TargetDetailResponse`는 `TargetResponse`에 `media_count`, `has_persona`가 추가된다.

## Consent

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/consents` | 필요 | `ConsentCreate` | `201 ConsentResponse` |
| `GET /api/v1/consents` | 필요 | 없음 | `ConsentResponse[]` |
| `GET /api/v1/targets/{target_id}/consents` | 필요 | path | `ConsentResponse[]` |
| `PATCH /api/v1/consents/{consent_id}/revoke` | 필요 | 없음 | `ConsentRevokeResponse` |

`ConsentCreate`는 `consent_type*`, `target_id`, `consent_version`, `consent_text_snapshot`, `is_agreed`, `is_consented`, `details`를 받는다.

## Verification

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/targets/{target_id}/verification-requests` | 필요 | multipart: `verification_type_param*`, `applicant_note`, `file*` | `201 VerificationRequestResponse` |
| `GET /api/v1/targets/{target_id}/verification-requests?skip=0&limit=20` | 필요 | query | `PaginatedResponse[VerificationRequestResponse]` |
| `GET /api/v1/verification-requests/{request_id}` | 필요 | path | `VerificationRequestDetailResponse` |

`verification_type_param`은 `FAMILY_RELATION_CERTIFICATE`, `ID_CARD`, `SELF_DECLARATION`, `OTHER` 중 하나다. 생성 조건과 관리자 검수 흐름은 [05-verification-consent-flow.md](05-verification-consent-flow.md)를 본다.

## Media

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/targets/{target_id}/media` | 필요 | multipart: `media_type*`, `file*` | `201 MediaUploadResponse` |
| `GET /api/v1/targets/{target_id}/media` | 필요 | path | `TargetMediaResponse[]` |
| `DELETE /api/v1/media/{media_id}` | 필요 | path | `MediaDeleteResponse(message)` |

`media_type`은 `image` 또는 `voice`다.

## Persona

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/targets/{target_id}/persona` | 필요 | 없음 | `201 PersonaDetailResponse` |
| `GET /api/v1/personas/{persona_id}` | 필요 | path | `PersonaDetailResponse` |
| `GET /api/v1/personas/{persona_id}/status` | 필요 | path | `PersonaStatusResponse` |
| `POST /api/v1/personas/{persona_id}/voice-profile` | 필요 | 없음 | `201 PersonaVoiceProfileResponse` |
| `GET /api/v1/personas/{persona_id}/voice-profile` | 필요 | path | `PersonaVoiceProfileResponse` |
| `POST /api/v1/personas/{persona_id}/voice-profile/evaluate` | 필요 | 없음 | `PersonaVoiceProfileResponse` |
| `PATCH /api/v1/personas/{persona_id}/voice-profile/user-confirm` | 필요 | `VoiceProfileReviewRequest(review_note)` | `PersonaVoiceProfileResponse` |

`PersonaDetailResponse`에는 `status`, `persona_name`, `speaking_style`, `personality_summary`, `memory_summary`, `system_prompt`, `is_voice_profile_created`, `is_consent_required`, `voice_profile`이 포함된다.

## Chat

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/personas/{persona_id}/chats` | 필요 | `PersonaChatCreateRequest(title)` | `201 PersonaChatResponse` |
| `GET /api/v1/personas/{persona_id}/chats` | 필요 | path | `PersonaChatResponse[]` |
| `POST /api/v1/chats/{chat_id}/messages` | 필요 | `PersonaMessageCreateRequest` | `201 PersonaMessagePairResponse` |
| `POST /api/v1/chats/{chat_id}/audio` | 필요 | multipart audio file | `201 PersonaMessagePairResponse` |
| `GET /api/v1/chats/{chat_id}/messages` | 필요 | path | `PersonaMessageResponse[]` |

`PersonaMessagePairResponse`는 `{ "user_message": PersonaMessageResponse, "persona_message": PersonaMessageResponse }`다.

## Interview

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/interviews` | 필요 | `AIInterviewSessionCreateRequest(session_type*, title, target_id, photo_memory_id)` | `201 AIInterviewSessionResponse` |
| `GET /api/v1/interviews/{session_id}` | 필요 | path | `AIInterviewSessionDetailResponse` |
| `POST /api/v1/interviews/{session_id}/questions` | 필요 | `AIInterviewQuestionCreateRequest(question_type)` | `201 AIInterviewQuestionResponse` |
| `POST /api/v1/interviews/{session_id}/answers` | 필요 | `AIInterviewAnswerCreateRequest(question_id*, answer_text, answer_audio_path)` | `201 AIInterviewAnswerResponse` |

`session_type`은 `TARGET_PROFILE`, `PHOTO_MEMORY`, `SELF_STORY`다.

## Photo Memory

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/photo-memories` | 필요 | multipart: `title*`, `description`, `taken_at`, `location`, `file*` | `201 PhotoMemoryResponse` |
| `GET /api/v1/photo-memories` | 필요 | 없음 | `PhotoMemoryResponse[]` |
| `GET /api/v1/photo-memories/{photo_memory_id}` | 필요 | path | `PhotoMemoryResponse` |
| `DELETE /api/v1/photo-memories/{photo_memory_id}` | 필요 | path | `PhotoMemoryDeleteResponse(message)` |

## StoryBook

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/storybooks` | 필요 | `StoryBookCreateRequest(title*, interview_session_id, photo_memory_id, visibility)` | `201 StoryBookDetailResponse` |
| `GET /api/v1/storybooks` | 필요 | 없음 | `StoryBookResponse[]` |
| `GET /api/v1/storybooks/{storybook_id}` | 필요 | path | `StoryBookDetailResponse` |
| `GET /api/v1/storybooks/{storybook_id}/chapters` | 필요 | path | `StoryChapterResponse[]` |
| `POST /api/v1/storybooks/{storybook_id}/regenerate` | 필요 | 없음 | `StoryBookDetailResponse` |

## Sharing

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/storybooks/{storybook_id}/share-links` | 필요 | `ShareLinkCreateRequest(expires_at)` | `201 ShareLinkResponse` |
| `GET /api/v1/storybooks/{storybook_id}/share-links` | 필요 | path | `ShareLinkResponse[]` |
| `GET /api/v1/share/{token}` | 없음 | path | `PublicSharedStoryBookResponse` |
| `PATCH /api/v1/share-links/{share_link_id}/disable` | 필요 | 없음 | `ShareLinkDisableResponse` |

공개 조회 응답은 `{ "title", "summary", "visibility", "chapters" }`로 구성된다.

## Group

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/groups` | 필요 | `MemoryGroupCreateRequest(name*, description)` | `201 MemoryGroupResponse` |
| `GET /api/v1/groups` | 필요 | 없음 | `MemoryGroupResponse[]` |
| `GET /api/v1/groups/{group_id}` | 필요 | path | `MemoryGroupDetailResponse` |
| `POST /api/v1/groups/{group_id}/members` | 필요 | `GroupMemberCreateRequest(user_id*, role)` | `201 GroupMemberResponse` |
| `GET /api/v1/groups/{group_id}/members` | 필요 | path | `GroupMemberResponse[]` |
| `POST /api/v1/groups/{group_id}/storybooks/{storybook_id}` | 필요 | 없음 | `201 GroupStoryBookResponse` |
| `GET /api/v1/groups/{group_id}/storybooks` | 필요 | path | `GroupStoryBookListItemResponse[]` |

## Deletion

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/deletion-requests` | 필요 | `DeletionRequestCreateRequest(target_type*, target_id, reason)` | `201 DeletionRequestResponse` |
| `GET /api/v1/deletion-requests` | 필요 | 없음 | `DeletionRequestResponse[]` |
| `GET /api/v1/deletion-requests/{request_id}` | 필요 | path | `DeletionRequestResponse` |
| `PATCH /api/v1/deletion-requests/{request_id}/cancel` | 필요 | 없음 | `DeletionRequestResponse` |

## Report

| API | 인증 | Request | Response |
| --- | --- | --- | --- |
| `POST /api/v1/reports` | 필요 | `CreateReportRequest(target_type*, target_id*, reason_type*, reason_detail)` | `ReportResponse` |
| `GET /api/v1/reports?page=1&size=20` | 필요 | query | `PaginatedResponse[ReportResponse]` |
| `GET /api/v1/reports/{report_id}` | 필요 | path | `ReportResponse` |

## Admin

모든 admin API는 `User.role == admin`이어야 한다.

| API | Request | Response |
| --- | --- | --- |
| `GET /api/v1/admin/verification-requests` | query: `status`, `page`, `size` | `PaginatedResponse[VerificationRequestAdminResponse]` |
| `GET /api/v1/admin/verification-requests/{request_id}` | path | `VerificationRequestAdminResponse` |
| `GET /api/v1/admin/verification-requests/{request_id}/file` | path | file response |
| `PATCH /api/v1/admin/verification-requests/{request_id}/approve` | `VerificationRequestApproveRequest` | `VerificationRequestAdminResponse` |
| `PATCH /api/v1/admin/verification-requests/{request_id}/reject` | `VerificationRequestRejectRequest` | `VerificationRequestAdminResponse` |
| `PATCH /api/v1/admin/verification-requests/{request_id}/need-more-info` | `VerificationRequestNeedMoreInfoRequest` | `VerificationRequestAdminResponse` |
| `PATCH /api/v1/admin/verification-requests/{request_id}/revoke` | `VerificationRequestRevokeRequest` | `VerificationRequestAdminResponse` |
| `GET /api/v1/admin/deletion-requests` | query | `DeletionRequestResponse[]` |
| `GET /api/v1/admin/deletion-requests/{request_id}` | path | `DeletionRequestResponse` |
| `PATCH /api/v1/admin/deletion-requests/{request_id}/approve-and-process` | 없음 | `DeletionRequestResponse` |
| `PATCH /api/v1/admin/deletion-requests/{request_id}/reject` | 없음 | `DeletionRequestResponse` |
| `GET /api/v1/admin/audit-logs` | query filters | `PaginatedResponse[AuditLogResponse]` |
| `GET /api/v1/admin/usage-limits` | query | `PaginatedResponse[UsageLimitResponse]` |
| `PATCH /api/v1/admin/users/{user_id}/usage-limit` | `UpdateUsageLimitRequest` | `UsageLimitResponse` |
| `PATCH /api/v1/admin/personas/{persona_id}/usage-limit` | `UpdatePersonaUsageLimitRequest` | `PersonaUsageLimitResponse` |
| `GET /api/v1/admin/rate-limit-events` | query | `PaginatedResponse[RateLimitEventResponse]` |
| `GET /api/v1/admin/reports` | query | `PaginatedResponse` |
| `GET /api/v1/admin/reports/{report_id}` | path | report object |
| `PATCH /api/v1/admin/reports/{report_id}/reviewing` | optional JSON dict | report object |
| `PATCH /api/v1/admin/reports/{report_id}/resolve` | optional JSON dict | report object |
| `PATCH /api/v1/admin/reports/{report_id}/reject` | optional JSON dict | report object |
| `PATCH /api/v1/admin/reports/{report_id}/action-taken` | optional JSON dict | report object |
| `GET /api/v1/admin/voice-profiles/{voice_profile_id}` | path | `PersonaVoiceProfileResponse` |
| `PATCH /api/v1/admin/voice-profiles/{voice_profile_id}/approve` | `VoiceProfileReviewRequest` | `PersonaVoiceProfileResponse` |
| `PATCH /api/v1/admin/voice-profiles/{voice_profile_id}/reject` | `VoiceProfileReviewRequest` | `PersonaVoiceProfileResponse` |
| `PATCH /api/v1/admin/voice-profiles/{voice_profile_id}/revoke` | `VoiceProfileReviewRequest` | `PersonaVoiceProfileResponse` |

## Realtime Voice

```http
WS /api/v1/ws/personas/{persona_id}/voice?token=<access_token>
```

상세 protocol은 [06-realtime-voice-chat.md](06-realtime-voice-chat.md)를 본다.

서버 송신 예시:

```json
{ "type": "session_started", "session_id": 1 }
```

```json
{ "type": "final_transcript", "text": "안녕하세요" }
```

```json
{ "type": "persona_audio", "audio_url": "/uploads/voices/call_outputs/1/output.wav", "audio_file_path": "uploads/voices/call_outputs/1/output.wav" }
```

```json
{ "type": "error", "message": "Voice call session has not started" }
```

## Enum 값

| Enum | 값 |
| --- | --- |
| `TargetType` | `parent`, `grandparent`, `friend`, `romantic`, `self`, `other` |
| `MediaType` | `image`, `voice` |
| `ConsentType` | `target_profile_consent`, `photo_upload_consent`, `voice_upload_consent`, `voice_cloning_consent`, `ai_persona_creation_consent`, `ai_response_notice_consent`, `storybook_share_consent`, `group_share_consent`, `data_retention_consent`, `third_party_ai_processing_consent`, legacy: `voice_collection`, `photo_collection`, `persona_creation`, `data_usage`, `ai_processing`, `ai_response_notice`, `storybook_share` |
| `VerificationType` | `FAMILY_RELATION_CERTIFICATE`, `ID_CARD`, `SELF_DECLARATION`, `OTHER` |
| `VerificationStatus` | `PENDING`, `NEED_MORE_INFO`, `APPROVED`, `REJECTED`, `EXPIRED`, `REVOKED` |
| `PersonaStatus` | `PENDING`, `READY`, `FAILED` |
| `VoiceProfileStatus` | `PENDING`, `PROCESSING`, `READY`, `FAILED`, `NEEDS_MORE_SAMPLES`, `REVOKED` |
| `VoiceProfileReviewStatus` | `NOT_REVIEWED`, `USER_CONFIRMED`, `ADMIN_APPROVED`, `REJECTED` |
| `MessageType` | `TEXT`, `AUDIO` |
| `SenderType` | `USER`, `PERSONA`, `SYSTEM` |
| `InterviewType` | `TARGET_PROFILE`, `PHOTO_MEMORY`, `SELF_STORY` |
| `StoryBookVisibility` | `PRIVATE`, `LINK`, `GROUP`, `PUBLIC` |
| `DeletionStatus` | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `REJECTED`, `CANCELLED` |
| `GroupMemberRole` | `OWNER`, `MEMBER`, `VIEWER` |
| `ReportStatus` | `PENDING`, `REVIEWING`, `RESOLVED`, `REJECTED`, `ACTION_TAKEN` |
