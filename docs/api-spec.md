# Remory API Spec

Remory는 target 기반 가상 페르소나와 대화하고, 사진/AI 인터뷰 기반 스토리북을 생성·공유하는 AI 기억 플랫폼이다.

- API prefix: `/api/v1`
- 인증: Bearer JWT 토큰
- 주요 데이터: User, Target, TargetMedia, Persona, Chat, Interview, PhotoMemory, StoryBook, ShareLink, MemoryGroup, DeletionRequest

## Common Rules

### Base URL

```text
http://localhost:8000
```

모든 v1 API는 다음 prefix를 사용한다.

```text
/api/v1
```

### Auth Header

로그인이 필요한 API는 다음 헤더가 필요하다.

```http
Authorization: Bearer {access_token}
```

### Error Response

현재 API는 FastAPI 기본 에러 형식 또는 `RemoryException` 변환 형식을 반환한다.

```json
{
  "detail": "Target not found (ID: 123)"
}
```

주요 상태 코드:

- `400`: 잘못된 요청, 파일 업로드 실패, 일반 처리 오류
- `401`: 인증 실패 또는 토큰 없음
- `403`: 소유권/권한 없음
- `404`: 리소스 없음
- `422`: request body, form, enum 등 검증 실패

### File Upload

파일 업로드는 `multipart/form-data`를 사용한다.

예시:

```http
Content-Type: multipart/form-data
Authorization: Bearer {access_token}
```

```text
file=@photo.jpg; type=image/jpeg
title=Birthday
description=Family photo
```

Note: API 응답에는 내부 저장 파일 경로(예: `document_file_path`, `file_path`, `stored_filename`)를 일반 사용자에게 노출하지 않습니다. 관리자 전용 엔드포인트만 심사 목적으로 내부 경로를 포함할 수 있으니 프론트엔드에서는 해당 필드에 의존하지 마세요.

### Date Format

날짜/시간은 ISO 8601 문자열을 사용한다.

```json
"2026-05-09T10:30:00"
```

### Soft Delete

`deleted_at`이 있는 데이터는 기본 조회에서 제외된다. 일부 기존 모델은 `is_deleted=true`를 사용한다.

## Enums

| Name | Values |
|---|---|
| `media_type` | `image`, `voice` |
| `persona.status` | `PENDING`, `READY`, `FAILED` |
| `sender_type` | `USER`, `PERSONA`, `SYSTEM` |
| `message_type` | `TEXT`, `AUDIO` |
| `interview.session_type` | `TARGET_PROFILE`, `PHOTO_MEMORY`, `SELF_STORY` |
| `interview.status` | `IN_PROGRESS`, `COMPLETED`, `CANCELLED` |
| `storybook.source_type` | `INTERVIEW`, `PHOTO_MEMORY`, `SELF_STORY` |
| `storybook.status` | `DRAFT`, `GENERATED`, `FAILED` |
| `storybook.visibility` | `PRIVATE`, `LINK`, `GROUP`, `PUBLIC` |
| `group.role` | `OWNER`, `MEMBER`, `VIEWER` |
| `verification.status` | `PENDING`, `APPROVED`, `REJECTED` |
| `deletion.target_type` | `TARGET`, `TARGET_MEDIA`, `PERSONA`, `PERSONA_CHAT`, `PERSONA_MESSAGE`, `PHOTO_MEMORY`, `STORYBOOK`, `SHARE_LINK`, `MEMORY_GROUP`, `ACCOUNT`, `VERIFICATION_REQUEST` |
| `deletion.status` | `REQUESTED`, `COMPLETED`, `FAILED` |

## A. Auth

### Register

- Method: `POST`
- URL: `/api/v1/auth/register`
- Auth: No
- Description: 새 사용자를 생성하고 access/refresh token을 반환한다.

Request:

```json
{
  "email": "user@example.com",
  "nickname": "user",
  "password": "securepassword123"
}
```

Response:

```json
{
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "nickname": "user",
    "created_at": "2026-05-09T10:00:00",
    "updated_at": "2026-05-09T10:00:00"
  }
}
```

Errors: `400`, `422`

### Login

- Method: `POST`
- URL: `/api/v1/auth/login`
- Auth: No
- Description: 이메일/비밀번호로 로그인한다.

Request:

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response: register와 동일한 token 응답.

Errors: `401`, `422`

### Me

- Method: `GET`
- URL: `/api/v1/auth/me`
- Auth: Yes
- Description: 현재 로그인한 사용자 정보를 조회한다.

Request Body: 없음

Response:

```json
{
  "id": 1,
  "email": "user@example.com",
  "nickname": "user",
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`

## B. Target

### Create Target

- Method: `POST`
- URL: `/api/v1/targets`
- Auth: Yes
- Description: 페르소나 생성 대상 target을 생성한다.

Request:

