# 03. Frontend Integration

## 목차

- [기본 설정](#기본-설정)
- [인증 헤더](#인증-헤더)
- [Response 처리](#response-처리)
- [multipart 업로드](#multipart-업로드)
- [화면별 API 연결](#화면별-api-연결)
- [에러 처리](#에러-처리)
- [Realtime Voice](#realtime-voice)

## 기본 설정

| 항목 | 값 |
| --- | --- |
| REST base path | `/api/v1` |
| Health | `/health` |
| Swagger | `/docs` |
| Auth scheme | Bearer access token |
| Refresh | `POST /api/v1/auth/refresh-token` |

예시:

```ts
const API_BASE = "/api/v1";

async function apiFetch(path: string, init: RequestInit = {}) {
  const token = localStorage.getItem("access_token");
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!response.ok) throw await response.json().catch(() => ({ detail: response.statusText }));
  if (response.status === 204) return null;
  return response.json();
}
```

## 인증 헤더

로그인/회원가입 응답:

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

이후 인증 API에는 다음 헤더를 붙인다.

```http
Authorization: Bearer jwt-access-token
```

access token 만료 시 `POST /api/v1/auth/refresh-token`에 `refresh_token`을 보내 새 token pair를 저장한다. logout은 `POST /api/v1/auth/logout`에 `refresh_token`을 보낸다.

## Response 처리

자세한 schema는 [02-backend-api.md](02-backend-api.md)의 [Response Shape](02-backend-api.md#response-shape)를 기준으로 한다.

| Shape | 프론트 처리 |
| --- | --- |
| 단일 객체 | 상세 화면 또는 form 초기값으로 사용 |
| 배열 | list 렌더링, 빈 배열은 empty state |
| `PaginatedResponse` | `items` 렌더링, `total/skip/limit`으로 pagination |
| `MessageResponse` | `message` toast |
| `204` | 성공 toast 후 화면 이동/목록 갱신 |

`PaginatedResponse` 예시:

```json
{
  "total": 1,
  "skip": 0,
  "limit": 20,
  "items": []
}
```

## multipart 업로드

JSON 헤더를 수동으로 넣지 말고 `FormData`를 그대로 보낸다.

Target media:

```ts
const form = new FormData();
form.append("media_type", "image");
form.append("file", file);

await apiFetch(`/targets/${targetId}/media`, {
  method: "POST",
  body: form,
});
```

Verification:

```ts
const form = new FormData();
form.append("verification_type_param", "SELF_DECLARATION");
form.append("applicant_note", "본인 확인 요청");
form.append("file", file);
```

Photo memory:

```ts
const form = new FormData();
form.append("title", "Birthday");
form.append("description", "Family birthday photo");
form.append("file", file);
```

## 화면별 API 연결

| 화면 | API 순서 |
| --- | --- |
| Auth | `POST /auth/register` 또는 `/auth/login` -> token 저장 -> `GET /auth/me` |
| Target | `GET /targets` -> `POST /targets` -> `GET /targets/{id}` |
| Consent | `POST /consents` -> `GET /targets/{target_id}/consents` |
| Verification | `POST /targets/{id}/verification-requests` -> `GET /targets/{id}/verification-requests` |
| Media | `POST /targets/{id}/media` -> `GET /targets/{id}/media` |
| Persona | `POST /targets/{id}/persona` -> `GET /personas/{id}` -> `GET /personas/{id}/status` |
| Chat | `POST /personas/{id}/chats` -> `POST /chats/{id}/messages` -> `GET /chats/{id}/messages` |
| StoryBook | `POST /storybooks` -> `GET /storybooks/{id}` -> `GET /storybooks/{id}/chapters` |
| Sharing | `POST /storybooks/{id}/share-links` -> public `GET /share/{token}` |
| Admin | admin token으로 `/admin/*` API 호출 |

## 에러 처리

| Status | 실제 shape | 처리 |
| --- | --- | --- |
| 400 | `{ "detail": "..." }` | 사용자 입력 또는 파일 조건 안내 |
| 401 | `{ "detail": "Could not validate credentials" }`류 | refresh token 시도 후 실패 시 로그아웃 |
| 403 | `{ "detail": "Forbidden" }`류 | 권한 없음 화면 |
| 404 | `{ "detail": "..." }` | not found/권한 숨김 안내 |
| 422 | `{ "detail": [...] }` | 필드별 validation 메시지 |
| 429 | `{ "detail": "..." }` | 제한 안내, 잠시 후 재시도 |

프론트 공통 parser:

```ts
function errorMessage(error: unknown) {
  const detail = (error as any)?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join("\n");
  if (typeof detail === "string") return detail;
  return "요청 처리 중 오류가 발생했습니다.";
}
```

## Realtime Voice

```text
ws://localhost:8000/api/v1/ws/personas/{persona_id}/voice?token={access_token}
```

client message는 `start`, `audio_chunk`, `end_utterance`, `stop`을 사용한다. 서버 message는 `session_started`, `final_transcript`, `persona_text`, `persona_audio`, `session_ended`, `error`다. 상세는 [06-realtime-voice-chat.md](06-realtime-voice-chat.md)를 본다.
