# Remory API Test Scenario

이 문서는 pytest 통합 테스트에서 검증하는 전체 사용자 흐름을 사람이 읽을 수 있게 정리한 것이다.

## Test Environment

- Test runner: `pytest`
- Client: FastAPI `TestClient`
- Test DB: in-memory SQLite
- Upload files: test byte content로 생성
  - image: `b"fake image content"`, MIME `image/jpeg`
  - voice: `b"fake audio content"`, MIME `audio/mpeg`
- 테스트 전후 `uploads/images`, `uploads/voices`, `uploads/photo_memories` 산출물을 정리한다.

## Full User Flow

### 1. Health Check

1. `GET /health`
2. API 서버가 정상 응답하는지 확인한다.
3. 기대 결과: `200 OK`, `{"status": "ok"}`

### 2. Auth

1. `POST /api/v1/auth/register`
2. 테스트 사용자 회원가입을 수행한다.
3. 응답에서 `access_token`, `refresh_token`, `user`를 확인한다.
4. `POST /api/v1/auth/login`
5. 같은 계정으로 로그인한다.
6. `GET /api/v1/auth/me`
7. Bearer token으로 현재 사용자 정보를 조회한다.

### 3. Target

1. `POST /api/v1/targets`
2. `Mom` target을 생성한다.
3. `GET /api/v1/targets`
4. 내 target 목록에 생성한 target이 있는지 확인한다.
5. `GET /api/v1/targets/{target_id}`
6. target 상세 조회가 되는지 확인한다.
7. 다른 사용자 token으로 같은 target 조회 시 `403` 또는 `404`가 반환되는지 확인한다.

### 4. TargetMedia

1. `POST /api/v1/targets/{target_id}/media`
2. `media_type=image`, `image/jpeg` 파일을 업로드한다.
3. `POST /api/v1/targets/{target_id}/media`
4. `media_type=voice`, `audio/mpeg` 파일을 업로드한다.
5. 실제 파일이 `uploads/images/...`, `uploads/voices/...`에 생성되는지 확인한다.
6. `GET /api/v1/targets/{target_id}/media`
7. image/voice 2개 목록이 조회되는지 확인한다.
8. 다른 사용자가 media 업로드를 시도하면 `403` 또는 `404`가 반환되는지 확인한다.

### 5. Persona

1. `POST /api/v1/targets/{target_id}/persona`
2. target 정보와 media count 기반 mock persona를 생성한다.
3. 기대 결과: `status=READY`, `persona_name` 존재.
4. `GET /api/v1/personas/{persona_id}`
5. persona 상세와 voice profile metadata를 확인한다.
6. `GET /api/v1/personas/{persona_id}/status`
7. `READY` 상태가 반환되는지 확인한다.
8. 다른 사용자 접근은 `403` 또는 `404`인지 확인한다.

### Verification -> Persona creation flow (end-to-end)

이 시나리오는 verification이 persona 생성 흐름에 미치는 영향을 검증한다.

1. `POST /api/v1/targets` — Target 생성
   - 기대: `201 Created` 및 target id 반환
2. `POST /api/v1/targets/{target_id}/verification-requests` — VerificationRequest 제출 (multipart/form-data)
   - 업로드 파일이 `uploads/verifications/{user_id}/...`에 생성되는지 확인
   - 기대: `201 Created`, status=`PENDING`
3. `POST /api/v1/targets/{target_id}/persona` — Persona 생성 시도
   - 기대: verification이 승인되지 않았으므로 persona 생성이 실패해야 함 (`422` 또는 `403`)
4. 관리자 계정으로 `PATCH /api/v1/admin/verification-requests/{request_id}/approve` — Admin 승인
   - 기대: status=`APPROVED`, `reviewed_by` 및 `reviewed_at`가 기록됨
5. 다시 `POST /api/v1/targets/{target_id}/persona` — Persona 생성
   - 기대: verification이 승인되었으므로 persona 생성 성공 (`201` 또는 `200`, `status=READY`)
6. `POST /api/v1/deletion-requests` with `target_type=VERIFICATION_REQUEST` — VerificationRequest 삭제 요청
   - 기대: 삭제 요청 처리 후 실제 document 파일이 삭제되고, DB의 `document_file_path`, `stored_filename`, `original_filename` 같은 민감 필드가 NULL 처리되며 `deleted_at`이 기록됨
7. 파일 시스템 확인: 삭제된 파일이 더 이상 존재하지 않는지 확인

이 흐름은 프론트엔드가 verification 상태에 의존해 persona 생성 버튼을 활성화/비활성화하거나, 파일 노출을 시도하지 않도록 설계되었는지 검증한다.

### 6. PersonaChat / PersonaMessage

1. `POST /api/v1/personas/{persona_id}/chats`
2. persona chat을 생성한다.
3. `GET /api/v1/personas/{persona_id}/chats`
4. chat 목록에 생성된 chat이 포함되는지 확인한다.
5. `POST /api/v1/chats/{chat_id}/messages`
6. user message를 전송한다.
7. user message와 mock persona reply가 함께 생성되는지 확인한다.
8. `GET /api/v1/chats/{chat_id}/messages`
9. `USER`, `PERSONA` 순서로 조회되는지 확인한다.
10. 다른 사용자가 chat에 message를 보내면 `403` 또는 `404`인지 확인한다.