```json
{
  "name": "Mom",
  "description": "Warm and thoughtful",
  "target_type": "parent"
}
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "name": "Mom",
  "description": "Warm and thoughtful",
  "target_type": "parent",
  "profile_image_path": null,
  "is_deleted": false,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `422`

### List Targets

- Method: `GET`
- URL: `/api/v1/targets?skip=0&limit=20`
- Auth: Yes
- Description: 내 target 목록을 조회한다.

Request Body: 없음

Response:

```json
{
  "total": 1,
  "skip": 0,
  "limit": 20,
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "name": "Mom",
      "description": "Warm and thoughtful",
      "target_type": "parent",
      "profile_image_path": null,
      "is_deleted": false,
      "created_at": "2026-05-09T10:00:00",
      "updated_at": "2026-05-09T10:00:00"
    }
  ]
}
```

Errors: `401`

### Get Target

- Method: `GET`
- URL: `/api/v1/targets/{target_id}`
- Auth: Yes
- Description: 본인 소유 target 상세를 조회한다.

Request Body: 없음

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "name": "Mom",
  "description": "Warm and thoughtful",
  "target_type": "parent",
  "profile_image_path": null,
  "is_deleted": false,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00",
  "media_count": 2,
  "has_persona": true
}
```

Errors: `401`, `403`, `404`

### Update Target

- Method: `PUT`
- URL: `/api/v1/targets/{target_id}`
- Auth: Yes
- Description: target 정보를 수정한다.
- Note: `PATCH /api/v1/targets/{target_id}`는 미구현.

Request:

```json
{
  "name": "Mother",
  "description": "Updated description",
  "target_type": "parent"
}
```

Response: Target response.

Errors: `401`, `403`, `404`, `422`

### Delete Target

- Method: `DELETE`
- URL: `/api/v1/targets/{target_id}`
- Auth: Yes
- Description: target을 soft delete 처리한다.

Request Body: 없음

Response: `204 No Content`

Errors: `401`, `403`, `404`

## C. TargetMedia

### Upload Target Media

- Method: `POST`
- URL: `/api/v1/targets/{target_id}/media`
- Auth: Yes
- Description: target persona 생성을 위한 이미지/음성 파일을 업로드한다.
- Content-Type: `multipart/form-data`

Request:

```text
media_type=image
file=@photo.jpg; type=image/jpeg
```

또는

```text
media_type=voice
file=@voice.mp3; type=audio/mpeg
```

Response:

```json
{
  "file_id": 1,
  "target_id": 1,
  "uploaded_by": 1,
  "original_filename": "photo.jpg",
  "stored_filename": "uuid.jpg",
  "file_path": "uploads/images/1/uuid.jpg",
  "media_type": "image",
  "file_size": 12345,
  "mime_type": "image/jpeg",
  "message": "File uploaded successfully"
}
```

Errors: `400`, `401`, `403`, `404`, `422`

### List Target Media

- Method: `GET`
- URL: `/api/v1/targets/{target_id}/media`
- Auth: Yes
- Description: target의 삭제되지 않은 media 목록을 조회한다.

Request Body: 없음

Response:

```json
[
  {
    "id": 1,
    "target_id": 1,
    "uploaded_by": 1,
    "media_type": "image",
    "original_filename": "photo.jpg",
    "stored_filename": "uuid.jpg",
    "file_path": "uploads/images/1/uuid.jpg",
    "mime_type": "image/jpeg",
    "file_size": 12345,
    "duration_seconds": null,
    "is_deleted": false,
    "created_at": "2026-05-09T10:00:00",
    "updated_at": "2026-05-09T10:00:00"
  }
]
```

Errors: `401`, `403`, `404`

## C. Target Verification

Target에 대한 신원/권한 검증 요청(verification request)을 제출하고 조회하는 API입니다. 민감 파일 경로(`document_file_path`, 내부 저장 경로 등)는 일반 사용자 응답에 노출되지 않습니다. 관리자 전용 엔드포인트에서만 심사 목적의 내부 정보 접근이 허용됩니다.

### Submit Verification Request

- Method: `POST`
- URL: `/api/v1/targets/{target_id}/verification-requests`
- Auth: Yes
- Permission: target 소유자
- Description: 타겟에 대한 verification request(신분증, 증빙서류 등)를 multipart/form-data로 제출한다. 실제 파일은 백엔드에서 안전한 위치에 저장되며, 일반 사용자 응답에는 내부 파일 경로가 포함되지 않는다.

Request (multipart/form-data):

```text
verification_type=IDENTITY_DOCUMENT
document=@id_card.jpg; type=image/jpeg
notes=Scanned ID front side
```

Response (201 Created):

```json
{
  "id": 10,
  "target_id": 1,
  "user_id": 1,
  "verification_type": "IDENTITY_DOCUMENT",
  "status": "PENDING",
  "submitted_at": "2026-05-09T11:00:00",
  "reviewed_at": null,
  "reviewed_by": null,
  "rejection_reason": null
}
```

Major Errors: `400` (multipart/form-data 오류), `401`, `403`, `404`, `422`

### List My Verification Requests for a Target

- Method: `GET`
- URL: `/api/v1/targets/{target_id}/verification-requests`
- Auth: Yes
- Permission: target 소유자
- Description: 본인이 제출한 target의 verification request 목록을 조회한다. `document_file_path`, `stored_filename` 등 내부 파일 경로는 노출되지 않는다.

Response (200 OK):

```json
{
  "total": 1,
  "items": [
    {
      "id": 10,
      "verification_type": "IDENTITY_DOCUMENT",
      "status": "PENDING",
      "submitted_at": "2026-05-09T11:00:00",
      "reviewed_at": null,
      "rejection_reason": null
    }
  ]
}
```

Major Errors: `401`, `403`, `404`

### Get Verification Request Detail (user)

