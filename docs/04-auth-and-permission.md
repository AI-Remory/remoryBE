# 04. Auth And Permission

## 목차

- [JWT 인증](#jwt-인증)
- [Role 구조](#role-구조)
- [USER 권한](#user-권한)
- [ADMIN 권한](#admin-권한)
- [Owner-only 접근 규칙](#owner-only-접근-규칙)
- [Admin-only API 규칙](#admin-only-api-규칙)
- [401/403 처리 기준](#401403-처리-기준)
- [보안 메모](#보안-메모)

## JWT 인증

Remory는 access token과 refresh token을 사용한다.

- Access token: 일반 API 인증에 사용
- Refresh token: access token 재발급과 logout blacklist에 사용
- Algorithm: `HS256`
- Secret: `.env`의 `SECRET_KEY`

Access token payload에는 최소한 다음 값이 들어간다.

```json
{
  "sub": "1",
  "token_type": "access",
  "exp": 1780000000
}
```

인증 헤더:

```http
Authorization: Bearer {access_token}
```

WebSocket 음성 대화는 헤더 대신 query param을 사용한다.

```text
WS /api/v1/ws/personas/{persona_id}/voice?token={access_token}
```

## Role 구조

`User.role`은 일반 사용자와 관리자 권한을 구분한다.

| Role | 의미 |
| --- | --- |
| `USER` | 일반 서비스 사용자 |
| `ADMIN` | 검증/신고/음성 profile/usage/audit 운영자 |

## USER 권한

USER는 자신이 소유한 리소스만 접근한다.

- 내 target 생성/조회/수정/삭제
- 내 target media 업로드/조회/삭제
- 내 consent 생성/조회/철회
- 내 target verification 제출/조회
- 내 target의 persona 생성/조회
- 내 persona chat/message 생성/조회
- 내 interview/photo memory/storybook 생성/조회
- 내 storybook share link 생성/비활성화
- 내가 속한 group 조회
- 내 deletion request 생성/조회/취소
- 내 report 생성/조회

## ADMIN 권한

ADMIN은 운영 목적의 admin API에 접근할 수 있다.

- TargetVerificationRequest 목록/상세/파일 조회
- verification approve/reject/need-more-info/revoke
- deletion request 승인/처리/거절
- audit log 조회
- usage limit 조회/수정
- rate limit event 조회
- report 조회/처리
- voice profile 조회/승인/거절/철회

ADMIN이라고 해서 일반 사용자 API의 owner-only 정책을 우회하는 구조는 아니다. 운영 API는 `/api/v1/admin/...` 아래에 별도로 둔다.

## Owner-only 접근 규칙

다음 리소스는 항상 owner check를 거친다.

- `Target.user_id`
- `TargetMedia.target.user_id`
- `Persona.target.user_id`
- `PersonaChat.user_id`
- `PersonaMessage.chat.user_id`
- `AIInterviewSession.user_id`
- `PhotoMemory.user_id`
- `StoryBook.user_id`
- `ShareLink.storybook.user_id`
- `MemoryGroup` owner/member 관계
- `DeletionRequest.user_id`
- `Report.reporter_user_id`

정책:

- 다른 사용자의 리소스 접근은 `403` 또는 정보 은닉을 위한 `404`로 처리한다.
- 조회 목록 API는 내 리소스만 반환한다.
- update/delete/process 계열 API는 대상 리소스가 내 것인지 먼저 확인한다.

## Admin-only API 규칙

Admin API는 `get_admin_user` dependency로 `User.role == ADMIN`을 확인한다.

대표 경로:

- `/api/v1/admin/verification-requests`
- `/api/v1/admin/deletion-requests`
- `/api/v1/admin/audit-logs`
- `/api/v1/admin/usage-limits`
- `/api/v1/admin/rate-limit-events`
- `/api/v1/admin/reports`
- `/api/v1/admin/voice-profiles`

일반 사용자가 호출하면 `403`을 반환한다.

## 401/403 처리 기준

| Status | 기준 | 예시 |
| --- | --- | --- |
| `401` | 인증 자체가 실패 | token 없음, 만료, 잘못된 token, token type 불일치 |
| `403` | 인증은 됐지만 권한 또는 정책 조건 실패 | owner 아님, ADMIN 아님, consent 없음, verification 미승인 |

프론트 처리:

- `401`: refresh 또는 로그인 이동
- `403`: 권한 없음/조건 미충족 안내
- `404`: 존재하지 않거나 접근할 수 없는 리소스로 안내

## 보안 메모

- Access token은 가능한 memory에 둔다.
- `.env`와 token, API key는 커밋하지 않는다.
- verification 파일 경로는 일반 사용자 JSON 응답에 노출하지 않는다.
- AuditLog metadata는 token/password/secret/api_key 등 민감 키를 sanitize한다.
- voice cloning은 verification, consent, voice media, READY profile, review approval 조건을 모두 만족해야 한다.
