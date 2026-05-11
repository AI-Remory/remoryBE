# Remory Frontend API Guide

이 문서는 Remory 프론트엔드에서 자주 사용하는 인증, 파일 업로드, Target Verification, 관리자 화면 연동을 빠르게 붙일 수 있도록 정리한 가이드다.

- API Base URL: `http://localhost:8000`
- v1 prefix: `/api/v1`
- 인증 방식: Bearer JWT
- 문서 대상: 프론트엔드 개발자

---

## 1. 기본 설정

### 1-1. API Base URL

개발 환경 기준 기본 Base URL은 다음과 같다.

```text
http://localhost:8000
```

실제 요청 경로는 항상 `/api/v1` prefix를 붙여 사용한다.

예:

```text
http://localhost:8000/api/v1/auth/me
http://localhost:8000/api/v1/targets
http://localhost:8000/api/v1/admin/verification-requests
```

### 1-2. 인증 API 헤더 형식

로그인이 필요한 모든 API는 다음 형식의 `Authorization` 헤더를 사용한다.

```http
Authorization: Bearer ${accessToken}
```

### 1-3. Bearer Token 사용법

로그인 또는 회원가입 성공 시 `access_token`과 `refresh_token`이 반환된다.

프론트엔드는 일반적으로 `access_token`을 API 호출에 사용한다.

예시:

```ts
const accessToken = "jwt-access-token";

fetch("http://localhost:8000/api/v1/auth/me", {
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
});
```

### 1-4. accessToken 저장 위치 주의사항

`accessToken`은 민감 정보다. 가능하면 아래 우선순위를 권장한다.

1. **메모리 상태**(예: React state, Zustand, Redux store)
2. **짧은 만료 정책 + 재로그인/refresh 전략**
3. 정말 필요한 경우에만 `sessionStorage`

주의:

- `localStorage`는 XSS에 취약하므로 가능하면 피하는 것이 좋다.
- 브라우저 탭 간 동기화가 꼭 필요하지 않다면 메모리 기반 저장이 더 안전하다.
- `refresh_token` 저장 방식은 프론트 정책과 보안 정책에 따라 별도로 설계해야 한다.

---

## 2. 인증 헤더 예시

### 2-1. fetch 예시

```ts
const accessToken = "jwt-access-token";

const response = await fetch("http://localhost:8000/api/v1/auth/me", {
  method: "GET",
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
});

if (!response.ok) {
  throw new Error(`Request failed: ${response.status}`);
}

const me = await response.json();
console.log(me);
```

### 2-2. axios 예시

```ts
import axios from "axios";

const accessToken = "jwt-access-token";

const api = axios.create({
  baseURL: "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

const { data } = await api.get("/auth/me");
console.log(data);
```

---

## 3. FormData 파일 업로드 예시

업로드 API는 `multipart/form-data`를 사용한다. 이때 **브라우저가 `Content-Type`을 자동 설정하게 두는 것**을 권장한다.

### 3-1. TargetMedia 업로드

실제 경로:

```text
POST /api/v1/targets/{target_id}/media
```

전송 필드:

- `media_type`: `image` 또는 `voice`
- `file`: 업로드 파일

예시:

```ts
const formData = new FormData();
formData.append("media_type", "image");
formData.append("file", fileInput.files?.[0] as File);

const response = await fetch(`http://localhost:8000/api/v1/targets/${targetId}/media`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
  body: formData,
});
```

### 3-2. PhotoMemory 업로드

실제 경로:

```text
POST /api/v1/photo-memories
```

전송 필드:

- `file`: 업로드 파일
- `title`: 사진 메모리 제목
- `description`: 설명
- `taken_at`: 촬영 시각(선택/요구 여부는 UI 설계에 맞춰 전송)
- `location`: 위치(선택)

예시:

```ts
const formData = new FormData();
formData.append("file", fileInput.files?.[0] as File);
formData.append("title", "Birthday");
formData.append("description", "Family birthday photo");

