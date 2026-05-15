# 03. Frontend Integration (Code-Based)

## OpenVoice Integration Notes (2026-05-15)
- Voice profile API flow is unchanged:
  1. `POST /api/v1/personas/{persona_id}/voice-profile`
  2. `POST /api/v1/personas/{persona_id}/voice-profile/evaluate`
  3. `PATCH /api/v1/personas/{persona_id}/voice-profile/user-confirm`
- Frontend should check:
  - `status` (`READY`, `FAILED`, `NEEDS_MORE_SAMPLES`, ...)
  - `error_message` when not `READY`
  - `sample_audio_path` after evaluate success
- `user-confirm` should be enabled only when `status === "READY"`.
- For realtime voice call:
  - backend requires READY + (`USER_CONFIRMED` or `ADMIN_APPROVED`)
  - if OpenVoice synthesis fails in production/no-failover mode, backend returns websocket error instead of hidden mock audio.

## 1) Base URL / WS URL
- REST Base URL: `/api/v1`
- Health URL: `/health`
- WebSocket Base URL: `/api/v1/ws`
- VoiceCall WS: `/api/v1/ws/personas/{persona_id}/voice?token=<access_token>`

## 2) Authorization Header 규칙
- 인증 필요 API는 `Authorization: Bearer <access_token>`
- 미인증 API: `/auth/*`(me 제외), `/share/{token}`, `/health`
- Admin API는 동일 헤더를 사용하고 서버에서 `role == ADMIN` 검사

## 3) Access/Refresh Token 처리
- 로그인/회원가입 응답: `access_token`, `refresh_token`, `user`
- 권장 처리
  1. `access_token`은 메모리 우선, 필요 시 안전한 저장소 사용
  2. `401` 발생 시 `POST /auth/refresh-token`으로 재발급 시도
  3. 재발급 실패 시 로그인 화면 이동
- 로그아웃: `POST /auth/logout`에 `refresh_token` 전달

## 4) 사용자/관리자 분기
- `GET /auth/me` 응답의 `role` 사용 (`USER` 또는 `ADMIN`)
- 프론트 권장 분기
  - `role === "ADMIN"`이면 관리자 메뉴 노출
  - 일반 화면은 role과 무관하게 API 실패(`403`) 처리 유지

## 5) 파일 URL 처리 방식
- `file_path`, `audio_file_path`는 deprecated
- 반드시 API URL 필드 사용
  - PhotoMemory: `image_api_url`
  - TargetMedia: `file_api_url`
  - PersonaMessage: `audio_api_url`
- 금지:
  - `<img src={API_BASE + file_path}>`
  - `<audio src={API_BASE + audio_file_path}>`

### 보호 파일 fetch 공통 예시
```ts
export async function fetchProtectedBlob(apiUrl: string, accessToken: string) {
  const res = await fetch(apiUrl, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });

  if (res.status === 401) throw new Error("LOGIN_REQUIRED");
  if (res.status === 403) throw new Error("FORBIDDEN");
  if (res.status === 404) throw new Error("FILE_NOT_FOUND");
  if (!res.ok) throw new Error("FILE_LOAD_FAILED");

  return res.blob();
}
```

### 이미지 렌더링 예시
```tsx
function ProtectedImage({ imageApiUrl, token }: { imageApiUrl: string; token: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let url: string | null = null;
    fetchProtectedBlob(imageApiUrl, token)
      .then((blob) => {
        url = URL.createObjectURL(blob);
        setSrc(url);
      })
      .catch(() => setSrc(null));
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [imageApiUrl, token]);

  if (!src) return null;
  return <img src={src} alt="" />;
}
```

### 오디오 렌더링 예시
```tsx
function ProtectedAudio({ audioApiUrl, token }: { audioApiUrl: string; token: string }) {
  const [src, setSrc] = useState<string | null>(null);

  useEffect(() => {
    let url: string | null = null;
    fetchProtectedBlob(audioApiUrl, token)
      .then((blob) => {
        url = URL.createObjectURL(blob);
        setSrc(url);
      })
      .catch(() => setSrc(null));
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [audioApiUrl, token]);

  if (!src) return null;
  return <audio controls src={src} />;
}
```

## 6) 리스트 응답 렌더링 규칙
- 페이지형: `PaginatedResponse` -> `items` 렌더링, `total/skip/limit`으로 페이지 계산
- 배열형: `[]` empty state 처리
- 정렬
  - 대부분 최신순(desc)
  - 채팅 메시지는 생성순(asc)