- Method: `GET`
- URL: `/api/v1/verification-requests/{request_id}`
- Auth: Yes
- Permission: request 제출자 또는 target 소유자
- Description: verification request의 상태 및 감사 목적의 메타데이터를 조회한다. 민감 파일 경로는 포함되지 않는다.

Response (200 OK):

```json
{
  "id": 10,
  "target_id": 1,
  "user_id": 1,
  "verification_type": "IDENTITY_DOCUMENT",
  "status": "PENDING",
  "submitted_at": "2026-05-09T11:00:00",
  "reviewed_at": null,
  "reviewed_by": null,
  "rejection_reason": null
}
```

Major Errors: `401`, `403`, `404`

## Admin: Verification Requests

관리자(혹은 검수 담당자)가 검토/승인/거절을 수행하는 엔드포인트입니다. 관리자 엔드포인트는 내부 파일 경로(`document_file_path`, `stored_filename`)나 원본 파일명(`original_filename`) 같은 심사에 필요한 정보를 포함할 수 있으며, 접근 권한/로그를 엄격히 제한해야 합니다.

### List Verification Requests (admin)

- Method: `GET`
- URL: `/api/v1/admin/verification-requests`
- Auth: Yes
- Permission: 관리자
- Description: 모든 verification request를 조회한다. `status` 쿼리를 통해 필터링 가능하다.

Request example:

```
GET /api/v1/admin/verification-requests?skip=0&limit=20
```

Response (200 OK):

```json
{
  "total": 2,
  "items": [
    {
      "id": 10,
      "target_id": 1,
      "user_id": 1,
      "verification_type": "IDENTITY_DOCUMENT",
      "status": "PENDING",
      "submitted_at": "2026-05-09T11:00:00",
      "document_file_path": "uploads/verifications/1/uuid.jpg",
      "original_filename": "id_card.jpg",
      "stored_filename": "uuid.jpg",
      "reviewed_at": null,
      "reviewed_by": null,
      "rejection_reason": null
    }
  ]
}
```

Major Errors: `401`, `403`, `422`

### List Verification Requests (admin) - filter by status

- Method: `GET`
- URL: `/api/v1/admin/verification-requests?status=PENDING`
- Auth: Yes
- Permission: 관리자
- Description: 특정 상태(`PENDING`, `APPROVED`, `REJECTED`)의 검수 대상을 조회한다.

Response: same as above but filtered.

Major Errors: `401`, `403`, `422`

### Approve Verification Request

- Method: `PATCH`
- URL: `/api/v1/admin/verification-requests/{request_id}/approve`
- Auth: Yes
- Permission: 관리자
- Description: 요청을 승인한다. 승인 시 해당 target에 대한 verification 상태를 `APPROVED`로 변경한다.

Request body: 없음

Response (200 OK):

```json
{
  "id": 10,
  "status": "APPROVED",
  "reviewed_at": "2026-05-09T11:30:00",
  "reviewed_by": 100
}
```

Major Errors: `401`, `403`, `404`, `422`

### Reject Verification Request

- Method: `PATCH`
- URL: `/api/v1/admin/verification-requests/{request_id}/reject`
- Auth: Yes
- Permission: 관리자
- Description: 요청을 거절한다. 거절 시 `rejection_reason`을 기록한다.

Request body (application/json):

```json
{
  "rejection_reason": "ID image is blurred"
}
```

Response (200 OK):

```json
{
  "id": 10,
  "status": "REJECTED",
  "reviewed_at": "2026-05-09T11:30:00",
  "reviewed_by": 100,
  "rejection_reason": "ID image is blurred"
}
```

Major Errors: `401`, `403`, `404`, `422`

### Delete Media

- Method: `DELETE`
- URL: `/api/v1/media/{media_id}`
- Auth: Yes
- Description: media 파일과 DB record를 삭제한다.

Request Body: 없음

Response:

```json
{
  "message": "Media deleted successfully"
}
```

Errors: `401`, `403`, `404`

## D. Persona

### Create Persona

- Method: `POST`
- URL: `/api/v1/targets/{target_id}/persona`
- Auth: Yes
- Description: target 정보와 media 목록을 기반으로 mock persona를 즉시 `READY` 상태로 생성한다. 단, 다음 전제 조건이 만족되어야 한다:
  - 해당 `target`에 대한 verification 상태가 `APPROVED` 여야 한다.
  - 사용자(또는 대상자)가 ConsentLog에 동의(또는 동의 기록이 존재)해야 한다.

Request Body: 없음

Response:

```json
{
  "id": 1,
  "target_id": 1,
  "status": "READY",
  "persona_name": "Mom Persona",
  "speaking_style": "Speaks warmly...",
  "personality_summary": "Mom is represented...",
  "memory_summary": "Built from 1 uploaded photo(s), 1 uploaded voice sample(s), and the target description.",
  "system_prompt": "You are Mom Persona...",
  "is_voice_profile_created": true,
  "is_consent_required": true,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00",
  "voice_profile": {
    "id": 1,
    "persona_id": 1,
    "reference_voice_file_path": "uploads/voices/1/uuid.mp3",
    "reference_voice_mime_type": "audio/mpeg",
    "reference_voice_duration": null,
    "voice_provider": null,
    "voice_id": null,
    "voice_name": null,
    "metadata": {
      "voice_media_count": 1,
      "representative_voice_file_path": "uploads/voices/1/uuid.mp3"
    },
    "created_at": "2026-05-09T10:00:00",
    "updated_at": "2026-05-09T10:00:00"
  }
}
```