const response = await fetch("http://localhost:8000/api/v1/photo-memories", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
  body: formData,
});
```

### 3-3. TargetVerificationRequest 문서 업로드

실제 경로:

```text
POST /api/v1/targets/{target_id}/verification-requests
```

전송 필드:

- `verification_type_param`: `family_relation_certificate` | `id_card` | `self_declaration` | `other`
- `file`: 입증 문서 파일

예시:

```ts
const formData = new FormData();
formData.append("verification_type_param", "family_relation_certificate");
formData.append("file", fileInput.files?.[0] as File);

const response = await fetch(
  `http://localhost:8000/api/v1/targets/${targetId}/verification-requests`,
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
    body: formData,
  }
);
```

### 3-4. multipart/form-data 주의사항

- `fetch`/`axios`에서 `Content-Type: multipart/form-data`를 직접 고정하지 않는 것을 권장한다.
- 브라우저가 boundary를 포함한 올바른 헤더를 자동 생성해야 한다.
- `FormData`를 사용할 때 JSON body와 혼용하지 않는다.

---

## 4. Target Verification 프론트 흐름

Target Verification은 **Persona 생성 전에 승인 여부를 확인하는 흐름**으로 붙이는 것이 좋다.

### 4-1. 흐름 요약

1. Target 생성
2. Verification 문서 제출
3. 서버에서 `PENDING` 상태로 저장
4. 관리자가 승인 전까지 Persona 생성 버튼 비활성화
5. `APPROVED`가 되면 Persona 생성 가능
6. `REJECTED`면 `rejection_reason` 표시

### 4-2. Target 생성

실제 경로:

```text
POST /api/v1/targets
```

Target 생성 후 해당 `target_id`를 사용해 verification request를 제출한다.

### 4-3. Verification request 제출

실제 경로:

```text
POST /api/v1/targets/{target_id}/verification-requests
```

성공 시 `status`는 보통 `pending`으로 내려온다.

프론트에서는 제출 직후 다음처럼 상태를 표시할 수 있다.

- `PENDING`: 승인 대기 중
- `APPROVED`: Persona 생성 가능
- `REJECTED`: 거절 사유 표시

### 4-4. PENDING 상태 표시

검증 요청 상세 또는 목록 응답에서 `status`를 확인해 UI에 반영한다.

예:

- `PENDING` → "검토 중입니다"
- `APPROVED` → "승인 완료"
- `REJECTED` → "거절됨"

### 4-5. APPROVED 전까지 Persona 생성 버튼 비활성화

Persona 생성 API는 다음 경로다.

```text
POST /api/v1/targets/{target_id}/persona
```

프론트에서는 아래 조건일 때 버튼을 비활성화하는 것이 좋다.

- verification request가 없음
- verification request 상태가 `PENDING`
- verification request 상태가 `REJECTED`

### 4-6. APPROVED면 Persona 생성 가능

`status === APPROVED`일 때만 Persona 생성 버튼을 활성화한다.

### 4-7. REJECTED면 rejection_reason 표시

거절된 경우 응답의 `rejection_reason`을 화면에 보여줄 수 있다.

예:

- "서류 해상도가 낮아 판독이 어렵습니다."
- "가족관계 증빙이 부족합니다."

### 4-8. Persona 생성 전 verification 미승인 에러

verification 승인 없이 Persona 생성 API를 호출하면 403 에러가 발생할 수 있다.

프론트에서는 이 경우 다음과 같이 처리한다.

- Persona 생성 버튼 비활성화
- 이미 호출했다면 403 응답을 받아 안내 메시지 출력
- 메시지 예: `Target verification approval is required before creating persona.`

---

## 5. 관리자 화면 API 예시

관리자 verification 목록은 다음 경로를 사용한다.

```text
GET /api/v1/admin/verification-requests
```

관리자 승인/거절 API:

```text
PATCH /api/v1/admin/verification-requests/{request_id}/approve
PATCH /api/v1/admin/verification-requests/{request_id}/reject
```

### 5-1. PENDING 목록 조회

```text
GET /api/v1/admin/verification-requests?status=PENDING
```

### 5-2. APPROVED 목록 조회

```text
GET /api/v1/admin/verification-requests?status=APPROVED
```

### 5-3. REJECTED 목록 조회

```text
GET /api/v1/admin/verification-requests?status=REJECTED
```

### 5-4. status 필터 사용법

`status` 쿼리 파라미터는 다음 값만 사용한다.

- `PENDING`
- `APPROVED`
- `REJECTED`

값이 잘못되면 validation error가 발생한다.

### 5-5. 관리자 승인 예시

```ts
const response = await fetch(
  `http://localhost:8000/api/v1/admin/verification-requests/${requestId}/approve`,
  {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  }
);
```

### 5-6. 관리자 거절 예시

```ts
const response = await fetch(
  `http://localhost:8000/api/v1/admin/verification-requests/${requestId}/reject`,
  {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      rejection_reason: "Document is not clear and needs higher quality image",
    }),
  }
);
```

### 5-7. 관리자 목록 조회 예시

```ts
const response = await fetch(
  "http://localhost:8000/api/v1/admin/verification-requests?status=PENDING&page=1&size=20",
  {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  }
);
```

---

## 6. 주요 에러 처리

### 6-1. 401 Unauthorized

발생 가능 상황:

- Authorization 헤더 없음
- 토큰 만료
- 잘못된 토큰

프론트 처리:

- 로그인 페이지로 이동
- 토큰 갱신 전략이 있다면 refresh 처리

### 6-2. 403 Forbidden

발생 가능 상황:

- 권한 없는 사용자가 관리자 API 접근
- 다른 사용자의 리소스 접근
- verification 승인 없이 Persona 생성 시도

프론트 처리:

- "권한이 없습니다" 메시지 표시
- 관리자 화면은 ADMIN만 접근 가능하게 라우팅 가드 적용

### 6-3. 404 Not Found

발생 가능 상황:

- 존재하지 않는 target/persona/request id
- 다른 사용자의 자원 접근이 404로 숨겨지는 경우

프론트 처리:

- "리소스를 찾을 수 없습니다" 메시지 표시
- 이전 화면으로 복귀

### 6-4. 422 Validation Error

발생 가능 상황:

- enum 값 오류
- 필수 필드 누락
- 문자열 길이 위반
- reject 사유가 비어 있음
- multipart form field 누락

프론트 처리:

- 필드별 validation message 표시
- form input 아래 에러 문구 출력

### 6-5. Persona 생성 전 verification 미승인 에러

발생 가능 상황:

- approval 전 Persona 생성 버튼을 눌렀을 때

프론트 처리:

- Persona 생성 버튼 비활성화
- 상태가 `APPROVED`인지 반드시 확인
- 서버에서 403이 오면 안내 메시지 출력

---

## 7. 프론트에서 주의할 점

### 7-1. 민감한 verification 파일 경로 노출 금지

verification 관련 문서 파일 경로는 사용자에게 직접 노출하지 않는다.

- 파일 시스템 경로를 UI에 표시하지 않는다.
- 다운로드가 필요한 경우에도 서버가 별도 권한 체크를 거친 안전한 방식이어야 한다.

### 7-2. 공유 링크 화면은 읽기 전용

공유 링크로 접근하는 화면은 읽기 전용으로 처리한다.

- 수정 버튼 숨김
- 민감한 소유자 정보 미노출
- 내부 파일 경로 미표시

### 7-3. 관리자 API는 ADMIN만 접근 가능

관리자 화면은 role 기반 라우팅 가드를 적용한다.

- ADMIN 아닌 경우 관리자 메뉴 숨김
- API 호출 전 role 체크 가능하면 선차단
- 그래도 서버 403은 반드시 처리

### 7-4. multipart/form-data에서는 Content-Type을 직접 고정하지 않는 것을 권장

`FormData`를 사용할 때는 브라우저가 boundary를 포함해 `Content-Type`을 자동 생성하도록 두는 것이 가장 안전하다.

---

## 8. 실제 자주 쓰는 엔드포인트 요약

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Target
- `POST /api/v1/targets`
- `GET /api/v1/targets`
- `GET /api/v1/targets/{target_id}`
- `PUT /api/v1/targets/{target_id}`
- `DELETE /api/v1/targets/{target_id}`

### TargetMedia
- `POST /api/v1/targets/{target_id}/media`
- `GET /api/v1/targets/{target_id}/media`

### Target Verification
- `POST /api/v1/targets/{target_id}/verification-requests`
- `GET /api/v1/targets/{target_id}/verification-requests`
- `GET /api/v1/verification-requests/{request_id}`

### Admin Verification
- `GET /api/v1/admin/verification-requests`
- `PATCH /api/v1/admin/verification-requests/{request_id}/approve`
- `PATCH /api/v1/admin/verification-requests/{request_id}/reject`

### Persona
- `POST /api/v1/targets/{target_id}/persona`
- `GET /api/v1/personas/{persona_id}`
- `GET /api/v1/personas/{persona_id}/status`

---

## 9. 구현 메모

- 날짜/시간은 ISO 8601 문자열 형식이다.
- 목록 응답은 보통 `total`, `skip`, `limit`, `items` 형태를 따른다.
- 관리자 verification 목록은 `status`, `page`, `size`를 사용할 수 있다.
- Persona 생성은 verification 승인 여부를 먼저 확인해야 한다.

---

## 10. 추천 프론트 구현 순서

1. `accessToken` 저장/주입 구조 설계
2. `fetch` 또는 `axios` 공통 API 클라이언트 구성
3. Target 생성 폼 구현
4. verification 제출 폼 구현
5. verification 상태 표시 UI 구현
6. Persona 생성 버튼 상태 제어
7. 관리자 verification 리스트/승인/거절 화면 구현
8. 공통 에러 처리 컴포넌트 추가

---

이 문서는 현재 구현된 API 경로를 기준으로 작성되었다.
추가 엔드포인트가 생기면 같은 형식으로 확장하면 된다.


---

## 11. Granular Consent Flow

The backend now stores consent as detailed history rows and supports revocation.
Frontend screens should create consent before enabling AI persona, upload, voice cloning, or sharing actions.

### Consent Types

Use these request values:

| Purpose | `consent_type` |
| --- | --- |
| Target profile data | `target_profile_consent` |
| Photo upload | `photo_upload_consent` |
| Voice upload | `voice_upload_consent` |
| Voice cloning | `voice_cloning_consent` |
| AI persona creation | `ai_persona_creation_consent` |
| AI response notice | `ai_response_notice_consent` |
| StoryBook link share | `storybook_share_consent` |
| Group share | `group_share_consent` |
| Data retention | `data_retention_consent` |
| Third-party AI processing | `third_party_ai_processing_consent` |

### Create Consent

```ts
await api.post("/api/v1/consents", {
  target_id: targetId,
  consent_type: "ai_persona_creation_consent",
  consent_version: "2026-05-12",
  consent_text_snapshot: "사용자가 AI 페르소나 생성을 동의했습니다.",
  is_agreed: true,
});
```

Target-scoped consent must use a target owned by the current user.
For global consent such as StoryBook share, group share, data retention, or third-party AI processing, send `target_id: null`.

### Read Consent State

```ts
const all = await api.get("/api/v1/consents");
const targetConsents = await api.get(`/api/v1/targets/${targetId}/consents`);
```

Both list endpoints return newest records first. For UI state, group by `target_id + consent_type` and use the first row as the latest state.

### Revoke Consent

```ts
await api.patch(`/api/v1/consents/${consentId}/revoke`);
```

After revoke:

- `is_agreed` is `false`
- `revoked_at` is set
- Persona/voice/share policy checks no longer accept that consent

### Required Consent Before Actions

Before enabling Persona creation:

- `ai_persona_creation_consent`
- `ai_response_notice_consent`

Before media upload:

- Photo: `photo_upload_consent`
- Voice: `voice_upload_consent`

Before voice profile creation:

- `voice_upload_consent`
- `voice_cloning_consent`

Before sharing:

- Share link: `storybook_share_consent`
- Group share: `group_share_consent`

Legacy consent values are still accepted for backward compatibility, but new frontend code should use the granular values above.