## 7) 에러 detail 표시 방식
- 문자열 detail:
  - 그대로 toast/inline 메시지 노출
- 배열 detail(422):
  - `detail[].msg`를 필드별로 매핑
- 권장 사용자 안내
  - `401`: "로그인이 만료되었습니다. 다시 로그인해 주세요."
  - `403`: "권한 또는 선행 조건이 충족되지 않았습니다."
  - `404`: "요청한 데이터를 찾을 수 없습니다."

## 8) 핵심 사용자 플로우

### A. 회원가입/로그인/내 정보
1. `POST /auth/register` 또는 `POST /auth/login`
2. 토큰 저장
3. `GET /auth/me`로 `id`, `role` 로딩

### B. Target 생성
1. `POST /targets`
2. 성공 후 `GET /targets` 또는 `GET /targets/{id}`

### C. TargetMedia 업로드
1. 동의 상태 확인(`GET /targets/{target_id}/consents`)
2. 필요 동의 생성(`POST /consents`)
3. `POST /targets/{target_id}/media` (`multipart/form-data`)
4. 목록 조회 `GET /targets/{target_id}/media`
5. 파일 렌더링은 `file_api_url` 사용

### D. ConsentLog 생성/조회/철회
1. 생성: `POST /consents`
2. 내 목록: `GET /consents`
3. 타겟별 목록: `GET /targets/{target_id}/consents`
4. 철회: `PATCH /consents/{consent_id}/revoke`

### E. Verification 제출/관리자 승인
1. 사용자 제출: `POST /targets/{target_id}/verification-requests`
2. 사용자 확인: `GET /targets/{target_id}/verification-requests`
3. 관리자 목록/상세: `/admin/verification-requests*`
4. 관리자 상태 변경: approve/reject/need-more-info/revoke

### F. Persona 생성/조회
1. `POST /targets/{target_id}/persona`
2. 폴링: `GET /personas/{persona_id}/status`
3. 상세: `GET /personas/{persona_id}`

### G. PersonaVoiceProfile 생성/평가/검수
1. 사용자 생성: `POST /personas/{persona_id}/voice-profile`
2. 평가: `POST /personas/{persona_id}/voice-profile/evaluate`
3. 사용자 확인: `PATCH /personas/{persona_id}/voice-profile/user-confirm`
4. 관리자 검수: `/admin/voice-profiles/{id}/*`

### H. PersonaChat/PersonaMessage
1. 채팅 생성: `POST /personas/{persona_id}/chats`
2. 텍스트 전송: `POST /chats/{chat_id}/messages`
3. 음성 전송: `POST /chats/{chat_id}/audio`
4. 목록: `GET /chats/{chat_id}/messages`
5. 오디오 재생: `audio_api_url` -> blob 렌더링

### I. AIInterview
1. 세션 생성: `POST /interviews`
2. 질문 생성: `POST /interviews/{session_id}/questions`
3. 답변 생성: `POST /interviews/{session_id}/answers`
4. 상세 조회: `GET /interviews/{session_id}`

### J. PhotoMemory
1. 업로드: `POST /photo-memories`
2. 목록/상세: `GET /photo-memories`, `GET /photo-memories/{id}`
3. 이미지: `image_api_url` fetch + blob 렌더링
4. 삭제: `DELETE /photo-memories/{id}`

### K. StoryBook 생성/공유
1. 생성: `POST /storybooks`
2. 목록/상세/챕터: `GET /storybooks*`
3. 재생성: `POST /storybooks/{id}/regenerate`
4. 링크 공유: `POST /storybooks/{id}/share-links`
5. 공개 조회: `GET /share/{token}`

### L. MemoryGroup
1. 그룹 생성: `POST /groups`
2. 멤버 관리: `POST/GET /groups/{group_id}/members`
3. 그룹 공유: `POST /groups/{group_id}/storybooks/{storybook_id}`
4. 그룹 책 목록: `GET /groups/{group_id}/storybooks`

### M. DeletionRequest
1. 생성: `POST /deletion-requests`
2. 목록/상세: `GET /deletion-requests*`
3. 취소: `PATCH /deletion-requests/{id}/cancel`

### N. Report
1. 생성: `POST /reports`
2. 내 목록/상세: `GET /reports`, `GET /reports/{id}`
3. 관리자 처리: `/admin/reports*`

### O. Admin review/audit/usage/rate-limit
1. 검수: `/admin/verification-requests*`
2. 삭제요청 운영: `/admin/deletion-requests*`
3. 감사로그: `/admin/audit-logs`
4. 사용량: `/admin/usage-limits`, `/admin/users/{id}/usage-limit`, `/admin/personas/{id}/usage-limit`
5. 이벤트: `/admin/rate-limit-events`

