# 03. Frontend Integration

## 목차

- [기본 설정](#기본-설정)
- [Authorization 헤더](#authorization-헤더)
- [multipart/form-data 업로드](#multipartform-data-업로드)
- [화면별 API 연결 순서](#화면별-api-연결-순서)
- [에러 처리](#에러-처리)
- [프론트 구현 메모](#프론트-구현-메모)

## 기본 설정

개발 Base URL:

```text
http://localhost:8000
```

v1 API prefix:

```text
/api/v1
```

프론트 `.env` 예시:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/api/v1
```

## Authorization 헤더

로그인 또는 회원가입 성공 시 `access_token`, `refresh_token`, `user`가 반환된다.

인증 API 호출:

```ts
const response = await fetch("http://localhost:8000/api/v1/auth/me", {
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
});
```

axios client 예시:

```ts
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

토큰 저장 권장:

- 1순위: memory state, Zustand/Redux 등 앱 상태
- 2순위: sessionStorage
- localStorage는 XSS 위험이 있어 최소화한다.

## multipart/form-data 업로드

브라우저가 boundary를 자동 생성해야 하므로 `Content-Type: multipart/form-data`를 직접 고정하지 않는다.

TargetMedia:

```ts
const formData = new FormData();
formData.append("media_type", "image");
formData.append("file", file);

await fetch(`${baseUrl}/targets/${targetId}/media`, {
  method: "POST",
  headers: { Authorization: `Bearer ${accessToken}` },
  body: formData,
});
```

PhotoMemory:

```ts
const formData = new FormData();
formData.append("file", file);
formData.append("title", "Birthday");
formData.append("description", "Family birthday photo");

await api.post("/photo-memories", formData);
```

Verification:

```ts
const formData = new FormData();
formData.append("verification_type_param", "FAMILY_RELATION_CERTIFICATE");
formData.append("file", file);
formData.append("applicant_note", "optional note");

await api.post(`/targets/${targetId}/verification-requests`, formData);
```

Chat audio:

```ts
const formData = new FormData();
formData.append("file", file);
formData.append("generate_audio", "true");

await api.post(`/chats/${chatId}/audio`, formData);
```

## 화면별 API 연결 순서

### 로그인/회원가입

1. `POST /auth/register` 또는 `POST /auth/login`
2. token과 user 저장
3. 앱 초기화 시 `GET /auth/me`

### Target 생성

1. `POST /targets`
2. 필요한 consent 생성: `POST /consents`
3. 검증 문서 제출: `POST /targets/{target_id}/verification-requests`
4. verification status가 `APPROVED`일 때 persona 생성 버튼 활성화

### Media 업로드

1. photo upload 전 `photo_upload_consent` 확인/생성
2. voice upload 전 `voice_upload_consent` 확인/생성
3. `POST /targets/{target_id}/media`
4. `GET /targets/{target_id}/media`로 목록 갱신

### Persona 생성

1. target 소유권은 서버가 검증한다.
2. 프론트에서는 `APPROVED` verification과 필수 consent가 있는지 먼저 표시한다.
3. `POST /targets/{target_id}/persona`
4. `GET /personas/{persona_id}` 또는 `/status`로 결과 확인

### Voice profile

1. target voice media 존재 확인
2. `voice_upload_consent`, `voice_cloning_consent` 확인
3. `POST /personas/{persona_id}/voice-profile`
4. `POST /personas/{persona_id}/voice-profile/evaluate`
5. status `READY`면 사용자 확인: `PATCH /personas/{persona_id}/voice-profile/user-confirm`

### Persona chat

1. `POST /personas/{persona_id}/chats`
2. 텍스트: `POST /chats/{chat_id}/messages`
3. 음성 파일: `POST /chats/{chat_id}/audio`
4. 메시지 목록: `GET /chats/{chat_id}/messages`

### Realtime voice chat

1. WebSocket 연결: `ws://localhost:8000/api/v1/ws/personas/{persona_id}/voice?token={accessToken}`
2. `start` 전송
3. `audio_chunk` 여러 개 전송
4. `end_utterance` 전송
5. `final_transcript`, `persona_text`, `persona_audio` 수신
6. `stop` 전송

상세 protocol은 [06-realtime-voice-chat.md](06-realtime-voice-chat.md)를 본다.

### StoryBook

1. Interview 또는 PhotoMemory source 준비
2. `POST /storybooks`
3. `GET /storybooks/{storybook_id}`
4. 필요 시 `POST /storybooks/{storybook_id}/regenerate`
5. 공유하려면 `storybook_share_consent` 후 share link 생성

### Admin 화면

Admin role 사용자만 admin 메뉴를 노출한다.

- Verification list/review: `/admin/verification-requests`
- Audit logs: `/admin/audit-logs`
- Usage limits: `/admin/usage-limits`
- Reports: `/admin/reports`
- Voice profile review: `/admin/voice-profiles/{voice_profile_id}`

## 에러 처리

### 401 Unauthorized

원인:

- Authorization 헤더 없음
- access token 만료
- 잘못된 token

처리:

- refresh flow가 있으면 재발급 시도
- 실패 시 로그인 화면으로 이동

### 403 Forbidden

원인:

- 다른 사용자의 리소스 접근
- admin-only API 접근
- verification/consent/voice profile 조건 미충족

처리:

- 권한 없음 메시지 표시
- persona/voice 생성 버튼은 상태 조건에 맞춰 비활성화

### 404 Not Found

원인:

- 없는 리소스
- owner-only 정책상 숨겨진 리소스

처리:

- 목록으로 복귀
- "리소스를 찾을 수 없습니다" 메시지 표시

### 422 Validation Error

원인:

- enum 값 오류
- 필수 필드 누락
- form field 이름 오류
- 파일 MIME/type 오류

처리:

- field 단위 메시지 표시
- multipart field 이름을 API 문서와 비교

### 429 Too Many Requests

원인:

- voice generation, STT, voice call seconds, active WebSocket 연결, utterance 제한 초과

처리:

- 재시도 시간 안내
- 관리자 화면에서는 usage limit 조정 가능

## 프론트 구현 메모

- verification 파일 경로는 UI에 직접 표시하지 않는다.
- share link 공개 화면은 읽기 전용으로 만든다.
- Admin 화면은 role 기반 route guard를 적용하되, 서버 403도 반드시 처리한다.
- Consent list는 최신순이다. `target_id + consent_type` 기준 최신 row를 현재 상태로 사용한다.
- 날짜/시간은 ISO 8601 문자열 기준으로 처리한다.