Errors:

- `401` (인증 필요)
- `403` (권한 없음 또는 ConsentLog 미동의)
- `422` (전제 조건 불충분: verification 미승인 등)

### Get Persona

- Method: `GET`
- URL: `/api/v1/personas/{persona_id}`
- Auth: Yes
- Description: 본인 target에 연결된 persona 상세를 조회한다.

Request Body: 없음

Response: Create Persona response와 동일.

Errors: `401`, `403`, `404`

### Get Persona Status

- Method: `GET`
- URL: `/api/v1/personas/{persona_id}/status`
- Auth: Yes
- Description: persona 생성 상태만 조회한다.

Request Body: 없음

Response:

```json
{
  "persona_id": 1,
  "target_id": 1,
  "status": "READY"
}
```

Errors: `401`, `403`, `404`

## E. Persona Chat

### Create Chat

- Method: `POST`
- URL: `/api/v1/personas/{persona_id}/chats`
- Auth: Yes
- Description: persona와 대화할 chat session을 생성한다.

Request:

```json
{
  "title": "First chat"
}
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "persona_id": 1,
  "title": "First chat",
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `403`, `404`

### List Chats

- Method: `GET`
- URL: `/api/v1/personas/{persona_id}/chats`
- Auth: Yes
- Description: persona의 내 chat 목록을 조회한다.

Request Body: 없음

Response:

```json
[
  {
    "id": 1,
    "user_id": 1,
    "persona_id": 1,
    "title": "First chat",
    "deleted_at": null,
    "created_at": "2026-05-09T10:00:00",
    "updated_at": "2026-05-09T10:00:00"
  }
]
```

Errors: `401`, `403`, `404`

### Send Message

- Method: `POST`
- URL: `/api/v1/chats/{chat_id}/messages`
- Auth: Yes
- Description: user message를 저장하고 mock persona reply를 생성해 함께 반환한다.

Request:

```json
{
  "message_type": "TEXT",
  "content": "Tell me about this memory.",
  "audio_file_path": null
}
```

Response:

```json
{
  "user_message": {
    "id": 1,
    "chat_id": 1,
    "sender_type": "USER",
    "message_type": "TEXT",
    "content": "Tell me about this memory.",
    "audio_file_path": null,
    "is_ai_generated": false,
    "created_at": "2026-05-09T10:00:00",
    "deleted_at": null
  },
  "persona_message": {
    "id": 2,
    "chat_id": 1,
    "sender_type": "PERSONA",
    "message_type": "TEXT",
    "content": "Mom Persona: ...",
    "audio_file_path": null,
    "is_ai_generated": true,
    "created_at": "2026-05-09T10:00:01",
    "deleted_at": null
  }
}
```

Errors: `401`, `403`, `404`, `422`

### List Messages

- Method: `GET`
- URL: `/api/v1/chats/{chat_id}/messages`
- Auth: Yes
- Description: chat messages를 `created_at` 오름차순으로 조회한다.

Request Body: 없음

Response:

```json
[
  {
    "id": 1,
    "chat_id": 1,
    "sender_type": "USER",
    "message_type": "TEXT",
    "content": "Tell me about this memory.",
    "audio_file_path": null,
    "is_ai_generated": false,
    "created_at": "2026-05-09T10:00:00",
    "deleted_at": null
  }
]
```

Errors: `401`, `403`, `404`

## F. AI Interview

### Create Interview

- Method: `POST`
- URL: `/api/v1/interviews`
- Auth: Yes
- Description: AI interview session을 생성한다.

Request:

```json
{
  "session_type": "SELF_STORY",
  "title": "My story interview",
  "target_id": null,
  "photo_memory_id": null
}
```

`TARGET_PROFILE`은 `target_id`가 필요하다. `PHOTO_MEMORY`는 `photo_memory_id`를 연결할 수 있다.

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "target_id": null,
  "photo_memory_id": null,
  "session_type": "SELF_STORY",
  "title": "My story interview",
  "status": "IN_PROGRESS",
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `403`, `404`, `422`

### Get Interview Detail

- Method: `GET`
- URL: `/api/v1/interviews/{session_id}`
- Auth: Yes
- Description: session, questions, answers를 함께 조회한다.

Request Body: 없음

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "target_id": null,
  "photo_memory_id": null,
  "session_type": "SELF_STORY",
  "title": "My story interview",
  "status": "IN_PROGRESS",
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00",
  "questions": [
    {
      "id": 1,
      "session_id": 1,
      "question_text": "오늘 가장 기억에 남는 일은 무엇인가요?",
      "question_type": "memory",
      "order_index": 1,
      "created_at": "2026-05-09T10:00:01",
      "answers": [
        {
          "id": 1,
          "session_id": 1,
          "question_id": 1,
          "answer_text": "A memory worth preserving.",
          "answer_audio_path": null,
          "deleted_at": null,
          "created_at": "2026-05-09T10:00:02",
          "updated_at": "2026-05-09T10:00:02"
        }
      ]
    }
  ]
}
```

Errors: `401`, `403`, `404`

### Generate Question

- Method: `POST`
- URL: `/api/v1/interviews/{session_id}/questions`
- Auth: Yes
- Description: session type에 맞는 mock question을 생성하고 저장한다.

Request:

```json
{
  "question_type": "memory"
}
```

Response:

