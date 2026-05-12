# 04. Auth And Permission

## 목차

- [JWT 인증](#jwt-인증)
- [Token API](#token-api)
- [Role 구조](#role-구조)
- [Owner-only 규칙](#owner-only-규칙)
- [Admin-only 규칙](#admin-only-규칙)
- [401/403 기준](#401403-기준)

## JWT 인증

인증 dependency는 `app/deps.py`의 `get_current_user`, `get_admin_user`를 기준으로 한다. 일반 API는 `Authorization: Bearer <access_token>`을 요구하고, WebSocket은 query string의 `token`으로 access token을 전달한다.

```http
Authorization: Bearer <access_token>
```

access token과 refresh token 만료 기간은 `Settings`의 `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`를 따른다.

## Token API

| API | 설명 |
| --- | --- |
| `POST /api/v1/auth/register` | 사용자 생성 후 access/refresh token pair 반환 |
| `POST /api/v1/auth/sign-up` | register alias |
| `POST /api/v1/auth/login` | email/password 인증 후 token pair 반환 |
| `GET /api/v1/auth/me` | 현재 access token 사용자 조회 |
| `POST /api/v1/auth/refresh-token` | refresh token rotation |
| `POST /api/v1/auth/logout` | refresh token revoke |

`AuthResponse`:

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

## Role 구조

`app/models/user.py` 기준:

| Role | 값 | 설명 |
| --- | --- | --- |
| USER | `user` | 일반 사용자 |
| ADMIN | `admin` | admin endpoint 접근 가능 |

## Owner-only 규칙

일반 사용자는 자신이 소유한 리소스만 접근한다. 서비스 레이어에서 `current_user.id`와 리소스 owner를 비교한다.

| 리소스 | 기준 owner |
| --- | --- |
| Target | `Target.user_id` |
| Target media | media의 target owner |
| Consent | `ConsentLog.user_id` 또는 target owner |
| Verification request | `TargetVerificationRequest.user_id` 또는 target owner |
| Persona | persona의 target owner |
| Chat/Message | chat의 `user_id`와 persona owner |
| PhotoMemory | `PhotoMemory.user_id` |
| StoryBook | `StoryBook.user_id` |
| ShareLink | storybook owner |
| Group | owner/member 권한 |
| DeletionRequest | `DeletionRequest.user_id` |
| Report | reporter user 기준 |

## Admin-only 규칙

`/api/v1/admin/*`는 `get_admin_user`를 사용한다. admin role이 아니면 접근할 수 없다.

Admin API 범위:

- verification request 목록/상세/파일/승인/거절/추가정보/철회
- deletion request 목록/상세/승인처리/거절
- audit log 조회
- usage limit, persona usage limit 수정
- rate limit event 조회
- report 조회/검토/해결/거절/action taken
- voice profile 조회/승인/거절/철회

## 401/403 기준

| Status | 상황 | 프론트 처리 |
| --- | --- | --- |
| 401 | token 누락, 만료, 검증 실패 | refresh token으로 재발급 후 재시도 |
| 403 | 인증은 되었지만 owner/admin 조건 실패 | 권한 없음 안내 |

WebSocket은 token이 없거나 persona 접근 권한이 없으면 `WS_1008_POLICY_VIOLATION`으로 close한다.