## 9) Persona 생성 전 Gate Flow
1. Target 소유권 필요
2. Verification 승인 필요
3. `ai_persona_creation_consent` 필요
4. `ai_response_notice_consent` 필요
5. 음성 사용 시 `voice_upload_consent` + `voice_cloning_consent` + READY voice profile 정책 필요

프론트 안내 문구:
- `Target verification approval is required before creating persona.`
- "관계 입증이 승인된 뒤 페르소나를 만들 수 있어요."

## 10) VoiceCall WebSocket Protocol

### 연결
- URL: `ws://<host>/api/v1/ws/personas/{persona_id}/voice?token=<access_token>`
- 토큰/소유권/정책 검사 실패 시 `1008` close 가능

### Client -> Server
- `start`
```json
{ "type": "start", "chat_id": 123 }
```
- `audio_chunk`
```json
{ "type": "audio_chunk", "data": "<base64>", "mime_type": "audio/webm" }
```
- `end_utterance`
```json
{ "type": "end_utterance" }
```
- `stop`
```json
{ "type": "stop" }
```

### Server -> Client
- `session_started`
```json
{ "type": "session_started", "session_id": 1 }
```
- `final_transcript`
```json
{ "type": "final_transcript", "text": "..." }
```
- `persona_text`
```json
{ "type": "persona_text", "text": "..." }
```
- `persona_audio`
```json
{ "type": "persona_audio", "audio_url": "...", "audio_file_path": "..." }
```
- `session_ended`
```json
{ "type": "session_ended" }
```
- `error`
```json
{ "type": "error", "message": "..." }
```

### Audio chunk 형식
- base64 raw bytes
- chunk size / chunk count 제한 적용
- `mime_type`에 따라 서버 저장 확장자 결정

### Session lifecycle
1. `start`
2. `audio_chunk` N회
3. `end_utterance` -> transcript/reply/audio 수신
4. 2-3 반복
5. `stop` 종료

### 프론트 렌더링 가이드
- `start` 전 chunk 전송 금지
- `error` 수신 시 동일 세션에서 복구 가능한지 분기
- `persona_audio`는 보호 파일 정책과 경로 체계를 함께 확인

## 11) 화면별 사용 API 매핑
- Auth 화면: `/auth/register`, `/auth/login`, `/auth/me`, `/auth/refresh-token`
- Target 화면: `/targets*`
- Consent 화면: `/consents*`, `/targets/{id}/consents`
- Verification 화면: 사용자 `/targets/{id}/verification-requests*`, 관리자 `/admin/verification-requests*`
- Persona 화면: `/targets/{id}/persona`, `/personas/{id}*`
- Chat 화면: `/personas/{id}/chats`, `/chats/{id}/*`
- Interview 화면: `/interviews*`
- PhotoMemory 화면: `/photo-memories*`
- StoryBook 화면: `/storybooks*`, `/storybooks/{id}/share-links`, `/share/{token}`
- Group 화면: `/groups*`
- Deletion 화면: `/deletion-requests*`
- Report 화면: `/reports*`, 관리자 `/admin/reports*`
- Admin 운영: `/admin/audit-logs`, `/admin/usage-limits`, `/admin/rate-limit-events`

## 12) 확인 필요(TODO)
- `/admin/reports*` 일부 endpoint는 response_model/request_model이 구체적으로 지정되지 않아 타입 안정성이 낮음
- `POST /reports` 생성 status code가 `201`이 아닌 `200`
- `InterviewService`의 `PHOTO_MEMORY` 분기에서 `photo_memory_id` 필수 여부가 TODO로 남아 있음
- VoiceCall `persona_audio.audio_url`는 운영의 public uploads 정책과 정합성 재검토 필요
## Usage Limit Integration Note (2026-05-14)
- Admin usage APIs:
  - `GET /api/v1/admin/usage-limits`
  - `PATCH /api/v1/admin/users/{user_id}/usage-limit`
  - `PATCH /api/v1/admin/personas/{persona_id}/usage-limit`
  - `GET /api/v1/admin/rate-limit-events`
- For `GET /api/v1/admin/usage-limits?user_id={id}`, backend may create the current month row on first read.
- Frontend should treat `period_ym` as the display key (`YYYY-MM`).
- Frontend should not assume usage rows already exist for every user/persona.
- If API returns `500` with safe detail (`Usage limit data is temporarily unavailable.`), show a generic retry message and keep prior UI state.