```json
{
  "id": 1,
  "session_id": 1,
  "question_text": "오늘 가장 기억에 남는 일은 무엇인가요?",
  "question_type": "memory",
  "order_index": 1,
  "created_at": "2026-05-09T10:00:01",
  "answers": []
}
```

Errors: `401`, `403`, `404`

### Submit Answer

- Method: `POST`
- URL: `/api/v1/interviews/{session_id}/answers`
- Auth: Yes
- Description: question에 대한 답변을 저장한다.

Request:

```json
{
  "question_id": 1,
  "answer_text": "A memory worth preserving.",
  "answer_audio_path": null
}
```

Response:

```json
{
  "id": 1,
  "session_id": 1,
  "question_id": 1,
  "answer_text": "A memory worth preserving.",
  "answer_audio_path": null,
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:02",
  "updated_at": "2026-05-09T10:00:02"
}
```

Errors: `401`, `403`, `404`, `422`

## G. PhotoMemory

### Upload PhotoMemory

- Method: `POST`
- URL: `/api/v1/photo-memories`
- Auth: Yes
- Description: 스토리북 생성을 위한 개인 사진을 업로드한다.
- Content-Type: `multipart/form-data`

Request:

```text
file=@birthday.jpg; type=image/jpeg
title=Birthday
description=Family birthday photo
taken_at=2026-05-09T10:00:00
location=Seoul
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "title": "Birthday",
  "description": "Family birthday photo",
  "file_path": "uploads/photo_memories/1/uuid.jpg",
  "original_filename": "birthday.jpg",
  "stored_filename": "uuid.jpg",
  "mime_type": "image/jpeg",
  "file_size": 12345,
  "taken_at": "2026-05-09T10:00:00",
  "location": "Seoul",
  "ai_caption": null,
  "emotion_keywords": null,
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `400`, `401`, `422`

### List PhotoMemories

- Method: `GET`
- URL: `/api/v1/photo-memories`
- Auth: Yes
- Description: 내 삭제되지 않은 PhotoMemory 목록을 조회한다.

Request Body: 없음

Response: PhotoMemory 배열.

Errors: `401`

### Get PhotoMemory

- Method: `GET`
- URL: `/api/v1/photo-memories/{photo_memory_id}`
- Auth: Yes
- Description: 본인 소유 PhotoMemory를 조회한다.

Request Body: 없음

Response: PhotoMemory response.

Errors: `401`, `403`, `404`

### Delete PhotoMemory

- Method: `DELETE`
- URL: `/api/v1/photo-memories/{photo_memory_id}`
- Auth: Yes
- Description: 실제 파일을 삭제하고 metadata record는 soft delete 처리한다.

Request Body: 없음

Response:

```json
{
  "message": "Photo memory deleted successfully"
}
```

Errors: `401`, `403`, `404`

## H. StoryBook

### Create StoryBook

- Method: `POST`
- URL: `/api/v1/storybooks`
- Auth: Yes
- Description: interview 또는 photo memory 기반 mock storybook과 chapters를 생성한다.

Request:

```json
{
  "title": "My Story",
  "interview_session_id": 1,
  "photo_memory_id": null,
  "visibility": "PRIVATE"
}
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "photo_memory_id": null,
  "interview_session_id": 1,
  "title": "My Story",
  "summary": "SELF_STORY 자료를 바탕으로 생성한 'My Story' 스토리북입니다.",
  "source_type": "SELF_STORY",
  "status": "GENERATED",
  "visibility": "PRIVATE",
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00",
  "chapters": [
    {
      "id": 1,
      "storybook_id": 1,
      "title": "Chapter 1: 오늘 가장 기억에 남는 일은 무엇인가요?",
      "content": "오늘 가장 기억에 남는 일은 무엇인가요?\n\nA memory worth preserving.",
      "summary": "A memory worth preserving.",
      "order_index": 1,
      "deleted_at": null,
      "created_at": "2026-05-09T10:00:00",
      "updated_at": "2026-05-09T10:00:00"
    }
  ]
}
```

Errors: `401`, `403`, `404`, `422`

### List StoryBooks

- Method: `GET`
- URL: `/api/v1/storybooks`
- Auth: Yes
- Description: 내 삭제되지 않은 StoryBook 목록을 최신순으로 조회한다.

Request Body: 없음

Response: StoryBook 배열. 챕터는 포함하지 않는다.

Errors: `401`

### Get StoryBook

- Method: `GET`
- URL: `/api/v1/storybooks/{storybook_id}`
- Auth: Yes
- Description: 본인 소유 StoryBook과 chapters를 조회한다.

Request Body: 없음

Response: Create StoryBook response와 동일한 구조.

Errors: `401`, `403`, `404`

### List Chapters

- Method: `GET`
- URL: `/api/v1/storybooks/{storybook_id}/chapters`
- Auth: Yes
- Description: 삭제되지 않은 chapters를 `order_index` 오름차순으로 조회한다.

Request Body: 없음

Response: StoryChapter 배열.

Errors: `401`, `403`, `404`

### Regenerate StoryBook

- Method: `POST`
- URL: `/api/v1/storybooks/{storybook_id}/regenerate`
- Auth: Yes
- Description: 기존 chapters를 soft delete 처리하고 source data 기반으로 다시 생성한다.

Request Body: 없음

Response: StoryBook detail response.

Errors: `401`, `403`, `404`

## I. ShareLink

### Create ShareLink

- Method: `POST`
- URL: `/api/v1/storybooks/{storybook_id}/share-links`
- Auth: Yes
- Description: 내 StoryBook에 대한 token 공유 링크를 생성한다. StoryBook visibility는 `LINK`로 변경된다.

Request:

```json
{
  "expires_at": "2026-12-31T23:59:59"
}
```

Response:

```json
{
  "id": 1,
  "storybook_id": 1,
  "owner_id": 1,
  "token": "random-url-safe-token",
  "is_active": true,
  "expires_at": "2026-12-31T23:59:59",
  "disabled_at": null,
  "share_url": "/api/v1/share/random-url-safe-token",
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `403`, `404`

### List ShareLinks

- Method: `GET`
- URL: `/api/v1/storybooks/{storybook_id}/share-links`
- Auth: Yes
- Description: 내 StoryBook의 공유 링크 목록을 조회한다.

Request Body: 없음

Response: ShareLink 배열.

Errors: `401`, `403`, `404`

### Public Share Read

- Method: `GET`
- URL: `/api/v1/share/{token}`
- Auth: No
- Description: token을 가진 사용자가 StoryBook을 읽기 전용으로 조회한다.

Request Body: 없음

Response:

```json
{
  "title": "My Story",
  "summary": "SELF_STORY 자료를 바탕으로 생성한 'My Story' 스토리북입니다.",
  "visibility": "LINK",
  "chapters": [
    {
      "title": "Chapter 1: 오늘 가장 기억에 남는 일은 무엇인가요?",
      "content": "오늘 가장 기억에 남는 일은 무엇인가요?\n\nA memory worth preserving.",
      "summary": "A memory worth preserving.",
      "order_index": 1
    }
  ]
}
```

응답에는 `owner_id`, 내부 파일 경로, user id 등 민감 필드를 포함하지 않는다.

Errors: `403`, `404`

### Disable ShareLink

- Method: `PATCH`
- URL: `/api/v1/share-links/{share_link_id}/disable`
- Auth: Yes
- Description: 내가 생성한 공유 링크를 비활성화한다.

Request Body: 없음

Response:

```json
{
  "id": 1,
  "is_active": false,
  "disabled_at": "2026-05-09T10:30:00"
}
```

Errors: `401`, `403`, `404`

## J. MemoryGroup

### Create Group

- Method: `POST`
- URL: `/api/v1/groups`
- Auth: Yes
- Description: 그룹을 생성한다. 생성자는 자동으로 `OWNER` 멤버가 된다.

Request:

```json
{
  "name": "Family",
  "description": "Family memories"
}
```

Response:

```json
{
  "id": 1,
  "owner_id": 1,
  "name": "Family",
  "description": "Family memories",
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `422`

### List Groups

- Method: `GET`
- URL: `/api/v1/groups`
- Auth: Yes
- Description: 내가 멤버로 속한 삭제되지 않은 그룹 목록을 조회한다.

Request Body: 없음

Response: MemoryGroup 배열.

Errors: `401`

### Get Group

- Method: `GET`
- URL: `/api/v1/groups/{group_id}`
- Auth: Yes
- Description: 그룹 정보와 내 role을 조회한다.

Request Body: 없음

Response:

```json
{
  "id": 1,
  "owner_id": 1,
  "name": "Family",
  "description": "Family memories",
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00",
  "my_role": "OWNER"
}
```

Errors: `401`, `403`, `404`

### Add Group Member

- Method: `POST`
- URL: `/api/v1/groups/{group_id}/members`
- Auth: Yes
- Description: OWNER가 그룹 멤버를 추가한다. 이미 멤버면 기존 멤버를 반환한다.

Request:

```json
{
  "user_id": 2,
  "role": "MEMBER"
}
```

Response:

```json
{
  "id": 2,
  "group_id": 1,
  "user_id": 2,
  "role": "MEMBER",
  "deleted_at": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `403`, `404`, `422`

### List Group Members

- Method: `GET`
- URL: `/api/v1/groups/{group_id}/members`
- Auth: Yes
- Description: 그룹 멤버 목록을 조회한다.

Request Body: 없음

Response: GroupMember 배열.

Errors: `401`, `403`, `404`

### Share StoryBook To Group

- Method: `POST`
- URL: `/api/v1/groups/{group_id}/storybooks/{storybook_id}`
- Auth: Yes
- Description: 내 StoryBook을 그룹에 공유한다. StoryBook visibility는 `GROUP`으로 변경된다.

Request Body: 없음

Response:

```json
{
  "id": 1,
  "group_id": 1,
  "storybook_id": 1,
  "shared_by": 1,
  "created_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `403`, `404`

### List Group StoryBooks

- Method: `GET`
- URL: `/api/v1/groups/{group_id}/storybooks`
- Auth: Yes
- Description: 그룹에 공유된 StoryBook 목록을 조회한다. 내부 파일 경로나 민감 데이터는 반환하지 않는다.

Request Body: 없음

Response:

```json
[
  {
    "id": 1,
    "title": "My Story",
    "summary": "SELF_STORY 자료를 바탕으로 생성한 'My Story' 스토리북입니다.",
    "visibility": "GROUP",
    "created_at": "2026-05-09T10:00:00"
  }
]
```

Errors: `401`, `403`, `404`

## K. DeletionRequest

### Create DeletionRequest

- Method: `POST`
- URL: `/api/v1/deletion-requests`
- Auth: Yes
- Description: 삭제 요청을 생성하고 MVP에서는 즉시 처리한다.

Request:

```json
{
  "target_type": "PHOTO_MEMORY",
  "target_id": 1,
  "reason": "remove sensitive photo"
}
```

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "target_type": "PHOTO_MEMORY",
  "target_id": 1,
  "reason": "remove sensitive photo",
  "status": "COMPLETED",
  "processed_at": "2026-05-09T10:00:00",
  "error_message": null,
  "created_at": "2026-05-09T10:00:00",
  "updated_at": "2026-05-09T10:00:00"
}
```

Errors: `401`, `403`, `404`, `422`

Note on `VERIFICATION_REQUEST` deletion:

- `target_type`에 `VERIFICATION_REQUEST`를 지정하면 해당 verification의 실제 문서 파일(document file)을 즉시 삭제하고, 내부 파일 경로(`document_file_path`), 내부 저장 파일명(`stored_filename`), (가능한 경우) `original_filename`을 NULL 처리하여 민감 데이터를 DB에 남기지 않습니다. 다만 `deleted_at` 등 운영·감사용 최소 메타데이터는 기록으로 남겨 감사가 가능하도록 합니다.

Major Errors: `401`, `403`, `404`, `422`

### List DeletionRequests

- Method: `GET`
- URL: `/api/v1/deletion-requests`
- Auth: Yes
- Description: 내 삭제 요청 목록을 최신순으로 조회한다.

Request Body: 없음

Response: DeletionRequest 배열.

Errors: `401`

### Get DeletionRequest

- Method: `GET`
- URL: `/api/v1/deletion-requests/{request_id}`
- Auth: Yes
- Description: 내 삭제 요청 상세를 조회한다.

Request Body: 없음

Response: DeletionRequest response.

Errors: `401`, `403`, `404`

---

## L. AI and Speech Pipeline

This section summarizes the frontend-facing contract for the AI and voice features.
Existing API paths and response schemas remain unchanged unless a new endpoint is listed here.

### Provider Settings

Configure providers with `.env` values. Do not commit real external API keys to GitHub.

| Variable | Example | Notes |
| --- | --- | --- |
| `GEMINI_API_KEY` | `AIza...` | Required only for real Gemini calls. If empty, the backend uses mock LLM output. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model used for persona replies, interview questions, and storybook generation. |
| `STT_PROVIDER` | `mock` or `faster_whisper` | Speech-to-text provider. `test` always uses `mock`. |
| `WHISPER_MODEL_SIZE` | `base` or `small` | faster-whisper model size. CPU mode is expected. |
| `TTS_PROVIDER` | `mock` or `melotts` | Text-to-speech provider. `test` always uses `mock`. |
| `VOICE_CLONE_PROVIDER` | `mock` or `openvoice` | Voice cloning provider. `test` always uses `mock`. |

Provider fallback rules:

- `ENVIRONMENT=test` always uses mock providers.
- If `GEMINI_API_KEY` is missing, LLM calls use `MockLLMService`.
- If Gemini fails or returns invalid storybook JSON, the backend falls back to mock output.
- MeloTTS/OpenVoice imports are optional; missing packages must not crash the server.

### PersonaChat Text Message

- Method: `POST`
- URL: `/api/v1/chats/{chat_id}/messages`
- Auth: Yes
- Content-Type: `application/json`
- Description: Saves the user text message, generates a persona reply through `LLMService`, and optionally generates TTS audio for the persona reply.

Request body:

```json
{
  "message_type": "TEXT",
  "content": "오늘 기분이 조금 복잡했어.",
  "audio_file_path": null,
  "generate_audio": false
}
```

Notes:

- `generate_audio` is optional and defaults to `false`.
- When `generate_audio=true`, the backend calls `TTSService.synthesize(...)`.
- The persona reply keeps `is_ai_generated=true`.
- The LLM prompt includes persona name, speaking style, personality summary, memory summary, system prompt, recent messages, and the current user message.
- Sensitive medical, legal, and financial advice is discouraged by the internal system prompt.

Response:

The existing `PersonaMessagePairResponse` is returned:

- `user_message`: saved user message.
- `persona_message`: saved persona reply.
- `persona_message.audio_file_path`: `null` unless TTS generation was requested and succeeded.

### PersonaChat Audio Message

- Method: `POST`
- URL: `/api/v1/chats/{chat_id}/audio`
- Auth: Yes
- Content-Type: `multipart/form-data`
- Description: Uploads an audio file, transcribes it with `STTService`, saves the transcribed text as a user audio message, then generates a persona reply.

Form fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `file` | file | Yes | MIME type must start with `audio/`. Otherwise the API returns `400`. |
| `generate_audio` | boolean | No | If `true`, persona reply audio is generated through TTS. |

Storage behavior:

- Uploaded audio is stored under `uploads/chat_audio/{user_id}/`.
- The user `PersonaMessage` is saved with `sender_type=USER`, `message_type=AUDIO`, `content=<STT text>`, and `audio_file_path=<saved audio path>`.
- The persona reply is saved as a text message. If TTS is requested, its `audio_file_path` points to the generated audio file.

Example request:

```bash
curl -X POST "http://localhost:8000/api/v1/chats/{chat_id}/audio" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@voice.m4a;type=audio/mp4" \
  -F "generate_audio=true"
```

### StoryBook Gemini Generation

StoryBook creation and regeneration use `LLMService.generate_storybook(...)`.

Affected endpoints:

- `POST /api/v1/storybooks`
- `POST /api/v1/storybooks/{storybook_id}/regenerate`

The backend passes interview question/answer data and optional photo memory data to Gemini when available. Gemini is instructed to return JSON in this shape:

```json
{
  "title": "...",
  "summary": "...",
  "chapters": [
    {
      "title": "...",
      "summary": "...",
      "content": "..."
    }
  ]
}
```

Frontend contract:

- Public request and response schemas are unchanged.
- At least one chapter is guaranteed.
- If Gemini fails or the JSON cannot be parsed, mock storybook content is used.

### Persona Voice Profile

Voice profile endpoints are available for the voice cloning MVP.

#### Create Voice Profile

- Method: `POST`
- URL: `/api/v1/personas/{persona_id}/voice-profile`
- Auth: Yes
- Description: Creates or requests creation of a voice profile for the persona by using voice media attached to the persona target.

Rules:

- The authenticated user must own the persona.
- The persona target must have at least one voice media item.
- If no reference voice media exists, the API returns `400`.
- In `ENVIRONMENT=test`, `MockVoiceCloneService` creates a `READY` profile immediately.
- With a real OpenVoice provider, the profile can be created as `PENDING`.
- Service-layer TODO checkpoints remain for target verification approval and explicit voice cloning consent logs.

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/personas/{persona_id}/voice-profile" \
  -H "Authorization: Bearer <access_token>"
```

#### Get Voice Profile

- Method: `GET`
- URL: `/api/v1/personas/{persona_id}/voice-profile`
- Auth: Yes
- Description: Returns the current persona voice profile.

Important response fields:

```json
{
  "id": 1,
  "persona_id": 1,
  "target_id": 1,
  "provider": "mock",
  "model_name": null,
  "status": "READY",
  "reference_audio_count": 1,
  "reference_audio_total_seconds": null,
  "voice_profile_path": "uploads/voice_profiles/...",
  "sample_audio_path": "uploads/voice_samples/...",
  "error_message": null,
  "created_at": "2026-05-12T00:00:00",
  "updated_at": "2026-05-12T00:00:00"
}
```

Supported statuses:

- `PENDING`
- `READY`
- `FAILED`
- `DISABLED`

---

## M. Granular Consent API

Consent is stored as an append-only history with explicit revocation state.
Frontend clients should use the latest record for the same `user_id + target_id + consent_type` as the current state.

### Supported Consent Types

Use these values in request JSON:

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

Legacy values such as `photo_collection`, `voice_collection`, `persona_creation`, and `storybook_share` are still accepted for compatibility, but new frontend work should use the granular values above.

### Create Consent

- Method: `POST`
- URL: `/api/v1/consents`
- Auth: Yes
- Description: Creates a new consent history row.

Request:

```json
{
  "target_id": 1,
  "consent_type": "ai_persona_creation_consent",
  "consent_version": "2026-05-12",
  "consent_text_snapshot": "User agreed to AI persona creation for this target.",
  "is_agreed": true
}
```

Notes:

- `target_id` is required for target-scoped consent types.
- `target_id` must belong to the logged-in user.
- Global consent types such as `storybook_share_consent`, `group_share_consent`, `data_retention_consent`, and `third_party_ai_processing_consent` may use `target_id=null`.
- `is_consented` and `details` are legacy-compatible fields; prefer `is_agreed` and `consent_text_snapshot`.

Response:

```json
{
  "id": 1,
  "user_id": 1,
  "target_id": 1,
  "consent_type": "ai_persona_creation_consent",
  "consent_version": "2026-05-12",
  "consent_text_snapshot": "User agreed to AI persona creation for this target.",
  "is_agreed": true,
  "agreed_at": "2026-05-12T00:00:00",
  "revoked_at": null,
  "ip_address": "127.0.0.1",
  "user_agent": "Mozilla/5.0",
  "is_consented": true,
  "details": null,
  "created_at": "2026-05-12T00:00:00",
  "updated_at": "2026-05-12T00:00:00"
}
```

### List My Consents

- Method: `GET`
- URL: `/api/v1/consents`
- Auth: Yes
- Description: Lists all consent records for the logged-in user, newest first.

### List Target Consents

- Method: `GET`
- URL: `/api/v1/targets/{target_id}/consents`
- Auth: Yes
- Description: Lists all consent records for one owned target, newest first.

### Revoke Consent

- Method: `PATCH`
- URL: `/api/v1/consents/{consent_id}/revoke`
- Auth: Yes
- Description: Revokes a consent record owned by the logged-in user.

Response behavior:

- `is_agreed=false`
- `is_consented=false`
- `revoked_at` is set

### Consent Gates

Persona creation now requires active latest consent for:

- `ai_persona_creation_consent`
- `ai_response_notice_consent`

Media upload requires:

- Image upload: `photo_upload_consent`
- Voice upload: `voice_upload_consent`

Voice profile / voice cloning requires:

- `voice_upload_consent`
- `voice_cloning_consent`

Sharing requires:

- Share link: `storybook_share_consent`
- Group share: `group_share_consent`

A revoked consent is not valid. If a newer record for the same target/type has `is_agreed=false`, backend policy checks fail with `403`.