### 7. AIInterviewSession

1. `POST /api/v1/interviews`
2. `SELF_STORY` session을 생성한다.
3. `POST /api/v1/interviews/{session_id}/questions`
4. mock question을 생성한다.
5. `POST /api/v1/interviews/{session_id}/answers`
6. question에 대한 answer를 저장한다.
7. `GET /api/v1/interviews/{session_id}`
8. session, question, answer가 nested 구조로 조회되는지 확인한다.
9. `TARGET_PROFILE`인데 `target_id`가 없으면 `422`인지 확인한다.
10. 다른 사용자 접근은 `403` 또는 `404`인지 확인한다.

### 8. PhotoMemory

1. `POST /api/v1/photo-memories`
2. multipart form으로 사진을 업로드한다.
3. 실제 파일이 `uploads/photo_memories/{user_id}/...`에 생성되는지 확인한다.
4. `GET /api/v1/photo-memories`
5. 내 PhotoMemory 목록을 확인한다.
6. `GET /api/v1/photo-memories/{photo_memory_id}`
7. 상세 조회를 확인한다.
8. `text/plain` 파일 업로드는 `400`인지 확인한다.
9. 다른 사용자 접근은 `403` 또는 `404`인지 확인한다.

### 9. StoryBook / StoryChapter

1. `POST /api/v1/storybooks`
2. interview session 기반 StoryBook을 생성한다.
3. mock summary와 chapter가 생성되는지 확인한다.
4. `GET /api/v1/storybooks`
5. 내 StoryBook 목록을 확인한다.
6. `GET /api/v1/storybooks/{storybook_id}`
7. StoryBook 상세와 chapters를 확인한다.
8. `GET /api/v1/storybooks/{storybook_id}/chapters`
9. chapter가 `order_index` 오름차순으로 조회되는지 확인한다.
10. `POST /api/v1/storybooks/{storybook_id}/regenerate`
11. 기존 source data 기반으로 재생성되는지 확인한다.
12. 다른 사용자 접근은 `403` 또는 `404`인지 확인한다.

### 10. ShareLink

1. `POST /api/v1/storybooks/{storybook_id}/share-links`
2. 공유 token과 `share_url`을 생성한다.
3. StoryBook visibility가 `LINK`로 변경되는지 확인한다.
4. `GET /api/v1/share/{token}`
5. 인증 없이 public read 응답을 조회한다.
6. 응답에 `owner_id`, 내부 파일 경로 등 민감 데이터가 없는지 확인한다.
7. `PATCH /api/v1/share-links/{share_link_id}/disable`
8. 공유 링크를 비활성화한다.
9. 비활성화된 token 조회가 `403`인지 확인한다.
10. 다른 사용자가 share link를 생성하려 하면 `403` 또는 `404`인지 확인한다.

### 11. MemoryGroup / GroupMember / GroupStoryBook

1. `POST /api/v1/groups`
2. 그룹을 생성한다.
3. 생성자가 자동으로 `OWNER`가 되는지 `GET /api/v1/groups/{group_id}`로 확인한다.
4. `POST /api/v1/groups/{group_id}/members`
5. 두 번째 사용자를 `MEMBER`로 추가한다.
6. `GET /api/v1/groups/{group_id}/members`
7. `OWNER`, `MEMBER`가 조회되는지 확인한다.
8. `POST /api/v1/groups/{group_id}/storybooks/{storybook_id}`
9. owner의 StoryBook을 그룹에 공유한다.
10. StoryBook visibility가 `GROUP`으로 변경되는지 확인한다.
11. `GET /api/v1/groups/{group_id}/storybooks`
12. 그룹 멤버가 공유 StoryBook 목록을 조회할 수 있는지 확인한다.
13. 응답에 내부 파일 경로나 `user_id` 같은 민감 데이터가 없는지 확인한다.
14. OWNER가 아닌 멤버가 멤버 추가를 시도하면 `403`인지 확인한다.

### 12. DeletionRequest

1. `POST /api/v1/deletion-requests`
2. `PHOTO_MEMORY` 삭제 요청을 생성한다.
3. 즉시 `COMPLETED`가 되고 실제 파일이 삭제되는지 확인한다.
4. `POST /api/v1/deletion-requests`
5. `TARGET_MEDIA` 삭제 요청을 생성한다.
6. 실제 media file이 삭제되는지 확인한다.
7. StoryBook에 ShareLink를 만든 뒤 `STORYBOOK` 삭제 요청을 생성한다.
8. StoryBook soft delete 후 share token 접근이 `403` 또는 `404`인지 확인한다.
9. `GET /api/v1/deletion-requests`
10. 내 삭제 요청 목록을 최신순으로 확인한다.
11. `GET /api/v1/deletion-requests/{request_id}`
12. 삭제 요청 상세를 확인한다.
13. 다른 사용자가 내 리소스에 삭제 요청을 만들면 `403` 또는 `404`인지 확인한다.

## Commands

```powershell
pytest
pytest -v
pytest tests/test_08_storybook.py -v
```
